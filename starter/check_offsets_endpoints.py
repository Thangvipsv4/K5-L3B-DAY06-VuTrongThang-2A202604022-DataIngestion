import json
from pathlib import Path
from src.ingestion import normalize_text

BASE = Path(__file__).resolve().parent
QUESTIONS = BASE / "benchmark" / "questions.json"
CORPUS = BASE / "data" / "raw" / "ml_lessons"

data = json.loads(QUESTIONS.read_text(encoding="utf-8"))

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

        print(f"\n{question['question_id']}")
        print(f"Old range: {old_start}-{old_end}")
        print(f"Occurrences: {len(positions)}")

        if len(positions) == 1:
            new_start = positions[0]
            new_end = new_start + len(needle)

            print(f"New range: {new_start}-{new_end}")
            print(f"Start delta: {new_start - old_start}")
            print(f"End delta: {new_end - old_end}")
            print(
                "Verified:",
                normalized[new_start:new_end] == needle
            )
            print("Excerpt:", needle[:160].replace("\n", " "))
        else:
            print("NEEDS MANUAL REVIEW")