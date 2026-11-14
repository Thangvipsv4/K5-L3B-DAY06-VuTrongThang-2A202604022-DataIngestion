
"""Implement fixed-size and structure-aware chunking."""
import hashlib

from .models import Chunk, DocumentPage


def _make_chunk(
    page: DocumentPage,
    text: str,
    index: int,
    start: int,
    end: int,
    strategy: str,
) -> Chunk:
    """Create a chunk while preserving source traceability."""
    chunk_hash = hashlib.sha256(
        f"{page.document_id}:{page.page}:{strategy}:{index}:{text}".encode("utf-8")
    ).hexdigest()[:16]

    metadata = dict(page.metadata)
    metadata.update({
        "chunk_index": index,
        "start_char": start,
        "end_char": end,
        "chunking_strategy": strategy,
    })

    return Chunk(
        chunk_id=chunk_hash,
        document_id=page.document_id,
        source=page.source,
        page=page.page,
        text=text,
        metadata=metadata,
    )


def fixed_size(
    page: DocumentPage,
    size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    """Split text into overlapping character windows."""
    if size <= 0:
        raise ValueError("size must be greater than 0")

    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and smaller than size")

    text = page.text
    if not text.strip():
        return []

    chunks = []
    start = 0
    index = 0
    step = size - overlap

    while start < len(text):
        end = min(start + size, len(text))
        chunk_text = text[start:end]

        if chunk_text.strip():
            chunks.append(
                _make_chunk(
                    page=page,
                    text=chunk_text,
                    index=index,
                    start=start,
                    end=end,
                    strategy="fixed_size",
                )
            )
            index += 1

        if end == len(text):
            break

        start += step

    return chunks


def by_paragraph(
    page: DocumentPage,
    max_size: int = 1000,
) -> list[Chunk]:
    """Group paragraphs into chunks and split oversized paragraphs."""
    if max_size <= 0:
        raise ValueError("max_size must be greater than 0")

    text = page.text
    if not text.strip():
        return []

    # Find paragraph boundaries while preserving original character offsets.
    import re

    paragraphs = []
    for match in re.finditer(r"\S.*?(?=\n[ \t]*\n|\Z)", text, re.DOTALL):
        start = match.start()
        end = match.end()

        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1

        if start < end:
            paragraphs.append((start, end))

    chunks = []
    current_start = None
    current_end = None
    index = 0

    def emit(start: int, end: int) -> None:
        nonlocal index
        chunk_text = text[start:end]

        if chunk_text.strip():
            chunks.append(
                _make_chunk(
                    page=page,
                    text=chunk_text,
                    index=index,
                    start=start,
                    end=end,
                    strategy="by_paragraph",
                )
            )
            index += 1

    for para_start, para_end in paragraphs:
        para_length = para_end - para_start

        # Split a paragraph that exceeds the maximum size.
        if para_length > max_size:
            if current_start is not None:
                emit(current_start, current_end)
                current_start = None
                current_end = None

            position = para_start
            while position < para_end:
                end = min(position + max_size, para_end)
                emit(position, end)
                position = end

            continue

        if current_start is None:
            current_start = para_start
            current_end = para_end
            continue

        combined_length = para_end - current_start

        if combined_length <= max_size:
            current_end = para_end
        else:
            emit(current_start, current_end)
            current_start = para_start
            current_end = para_end

    if current_start is not None:
        emit(current_start, current_end)

    return chunks
