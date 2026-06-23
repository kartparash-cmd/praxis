# Learning record format

A learning record is an "ADR for your brain": it captures a non-obvious thing
you have **demonstrated** you understand. Written on evidence, never on coverage.

Records live in `learning-records/NNNN-slug.md`. The numeric prefix increments.

## Frontmatter

Two blocks. **You (the model) own the top block. `praxis.py` owns the derived
block — never hand-edit it.**

```
---
id: 0007
title: pgvector HNSW index tuning
created: 2026-06-23
mastery_level: probing        # optional; deep mode only: probing | mastered
box: 3                        # DERIVED — praxis owns. Leitner box 1..5.
streak: 2                     # DERIVED — consecutive recalls.
last_tested: 2026-06-21       # DERIVED — or "never".
times_tested: 3               # DERIVED.
due: yes                      # DERIVED — yes/no.
---
```

To change any derived field, call the CLI — do not edit the file by hand:

```
praxis record 0007 --result recalled    # or: forgotten
```

If frontmatter ever looks wrong, recover from the event log:

```
praxis rebuild      # recompute every record's derived block from events.jsonl
praxis lint         # validate; fails loudly on schema drift
```

## Body

Free markdown. Keep it tight:

```
## What this record captures
The one insight, in your own words. If you can't write it plainly, it isn't learned.

## Recall questions
- 2-4 retrieval questions. These feed future warm-ups.
```

## Why the split exists

Leitner scheduling, streak counting, and date math are deterministic. An LLM
re-deriving them from prose over 50 sessions drifts and miscounts. So the
append-only `events.jsonl` is the source of truth and `praxis.py` is the only
writer of scheduling state. You teach and judge; the script counts.
