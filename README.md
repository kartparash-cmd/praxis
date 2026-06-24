# praxis

**Point praxis at your repo. It finds what's missing or wrong — with evidence — then teaches you until you own it.**

A Claude Code skill. The other learning skills teach a syllabus. praxis teaches **your codebase**, and checks you by making you write the fix.

> **30-second demo:** in a repo, run `/praxis` → it surfaces a real gap with `file:line` evidence (e.g. *"pgvector present, no HNSW index — `search.py:41`"*) → you write the fix → a test runs and goes green. That last beat — it ran your code and checked you — is the whole point.

<!-- DEMO GIF goes here once recorded (docs/demo.gif). Must show, in order:
     (1) a real repo open, (2) /praxis finds a real gap with file:line evidence,
     (3) user writes the fix, (4) a test runs green. The execution-grading
     moment is the conversion — do not cut it. -->

## Why not the other /teach skills

| | praxis | typical /teach skill |
|---|---|---|
| Curriculum | **gaps in your actual repo**, found with evidence | a generic topic syllabus |
| Checks you by | making you **write the fix**, then running it | a self-graded quiz |
| Shareable output | a clean **audit report** you can post | nothing |

If you just want a tutor for a topic, the others are great. If you want to get productive in *this* codebase, praxis is built for that — which is also the forward-deployed-engineer job: land in an unfamiliar repo and get useful fast.

## Install

**As a plugin (recommended):**

```
/plugin marketplace add kartparash-cmd/praxis
/plugin install praxis@praxis
```

**Or as a plain skill** (clone and symlink the skill dir):

```bash
git clone https://github.com/kartparash-cmd/praxis.git
ln -s "$PWD/praxis/skills/praxis" ~/.claude/skills/praxis
```

Then, in any repo:

```
/praxis
```

With no arguments inside a repo, praxis **audits the codebase** and proposes real gaps. Pick one and it teaches you. The very first run (on a fresh clone) audits praxis's own repo and teaches a concept from it — so you see the whole loop in under a minute, zero setup.

## Usage

```
/praxis                      # audit the current repo for gaps
/praxis teach <topic>        # spaced-retrieval lesson on a topic (or an audited gap)
/praxis teach --deep <topic> # mastery mode: advance only on a 5-probe checklist
/praxis                      # (with a workspace) recall warm-up, then the next lesson
```

praxis treats the current directory as a learning **workspace** and keeps plain files in it: a mission, HTML lessons, a glossary, trusted resources, and learning records with spaced-retrieval state. No app, no database — everything is readable text you can edit or delete.

---

<details>
<summary><b>How retention works (and why state is a CLI, not prose)</b></summary>

praxis uses Leitner-style spaced retrieval: forgotten items resurface first, mastered ones earn longer gaps. The scheduling math (boxes, streaks, due-dates) is **not** left to the model to recompute from prose each session — that drifts and miscounts. Instead:

- `learning-records/events.jsonl` is an **append-only source of truth** (one line per recall result).
- `praxis.py` (Python stdlib, zero deps) is the only writer of scheduling state. The model reads records freely but mutates state only through the CLI.
- Any corruption is recoverable: `praxis rebuild` recomputes everything from the event log; `praxis lint` fails loudly on schema drift.

```
praxis due                          # the review queue, ordered
praxis record 0007 --result recalled
praxis map                          # mastery map
praxis rebuild                      # recompute state from events.jsonl
praxis lint                         # validate
```
</details>

<details>
<summary><b>Workspace layout</b></summary>

```
<workspace>/
  MISSION.md            why you're learning (grounds every lesson)
  NOTES.md              prefs + the next queued lesson
  GLOSSARY.md           terms you've earned
  RESOURCES.md          high-trust sources (a public seed ships in the repo)
  audits/NNNN-*.md      saved audit reports — the shareable artifact
  lessons/NNNN-*.html   one-concept, printable lessons
  learning-records/
    events.jsonl        append-only source of truth
    NNNN-*.md           derived state + lesson notes
```
</details>

<details>
<summary><b>Optional: review nudge on session start</b></summary>

praxis is pull-first — it runs when you invoke it. If you want a nudge when you open a project, add a **project-scoped** hook (never global) to that workspace's `.claude/settings.json`:

```json
{ "hooks": { "SessionStart": [ { "hooks": [
  { "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/skills/praxis/praxis.py due --quiet --count" }
] } ] } }
```

(Plain-skill install: point the command at `~/.claude/skills/praxis/praxis.py` instead.) It prints nothing when nothing is due, makes no model/network calls, and no-ops outside a workspace. Off by default on purpose. **Do not install it in your global `~/.claude/settings.json`** — it would fire in every repo.
</details>

<details>
<summary><b>Trust model</b></summary>

When execution-grading is enabled, praxis runs **skill-authored tests** against code you write — never arbitrary code — and always through Claude Code's normal command-approval prompt. Still: it runs code in your repo, so point it at repos you trust.
</details>

<details>
<summary><b>Private overlay (power users)</b></summary>

Drop a `.praxis-overlay/` in a workspace and praxis will read your project registry, default stacks, and seeded resources from it. It's detected silently — the public skill behaves identically without it. The overlay is gitignored; it never enters this repo.
</details>

## Credits

Builds on the workspace/mission model and spaced-retrieval loop from [Matt Pocock's /teach](https://github.com/mattpocock/skills) and [Tanish Girotra's spaced-retrieval fork](https://github.com/tanishg98/claude-teach-skill) (both MIT). The deep-mode mastery-gate idea is inspired by [adamos486's /teach](https://github.com/adamos486/skills) (reimplemented, not copied).

## License

MIT — see [LICENSE](./LICENSE).
