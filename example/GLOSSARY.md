# Glossary

Terms earned in this workspace (promoted only once demonstrated).

- **HNSW** — Hierarchical Navigable Small World. A graph-based approximate
  nearest-neighbour index. Trades a little recall for a large query speedup vs an
  exact scan.
- **ef_search** (`hnsw.ef_search`) — pgvector query-time knob. Higher = better
  recall, slower query; lower = faster, may miss true neighbours.
- **exact scan** — answering a similarity query by comparing the query vector to
  every row. Correct but O(n); fine at small row counts, a latency cliff at scale.
