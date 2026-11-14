
"""Real local embedding provider using Sentence Transformers."""
import math
from sentence_transformers import SentenceTransformer


class MyEmbedder:
    """Generate real text embeddings using a local Sentence Transformer."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

        dimensions = self.model.get_sentence_embedding_dimension()
        if dimensions is None:
            raise ValueError("Could not determine embedding dimensions")

        self.dimensions = int(dimensions)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return normalized document vectors in input order."""
        if not texts:
            return []

        if not all(isinstance(text, str) for text in texts):
            raise TypeError("All document texts must be strings")

        vectors = self.model.encode(
            texts,
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        result = vectors.tolist()

        if len(result) != len(texts):
            raise ValueError("Embedding count does not match input count")

        for vector in result:
            if len(vector) != self.dimensions:
                raise ValueError("Unexpected embedding dimension")
            if not all(math.isfinite(value) for value in vector):
                raise ValueError("Embedding contains non-finite values")

        return result

    def embed_query(self, question: str) -> list[float]:
        """Return a normalized query vector compatible with document vectors."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")

        vector = self.model.encode(
            question,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        if len(vector) != self.dimensions:
            raise ValueError("Unexpected query embedding dimension")

        if not all(math.isfinite(value) for value in vector):
            raise ValueError("Query embedding contains non-finite values")

        return vector
