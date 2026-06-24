# Example workspace

A hand-verified, minimal praxis workspace so you can see the shape before running
it for real. It contains one audited gap, one lesson, and one learning record
already in box 2 (one successful recall).

Try it:

```bash
cd example
python3 ../skills/praxis/praxis.py map      # see the one record's state
python3 ../skills/praxis/praxis.py due      # see whether it's due for review
```

Then open `lessons/0001-pgvector-hnsw.html` in a browser to see what a lesson
looks like. The audit it came from is in `audits/0001-pgvector-hnsw.md`.
