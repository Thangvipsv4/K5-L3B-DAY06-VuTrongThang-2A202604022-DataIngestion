
"""PostgreSQL + pgvector storage with cosine search and metadata filters."""
import math
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .models import Chunk


class PgVectorStore:
    # Only these metadata keys can be used as search filters.
    ALLOWED_FILTERS = {
        "topic",
        "lesson",
        "license",
        "document_type",
        "source",
        "location_type",
    }

    def __init__(self, database_url: str, dimensions: int) -> None:
        """Retain connection settings and validate vector dimensions."""
        if not database_url:
            raise ValueError("database_url must not be empty")

        if not isinstance(dimensions, int) or dimensions <= 0:
            raise ValueError("dimensions must be a positive integer")

        self.database_url = database_url
        self.dimensions = dimensions

    def _validate_vector(self, vector: list[float]) -> None:
        """Validate vector dimensions and numeric values."""
        if len(vector) != self.dimensions:
            raise ValueError(
                f"Expected {self.dimensions} dimensions, got {len(vector)}"
            )

        if not all(
            isinstance(value, (int, float))
            and math.isfinite(value)
            for value in vector
        ):
            raise ValueError("Vector contains invalid numeric values")

    @staticmethod
    def _vector_literal(vector: list[float]) -> str:
        """Convert a vector to PostgreSQL vector literal format."""
        return "[" + ",".join(str(float(value)) for value in vector) + "]"

    def create_schema(self) -> None:
        """Create pgvector extension, storage table and indexes."""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS ingestion_chunks (
                        strategy TEXT NOT NULL,
                        chunk_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        page INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding VECTOR({self.dimensions}) NOT NULL,
                        PRIMARY KEY (strategy, chunk_id)
                    )
                    """
                )

                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_chunks_strategy_document
                    ON ingestion_chunks (strategy, document_id)
                    """
                )

                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_chunks_metadata
                    ON ingestion_chunks USING GIN (metadata)
                    """
                )

    def upsert(
        self,
        strategy: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> None:
        """Replace chunks for affected documents and insert their vectors."""
        if not strategy:
            raise ValueError("strategy must not be empty")

        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have equal lengths")

        if not chunks:
            return

        for chunk, vector in zip(chunks, vectors):
            if not chunk.chunk_id or not chunk.document_id:
                raise ValueError("chunk_id and document_id are required")

            if not chunk.source:
                raise ValueError("chunk source is required")

            if chunk.page < 1:
                raise ValueError("page must be >= 1")

            self._validate_vector(vector)

        document_ids = sorted({chunk.document_id for chunk in chunks})

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                # Remove old chunks for affected documents.
                # This also removes obsolete chunks after re-ingestion.
                for document_id in document_ids:
                    cur.execute(
                        """
                        DELETE FROM ingestion_chunks
                        WHERE strategy = %s AND document_id = %s
                        """,
                        (strategy, document_id),
                    )

                rows = [
                    (
                        strategy,
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.source,
                        chunk.page,
                        chunk.text,
                        Jsonb(chunk.metadata),
                        self._vector_literal(vector),
                    )
                    for chunk, vector in zip(chunks, vectors)
                ]

                cur.executemany(
                    """
                    INSERT INTO ingestion_chunks (
                        strategy,
                        chunk_id,
                        document_id,
                        source,
                        page,
                        text,
                        metadata,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                    """,
                    rows,
                )

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search by cosine similarity with optional metadata filters."""
        if not strategy:
            raise ValueError("strategy must not be empty")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        self._validate_vector(query_vector)

        filters = filters or {}

        invalid_keys = set(filters) - self.ALLOWED_FILTERS
        if invalid_keys:
            raise ValueError(
                f"Unsupported metadata filters: {sorted(invalid_keys)}"
            )

        conditions = ["c.strategy = %s"]
        params: list[Any] = [self._vector_literal(query_vector), strategy]

        for key, value in sorted(filters.items()):
            if value is None or isinstance(value, (dict, list)):
                raise ValueError(f"Invalid filter value for {key}")

            conditions.append("c.metadata ->> %s = %s")
            params.extend([key, str(value)])

        params.append(top_k)

        sql = f"""
            WITH query_vector AS (
                SELECT %s::vector AS embedding
            )
            SELECT
                c.chunk_id,
                c.document_id,
                c.source,
                c.page,
                c.text,
                c.metadata,
                1 - (c.embedding <=> q.embedding) AS score
            FROM ingestion_chunks AS c
            CROSS JOIN query_vector AS q
            WHERE {" AND ".join(conditions)}
            ORDER BY c.embedding <=> q.embedding
            LIMIT %s
        """

        with psycopg.connect(
            self.database_url,
            row_factory=dict_row,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()
