
import json
from pathlib import Path
from src.ingestion import normalize_text

BASE = Path(__file__).resolve().parent
CORPUS = BASE / "data" / "raw" / "ml_lessons"

OLD_FILE = BASE / "benchmark" / "questions_before_offset_fix.json"
NEW_FILE = BASE / "benchmark" / "questions.json"

old_data = json.loads(OLD_FILE.read_text(encoding="utf-8"))
new_data = json.loads(NEW_FILE.read_text(encoding="utf-8"))

old_questions = {
    q["question_id"]: q for q in old_data["questions"]
}

all_valid = True

for new_q in new_data["questions"]:
    old_q = old_questions[new_q["question_id"]]

    for old_ev, new_ev in zip(
        old_q["gold_evidence"],
        new_q["gold_evidence"]
    ):
        path = CORPUS / old_ev["source_path"]
        raw = path.read_text(encoding="utf-8-sig")
        normalized = normalize_text(raw)

        # Expected excerpt from original raw offsets
        expected = normalize_text(
            raw[old_ev["start_char"]:old_ev["end_char"]]
        )

        start = new_ev["start_char"]
        end = new_ev["end_char"]

        actual = normalized[start:end]
        valid = actual == expected

        print(
            f"{new_q['question_id']}: "
            f"{'PASS' if valid else 'FAIL'} "
            f"| range={start}-{end}"
        )

        if not valid:
            all_valid = False
            print("Expected:", repr(expected[:100]))
            print("Actual:  ", repr(actual[:100]))

print("\nFINAL:", "ALL PASS" if all_valid else "CHECK REQUIRED")
