
import csv
import re
from pathlib import Path

MANIFEST = Path("data/processed/manifest.csv")
OUTPUT = Path("data/processed/evidence_catalog.csv")
RAW_DIR = Path("data/raw/ml_lessons")

rows = []
missing = []

with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for doc in reader:
        # source_path trong manifest là đường dẫn tương đối
        source_path = Path(doc["source_path"])

        if not source_path.is_absolute():
            source_path = RAW_DIR / source_path

        if not source_path.exists():
            missing.append(str(source_path))
            continue

        text = source_path.read_text(encoding="utf-8-sig")
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        for index, match in enumerate(
            re.finditer(r"\S.*?(?=\n[ \t]*\n|\Z)", text, re.S),
            start=1,
        ):
            paragraph = match.group(0).strip()

            if len(paragraph) < 50:
                continue

            rows.append({
                "document_id": doc["document_id"],
                "title": doc["title"],
                "topic": doc["topic"],
                "lesson": doc["lesson"],
                "source_path": doc["source_path"],
                "paragraph_index": index,
                "start_char": match.start(),
                "end_char": match.end(),
                "text": paragraph,
            })

if not rows:
    raise RuntimeError(
        "No evidence paragraphs found. "
        "Check source_path in manifest.csv."
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("Documents processed:", len(set(r["document_id"] for r in rows)))
print("Evidence paragraphs:", len(rows))
print("Missing files:", len(missing))
print("Output:", OUTPUT)

if missing:
    print("\nMissing paths:")
    for path in missing:
        print("-", path)
