
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
        if not path.exists():
            print("MISSING:", path)
            continue

        raw = path.read_text(encoding="utf-8-sig")
        normalized = normalize_text(raw)

        start = evidence["start_char"]
        end = evidence["end_char"]

        print(f"\n{question['question_id']}: {path.name}")
        print("Gold offsets:", start, end)
        print("Raw length:", len(raw))
        print("Normalized length:", len(normalized))
        print("Raw excerpt:")
        print(repr(raw[start:end]))
        print("Normalized excerpt:")
        print(repr(normalized[start:end]))
