---
id: 0001
title: pgvector HNSW index tuning
created: 2026-06-20
box: 2
streak: 1
last_tested: 2026-06-21
times_tested: 1
due: yes
---

## What this record captures
A similarity query without an ANN index is an exact O(n) scan. An HNSW index walks
a graph instead, trading a little recall for a large speedup. `hnsw.ef_search` is
the query-time recall/latency knob (higher = more recall, slower). Below a few
thousand rows, no index is the right call.

## Recall questions
- Why is a pgvector query without an ANN index O(n)?
- Which query-time setting trades recall for latency, and in which direction?
- When is having no index the correct choice?
