
import csv
from pathlib import Path

path = Path("data/processed/evidence_catalog.csv")

with path.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

print("Total evidence:", len(rows))
print("Empty text:", sum(not r["text"].strip() for r in rows))
print("Missing document IDs:", sum(not r["document_id"] for r in rows))
print("Missing topics:", sum(not r["topic"] for r in rows))

print("\nSample evidence:")
for row in rows[:5]:
    print("\nTitle:", row["title"])
    print("Topic:", row["topic"])
    print("Paragraph:", row["paragraph_index"])
    print("Offsets:", row["start_char"], "-", row["end_char"])
    print("Text:", row["text"][:250].replace("\n", " "))
