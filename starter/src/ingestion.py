
"""Read and normalize source data. Supports Markdown and PDF."""
import unicodedata
from pathlib import Path
from typing import Any

from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace while preserving Markdown structure."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")

    lines = [line.rstrip() for line in text.split("\n")]

    # Keep at most two consecutive blank lines.
    normalized_lines = []
    blank_count = 0

    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:
                normalized_lines.append("")
        else:
            blank_count = 0
            normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


def load_markdown(
    path: Path,
    document_id: str,
    source: str,
    metadata: dict[str, Any] | None = None,
) -> list[DocumentPage]:
    """Load one Markdown file as one logical document page."""
    path = Path(path)
    raw_text = path.read_text(encoding="utf-8-sig")
    text = normalize_text(raw_text)

    page_metadata = dict(metadata or {})
    page_metadata.update({
        "source_path": path.as_posix(),
        "location_type": "markdown_file",
        "page_type": "logical_document",
        "is_empty": not bool(text),
    })

    return [
        DocumentPage(
            document_id=document_id,
            source=source,
            page=1,
            text=text,
            metadata=page_metadata,
        )
    ]


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Extract physical PDF pages. OCR is handled separately."""
    raise NotImplementedError("TODO: load_pdf")
