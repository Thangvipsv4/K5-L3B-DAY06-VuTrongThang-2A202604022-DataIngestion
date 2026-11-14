
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

        start = evidence["start_char"]
        end = evidence["end_char"]

        # Normalize the gold excerpt independently.
        needle = normalize_text(raw[start:end])

        positions = []
        pos = normalized.find(needle)

        while pos != -1:
            positions.append(pos)
            pos = normalized.find(needle, pos + 1)

        print(f"\n{question['question_id']}")

        if not positions:
            print("NOT FOUND: normalized gold excerpt")
            continue

        closest = min(positions, key=lambda p: abs(p - start))
        delta = closest - start

        print("Gold start:", start)
        print("Actual normalized start:", closest)
        print("Offset delta:", delta)
        print("Occurrences:", len(positions))
        print("Status:", "ALIGNED" if delta == 0 else "OFFSET MISMATCH")
