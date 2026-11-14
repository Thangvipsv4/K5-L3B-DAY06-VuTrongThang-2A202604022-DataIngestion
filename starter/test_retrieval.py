from src.embeddings import MyEmbedder
from src.store import PgVectorStore

DATABASE_URL = "postgresql://day6:day6_local_only@127.0.0.1:55433/day6_lab"
def main():
    embedder = MyEmbedder("sentence-transformers/all-MiniLM-L6-v2")
    store = PgVectorStore(database_url=DATABASE_URL, dimensions=384)

    question = (
        "Which earlier mathematical or statistical ideas are identified "
        "in the history lesson as foundations relevant to machine learning?"
    )
    query_vector = embedder.embed_query(question)

    experiments = [
        ("A - fixed size", "fixed_size", None),
        ("B - paragraph", "by_paragraph", None),
        ("C - paragraph + metadata filter", "by_paragraph",
         {"topic": "1-Introduction"}),
    ]

    print("\\nQUESTION:", question)

    for label, strategy, filters in experiments:
        print("\\n" + "=" * 70)
        print(label)
        print("Strategy:", strategy)
        print("Filters:", filters)

        results = store.search(
            strategy=strategy,
            query_vector=query_vector,
            top_k=3,
            filters=filters,
        )

        for rank, result in enumerate(results, start=1):
            print(f"\\nRank {rank}")
            print("Score:", result.get("score"))
            print("Document:", result.get("document_id"))
            print("Metadata:", result.get("metadata"))
            print("Text:", result.get("text", "")[:500].replace("\\n", " "))

if __name__ == "__main__":
    main()

