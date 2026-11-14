import csv
import os
from pathlib import Path

from src.ingestion import load_markdown
from src.chunking import fixed_size, by_paragraph
from src.embeddings import MyEmbedder
from src.store import PgVectorStore

DATA_DIR = Path("data/raw/ml_lessons")
MANIFEST_PATH = Path("data/processed/manifest.csv")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://day6:day6_local_only@localhost:55433/day6_lab",
)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def main():
    # 1. Read manifest
    with MANIFEST_PATH.open(encoding="utf-8-sig") as f:
        documents = list(csv.DictReader(f))

    print("Documents in manifest:", len(documents))

    # 2. Load documents and create chunks
    fixed_chunks = []
    paragraph_chunks = []

    for i, row in enumerate(documents, start=1):
        path = DATA_DIR / row["source_path"]

        if not path.is_file():
            raise FileNotFoundError(f"Missing source document: {path}")

        pages = load_markdown(
            path=path,
            document_id=row["document_id"],
            source=row["source"],
            metadata=row,
        )

        for page in pages:
            fixed_chunks.extend(
                fixed_size(page, size=500, overlap=50)
            )

            paragraph_chunks.extend(
                by_paragraph(page, max_size=1000)
            )

        print(f"Loaded {i}/{len(documents)}: {path.name}")

    print("\n=== CHUNK COUNTS ===")
    print("Fixed-size:", len(fixed_chunks))
    print("By-paragraph:", len(paragraph_chunks))

    # 3. Initialize real embedding model
    embedder = MyEmbedder(MODEL_NAME)

    print("\nEmbedding model:", embedder.model_name)
    print("Dimensions:", embedder.dimensions)

    # 4. Initialize vector store
    store = PgVectorStore(
        database_url=DATABASE_URL,
        dimensions=embedder.dimensions,
    )
    store.create_schema()

    # 5. Embed and store fixed-size chunks
    print("\nEmbedding fixed-size chunks...")
    fixed_vectors = embedder.embed_documents(
        [chunk.text for chunk in fixed_chunks]
    )

    store.upsert(
        strategy="fixed_size",
        chunks=fixed_chunks,
        vectors=fixed_vectors,
    )
    print("Stored fixed-size chunks:", len(fixed_chunks))

    # 6. Embed and store paragraph chunks
    print("\nEmbedding paragraph chunks...")
    paragraph_vectors = embedder.embed_documents(
        [chunk.text for chunk in paragraph_chunks]
    )

    store.upsert(
        strategy="by_paragraph",
        chunks=paragraph_chunks,
        vectors=paragraph_vectors,
    )
    print("Stored paragraph chunks:", len(paragraph_chunks))

    print("\n=== INGESTION COMPLETED ===")
    print("Documents:", len(documents))
    print("Fixed-size vectors:", len(fixed_vectors))
    print("Paragraph vectors:", len(paragraph_vectors))
    print("Embedding dimensions:", embedder.dimensions)


if __name__ == "__main__":
    main()
