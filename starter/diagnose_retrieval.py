import time
from src.embeddings import MyEmbedder
from src.store import PgVectorStore

def timed(label, fn):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    print(f"{label}: {elapsed:.3f} seconds", flush=True)
    return result

def main():
    embedder = timed(
        "1. Load model",
        lambda: MyEmbedder("sentence-transformers/all-MiniLM-L6-v2")
    )

    query_vector = timed(
        "2. Embed question",
        lambda: embedder.embed_query("What is machine learning?")
    )

    store = PgVectorStore(
        database_url="postgresql://day6:day6_local_only@127.0.0.1:55433/day6_lab",
        dimensions=384,
    )

    results1 = timed(
        "3. First vector search",
        lambda: store.search("fixed_size", query_vector, top_k=3)
    )

    print("First search returned:", len(results1), "chunks", flush=True)

    results2 = timed(
        "4. Second vector search",
        lambda: store.search("fixed_size", query_vector, top_k=3)
    )

    print("Second search returned:", len(results2), "chunks", flush=True)

    for i, result in enumerate(results2, 1):
        print(
            f"Rank {i}: score={result.get('score')}, "
            f"document={result.get('document_id')}"
        )

if __name__ == "__main__":
    main()
