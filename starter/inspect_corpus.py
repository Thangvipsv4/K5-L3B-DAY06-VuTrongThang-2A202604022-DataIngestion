
import csv
from collections import defaultdict

manifest_path = "data/processed/manifest.csv"

groups = defaultdict(list)

with open(manifest_path, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        topic = row.get("topic", "Unknown")
        groups[topic].append(row)

print("TOTAL DOCUMENTS:", sum(len(items) for items in groups.values()))

for topic, documents in sorted(groups.items()):
    print(f"\n{'=' * 60}")
    print(f"TOPIC: {topic} | DOCUMENTS: {len(documents)}")
    print("=" * 60)

    for doc in documents:
        print(
            f"- {doc.get('title', '')} "
            f"| lesson={doc.get('lesson', '')} "
            f"| type={doc.get('document_type', '')}"
        )
