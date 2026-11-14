
import json
from pathlib import Path
from src.ingestion import normalize_text

BASE = Path(__file__).resolve().parent
QUESTIONS = BASE / "benchmark" / "questions.json"
CORPUS = BASE / "data" / "raw" / "ml_lessons"

data = json.loads(QUESTIONS.read_text(encoding="utf-8"))

changes = []

for question in data["questions"]:
    for evidence in question["gold_evidence"]:
        path = CORPUS / evidence["source_path"]
        raw = path.read_text(encoding="utf-8-sig")
        normalized = normalize_text(raw)

        old_start = evidence["start_char"]
        old_end = evidence["end_char"]

        needle = normalize_text(raw[old_start:old_end])

        positions = []
        pos = normalized.find(needle)

        while pos != -1:
            positions.append(pos)
            pos = normalized.find(needle, pos + 1)

        if len(positions) != 1:
            raise ValueError(
                f"{question['question_id']}: "
                f"expected 1 match, got {len(positions)}"
            )

        new_start = positions[0]
        new_end = new_start + len(needle)

        if normalized[new_start:new_end] != needle:
            raise ValueError(
                f"{question['question_id']}: verification failed"
            )

        if (old_start, old_end) != (new_start, new_end):
            changes.append({
                "question_id": question["question_id"],
                "old": [old_start, old_end],
                "new": [new_start, new_end]
            })

            evidence["start_char"] = new_start
            evidence["end_char"] = new_end

if changes:
    QUESTIONS.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

print(f"Updated {len(changes)} evidence ranges:")

for change in changes:
    print(
        f"{change['question_id']}: "
        f"{change['old']} -> {change['new']}"
    )

print("Done.")
