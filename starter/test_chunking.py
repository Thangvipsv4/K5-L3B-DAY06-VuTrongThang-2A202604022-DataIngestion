import csv
from pathlib import Path

from src.ingestion import load_markdown
from src.chunking import fixed_size, by_paragraph

data_dir = Path("data/raw/ml_lessons")

fixed_total = 0
paragraph_total = 0
empty_docs = []
errors = []
fixed_max = 0
paragraph_max = 0

with open("data/processed/manifest.csv", encoding="utf-8-sig") as f:
    documents = list(csv.DictReader(f))

for row in documents:
    path = data_dir / row["source_path"]

    try:
        pages = load_markdown(
            path,
            row["document_id"],
            row["source"],
            metadata=row,
        )

        for page in pages:
            if not page.text.strip():
                empty_docs.append(row["document_id"])
                continue

            fixed = fixed_size(page, size=500, overlap=50)
            paragraph = by_paragraph(page, max_size=1000)

            fixed_total += len(fixed)
            paragraph_total += len(paragraph)

            fixed_max = max(
                fixed_max,
                max((len(c.text) for c in fixed), default=0)
            )
            paragraph_max = max(
                paragraph_max,
                max((len(c.text) for c in paragraph), default=0)
            )

            for chunk in fixed + paragraph:
                if not chunk.chunk_id or not chunk.document_id:
                    errors.append(f"Missing ID: {path}")

                if not chunk.metadata.get("source_path"):
                    errors.append(f"Missing source path: {path}")

                if not chunk.metadata.get("start_char") >= 0:
                    errors.append(f"Invalid start_char: {path}")

                if chunk.metadata["end_char"] <= chunk.metadata["start_char"]:
                    errors.append(f"Invalid offsets: {path}")

    except Exception as exc:
        errors.append(f"{path}: {exc}")

print("\n=== CORPUS CHUNKING REPORT ===")
print("Documents:", len(documents))
print("Fixed-size chunks:", fixed_total)
print("Paragraph chunks:", paragraph_total)
print("Maximum fixed chunk:", fixed_max)
print("Maximum paragraph chunk:", paragraph_max)
print("Empty documents:", len(empty_docs))
print("Errors:", len(errors))

if errors:
    print("\nError details:")
    for error in errors:
        print(error)

if empty_docs:
    print("\nEmpty document IDs:")
    print(empty_docs)
