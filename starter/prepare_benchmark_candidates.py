
import csv
import re
from collections import defaultdict
from pathlib import Path

INPUT = Path("data/processed/evidence_catalog.csv")
OUTPUT = Path("data/processed/evidence_candidates.csv")

candidates = defaultdict(list)

with INPUT.open("r", encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        text = row["text"].strip()

        # Bỏ nội dung chỉ có heading, link, ảnh hoặc video
        if len(text) < 120:
            continue

        if any(x in text.lower() for x in [
            "youtube.com",
            "youtu.be",
            "ff-quizzes",
            "click the image",
        ]):
            continue

        if text.startswith("![") or text.startswith("```"):
            continue

        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        clean = re.sub(r"[#>*_`]", "", clean)
        words = re.findall(r"\b[A-Za-z]{2,}\b", clean)

        if len(words) < 25:
            continue

        row["text"] = text
        candidates[row["document_id"]].append(row)

# Lấy tối đa 8 đoạn đầu tiên mỗi tài liệu
selected = []

for document_id, paragraphs in candidates.items():
    selected.extend(paragraphs[:8])

if not selected:
    raise RuntimeError("No useful evidence candidates found.")

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=selected[0].keys())
    writer.writeheader()
    writer.writerows(selected)

print("Documents with candidates:", len(candidates))
print("Candidate paragraphs:", len(selected))
print("Output:", OUTPUT)
