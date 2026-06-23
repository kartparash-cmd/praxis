# Audit — example-rag-service — 2026-06-23

Repo audited for gaps. Each is verified against the code, not inferred from the
manifest alone.

## Gap 1 — pgvector present, no ANN index (high confidence)
- **Evidence:** `requirements.txt:7` pins `pgvector==0.2.5`. Grepped `migrations/`
  and `models.py` for `USING hnsw` / `USING ivfflat` → no matches. The embedding
  column is queried with `<->` (`search.py:41`) but the table has only a btree PK.
- **Why it matters:** every similarity query is a sequential scan over all rows.
  At a few thousand rows it's fine; at 100k+ it's a latency cliff. An HNSW index
  is the standard fix, with a recall/build-time tradeoff worth understanding.

## Gap 2 — no connection pooling (medium confidence)
- **Evidence:** `db.py:12` opens a new `psycopg.connect(...)` per request inside
  the FastAPI dependency; no pool object anywhere. Grepped for `pool` → none.
- **Why it matters:** under concurrency you exhaust Postgres connections and add
  per-request connect latency.

_Picked for the example: Gap 1 → see `lessons/0001-pgvector-hnsw.html`._
