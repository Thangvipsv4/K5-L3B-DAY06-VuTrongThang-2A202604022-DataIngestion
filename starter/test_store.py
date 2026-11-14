
from src.store import PgVectorStore

DATABASE_URL = (
    "postgresql://day6:day6_local_only@localhost:55433/day6_lab"
)

store = PgVectorStore(
    database_url=DATABASE_URL,
    dimensions=384,
)

store.create_schema()

print("PostgreSQL connection: OK")
print("Vector dimensions: 384")
print("Schema creation: OK")
