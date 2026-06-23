---
name: praxis
description: Audit a real codebase for gaps, then teach you until you own them. Point /praxis at a repo and it finds what's missing or wrong (with evidence), then runs spaced-retrieval lessons to close each gap. Use when the user wants to get productive in an unfamiliar codebase, learn their own stack deeply, or asks to "audit", "teach me", or "what don't I understand here".
argument-hint: "[teach <topic>] [--deep]  (no args = audit the current repo)"
disable-model-invocation: true
---

The user invoked **praxis**. This is a stateful, multi-session tool. There are two
verbs over one engine ("understand a repo deeply"):

- **audit** (default, when run in a repo with no explicit topic) — find the real
  gaps in this codebase and propose them with evidence.
- **teach** — close a gap (or any topic) with a spaced-retrieval lesson that sticks.

Audit feeds teach: find a gap → teach it → it sticks.

## The golden rule of state

`praxis.py` (in this skill's directory) owns ALL scheduling state — Leitner boxes,
streaks, dates. **You read records freely. You mutate state ONLY by calling the
CLI.** Never hand-edit the derived frontmatter block (`box`, `streak`,
`last_tested`, `times_tested`, `due`). If you hand-edit it, it drifts and the
whole tool rots. Call `python3 <skilldir>/praxis.py …` instead.

## Routing — decide what the user wants

1. **`/praxis teach <topic>`** or the user names something to learn → TEACH mode.
2. **`/praxis` with an existing workspace** (a `learning-records/` dir is present)
   → start with the RECALL WARM-UP, then continue teaching the queued next lesson.
3. **`/praxis` in a git repo with no workspace** → AUDIT mode.
4. **Fresh clone of THIS skill's own repo, no workspace anywhere** → FIRST-RUN
   DEMO: audit this repo and teach one gap, so the first invocation is the wow
   moment (see "First run is the demo").

## AUDIT mode

Goal: a short list of *real, evidence-backed* gaps in this codebase — never a
generic syllabus, never an unverified guess.

1. **Scan** (cheap, read-only):
   - Dependency manifest(s): `requirements.txt`, `pyproject.toml`, `package.json`,
     `go.mod`, `Cargo.toml`, etc.
   - Recent history: `git log --since="2 weeks ago" --stat` (what's being touched).
   - File tree / entry points.
2. **Verify before claiming a gap.** A dependency in a manifest is NOT a gap. For
   each candidate, grep the code to confirm the gap actually exists. Example: a
   `pgvector` dep is only an "HNSW index missing" gap if you grep migrations/DDL
   and find no `USING hnsw` / `USING ivfflat`. Show the grep result.
3. **Propose, never auto-pick.** Output 2-4 candidates, each as:
   - **Gap** — one line.
   - **Evidence** — `file:line` showing it, plus what's absent and how you checked.
   - **Confidence** — high / medium, with why.
   - **Why it matters** — the concrete risk or capability.
4. **Save the audit** to `audits/NNNN-<slug>.md` — this is a clean, shareable
   artifact (the user may post it). Keep it copy-pasteable: no chatter, just the
   gaps + evidence.
5. Ask which gap to learn. On their pick → switch to TEACH mode for it.

If you cannot show evidence for any gap, say so and offer topic-driven teaching
instead. A confident wrong gap is worse than admitting you found none.

## TEACH mode — the session loop

Do not skip steps.

**On start:**
1. Load state: read `MISSION.md`, `NOTES.md`. Run the review queue:
   `python3 <skilldir>/praxis.py due`
2. **Recall warm-up** (if records exist): ask the 2-3 questions from the top of the
   queue (forgotten-first → never-tested → longest-untested — the CLI already
   ordered them). The user answers from memory; effortful recall is the point.
3. **Grade and stamp each tested item** via the CLI — never by editing files:
   `python3 <skilldir>/praxis.py record <id> --result recalled`  (or `forgotten`)
   If something was forgotten, briefly re-teach it before any new material.
4. If recall is solid, move to the next lesson in the zone of proximal development
   (from `NOTES.md > ## Next up`, or the audited gap the user picked).

**Teaching one concept:**
- Teach exactly ONE tightly-scoped thing, tied to the mission/gap.
- Ground every load-bearing claim in `RESOURCES.md`. Cite inline. If you have no
  source for a claim, flag it as low-confidence — do not state it as fact.
- Produce a **lesson**: one self-contained HTML file in `lessons/NNNN-slug.html`,
  light theme, printable, no external dependencies. It teaches the one concept and
  ends with a **Recall** section: 2-4 retrieval questions with answers hidden
  behind `<details>`. Give the user a one-line command to open it.
- Create the matching record if new:
  `python3 <skilldir>/praxis.py new --title "…"`  (add `--deep` for mastery mode)
  Then write the record body (what it captures, recall questions). Leave the
  derived frontmatter to the CLI.

**On session end:**
1. Promote newly-earned terms to `GLOSSARY.md`.
2. Write the next-best lesson candidate to `NOTES.md` under `## Next up`, so the
   next session starts with intent, not deliberation.

## Deep mode (`--deep`) — DEFERRED, gate behind the flag

When the user passes `--deep`, advance only when the concept passes a **discrete
5-probe checklist** (not a fabricated percentage). Each probe is pass/fail against
a rubric:

1. **Explain** it plainly in their own words.
2. **Apply** it to a novel case you invent on the spot.
3. **Identify** when it does and does NOT apply.
4. **Critique** an alternative approach.
5. **Teach it back** as if to a beginner.

Advance only when all 5 pass (state it as "5/5 probes", never "X%"). On a miss,
re-teach that probe's gap. Mark the record `mastery_level: mastered` (you may set
this descriptive field; it is not a scheduling field). Keep `--deep` simple until
the light core has proven out over real use.

## First run is the demo

If invoked on a fresh clone of THIS skill's own repo with no workspace anywhere:
audit THIS repo (it has `praxis.py`, `SKILL.md`, the reference docs) and teach one
real concept from it — e.g. "why scheduling state lives in `events.jsonl` not in
the markdown." Run the full loop (lesson + recall + `praxis record`) so the user
experiences the wow moment in under a minute, with zero setup. This IS the
onboarding and the demo.

## Execution-grading — DEFERRED, trust-bounded

When enabled, grade understanding by having the user write a small function/query,
then run a **skill-authored test** against it (never arbitrary user-typed
side-effecting code). Always go through Claude Code's normal command-approval
prompt — never bypass it. Only run code in repos the user trusts.

## Guardrails

- The shareable artifact is the **audit output**, not chatter. Keep audits clean.
- Never assert a gap you didn't verify by grepping the code.
- Never hand-edit `box`/`streak`/`last_tested`/`due` — call `praxis.py`.
- Write a learning record only when understanding is **demonstrated**, not covered.
- If a private overlay (`.praxis-overlay/`) exists, read it silently. If it does
  not exist, behave identically and never mention it.
- Make opening a lesson one command. Default lessons to light theme, printable.
