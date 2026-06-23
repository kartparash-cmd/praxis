# Mission format

`MISSION.md` captures **why** the user is learning this. Every lesson grounds to
it, so teaching stays concrete instead of textbook-abstract. In audit-led use,
the mission is often "be productive in THIS codebase" — which the repo itself
half-answers.

Keep it short. Interview only enough to fill it.

```
# Mission

## What I'm trying to do
One or two sentences. The real-world goal, not the topic.
e.g. "Ship a production RAG service on FastAPI + pgvector that returns in <300ms."

## Why it matters now
The deadline, project, or pressure making this worth learning today.

## What "done" looks like
The observable outcome that means I've learned enough.
e.g. "I can add and tune an HNSW index without copy-pasting, and explain the
recall/latency tradeoff."

## Starting point
What I already know vs. don't, so lessons land in my zone of proximal development.
```

If `MISSION.md` is empty or absent, the skill's first job is to ask why — except
on a fresh-clone first run, where it demos by auditing its own repo instead.
