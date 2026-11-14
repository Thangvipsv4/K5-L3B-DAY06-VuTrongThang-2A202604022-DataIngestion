
import csv
import json
import time
from pathlib import Path

from src.embeddings import MyEmbedder
from src.store import PgVectorStore

DATABASE_URL = "postgresql://day6:day6_local_only@127.0.0.1:55433/day6_lab"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "benchmark" / "questions.json"
OUTPUT_JSON = BASE_DIR / "benchmark" / "results.json"
OUTPUT_CSV = BASE_DIR / "benchmark" / "results.csv"


def overlaps(start_a, end_a, start_b, end_b):
    return start_a < end_b and end_a > start_b


def hit_at_1(results, gold_evidence):
    """Document-level Hit@1."""
    if not results:
        return 0

    gold_ids = {item["document_id"] for item in gold_evidence}
    return int(results[0].get("document_id") in gold_ids)


def full_evidence_hit_at_3(results, gold_evidence):
    """Return 1 if a top-3 chunk contains an entire gold evidence span."""
    for result in results[:3]:
        metadata = result.get("metadata") or {}
        doc_id = result.get("document_id")

        chunk_start = metadata.get("start_char")
        chunk_end = metadata.get("end_char")

        if chunk_start is None or chunk_end is None:
            continue

        for evidence in gold_evidence:
            if doc_id != evidence["document_id"]:
                continue

            evidence_start = evidence["normalized_start_char"]
            evidence_end = evidence["normalized_end_char"]

            if (
                int(chunk_start) <= int(evidence_start)
                and int(chunk_end) >= int(evidence_end)
            ):
                return 1

    return 0


def overlap_evidence_hit_at_3(results, gold_evidence):
    """Return 1 if a top-3 chunk overlaps any gold evidence span."""
    for result in results[:3]:
        metadata = result.get("metadata") or {}
        doc_id = result.get("document_id")

        chunk_start = metadata.get("start_char")
        chunk_end = metadata.get("end_char")

        if chunk_start is None or chunk_end is None:
            continue

        for evidence in gold_evidence:
            if doc_id != evidence["document_id"]:
                continue

            evidence_start = evidence["normalized_start_char"]
            evidence_end = evidence["normalized_end_char"]

            if overlaps(
                int(chunk_start),
                int(chunk_end),
                int(evidence_start),
                int(evidence_end),
            ):
                return 1

    return 0


def validate_gold_evidence(questions):
    """Check that all evidence items have valid normalized offsets."""
    count = 0

    for question in questions:
        for evidence in question["gold_evidence"]:
            start = evidence.get("normalized_start_char")
            end = evidence.get("normalized_end_char")

            if start is None or end is None or int(start) >= int(end):
                raise ValueError(
                    f"Invalid normalized offsets: {question['question_id']}"
                )

            count += 1

    print(f"Validated {count} gold evidence offsets.")


def main():
    if not QUESTIONS_FILE.exists():
        raise FileNotFoundError(
            f"Missing benchmark file: {QUESTIONS_FILE}"
        )

    benchmark = json.loads(
        QUESTIONS_FILE.read_text(encoding="utf-8")
    )
    questions = benchmark["questions"]

    validate_gold_evidence(questions)

    embedder = MyEmbedder(MODEL_NAME)
    store = PgVectorStore(
        database_url=DATABASE_URL,
        dimensions=384,
    )

    configurations = [
        ("A", "fixed_size"),
        ("B", "by_paragraph"),
        ("C", "by_paragraph"),
    ]

    records = []

    print(f"Loaded {len(questions)} benchmark questions.")

    for index, question in enumerate(questions, start=1):
        question_id = question["question_id"]
        query = question["question"]
        gold = question["gold_evidence"]
        query_vector = embedder.embed_query(query)

        print(f"\n[{index}/{len(questions)}] {question_id}: {query}")

        for config_name, strategy in configurations:
            filters = None

            if config_name == "C":
                filters = question.get("metadata_filter")

            start_time = time.perf_counter()

            results = store.search(
                strategy=strategy,
                query_vector=query_vector,
                top_k=3,
                filters=filters,
            )

            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000

            hit1 = hit_at_1(results, gold)
            full_evidence3 = full_evidence_hit_at_3(
                results, gold
            )
            overlap_evidence3 = overlap_evidence_hit_at_3(
                results, gold
            )

            record = {
                "question_id": question_id,
                "split": question["split"],
                "config": config_name,
                "strategy": strategy,
                "filters": filters,
                "hit_at_1": hit1,
                "full_evidence_hit_at_3": full_evidence3,
                "overlap_evidence_hit_at_3": overlap_evidence3,
                "retrieval_time_ms": round(elapsed_ms, 3),
                "top_results": [],
            }

            for rank, result in enumerate(results, start=1):
                record["top_results"].append({
                    "rank": rank,
                    "document_id": result.get("document_id"),
                    "score": float(result.get("score", 0)),
                    "metadata": result.get("metadata") or {},
                    "text": result.get("text", ""),
                })

            records.append(record)

            print(
                f"  {config_name}: "
                f"Hit@1={hit1}, "
                f"Full Evidence@3={full_evidence3}, "
                f"Overlap Evidence@3={overlap_evidence3}, "
                f"time={elapsed_ms:.2f} ms"
            )

    OUTPUT_JSON.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with OUTPUT_CSV.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        fields = [
            "question_id",
            "split",
            "config",
            "strategy",
            "filters",
            "hit_at_1",
            "full_evidence_hit_at_3",
            "overlap_evidence_hit_at_3",
            "retrieval_time_ms",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )
        writer.writeheader()

        for record in records:
            row = {
                key: record[key]
                for key in fields
            }
            row["filters"] = json.dumps(
                row["filters"],
                ensure_ascii=False,
            )
            writer.writerow(row)

    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")

    for split in ("dev", "test"):
        print(f"\n{split.upper()}")

        for config_name in ("A", "B", "C"):
            subset = [
                item for item in records
                if item["split"] == split
                and item["config"] == config_name
            ]

            if not subset:
                continue

            count = len(subset)

            hit1_avg = sum(
                x["hit_at_1"] for x in subset
            ) / count

            full_avg = sum(
                x["full_evidence_hit_at_3"]
                for x in subset
            ) / count

            overlap_avg = sum(
                x["overlap_evidence_hit_at_3"]
                for x in subset
            ) / count

            time_avg = sum(
                x["retrieval_time_ms"]
                for x in subset
            ) / count

            print(
                f"{config_name}: "
                f"Hit@1={hit1_avg:.3f}, "
                f"Full Evidence@3={full_avg:.3f}, "
                f"Overlap Evidence@3={overlap_avg:.3f}, "
                f"Avg retrieval={time_avg:.2f} ms"
            )

    print("\nSaved:")
    print(OUTPUT_JSON)
    print(OUTPUT_CSV)


if __name__ == "__main__":
    main()
