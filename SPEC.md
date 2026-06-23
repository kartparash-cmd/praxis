# SPEC — **praxis** (audit-led, teach as a first-class mode)

A Claude Code skill that **audits a real repo for gaps, then teaches you until you own them.** Public, polished, forkable — with a thin private overlay for Kay's own use.

> Revised to Option 2 after /autoplan. The engine is "understand a repo deeply." Two verbs sit on it: **audit** (find the gaps — the FDE job, the shareable artifact) and **teach** (close them — spaced retrieval, lessons, mastery). Audit feeds teach.

**Two goals (co-equal):**
1. A genuinely good tool Kay uses on-demand to learn his own stacks.
2. A public artifact worth forking — the reputation play. Differentiated because it audits *your* code (uncrowded category), and its **output is the shareable thing**.

---

## The engine + two verbs

```
/praxis                 # in a repo → AUDIT: find real gaps, propose with evidence
/praxis teach <topic>   # TEACH: spaced-retrieval lesson on a topic (or an audited gap)
/praxis teach --deep <topic>   # mastery-gated: advance only on a 5-probe checklist
/praxis                 # with an existing workspace → recall warm-up, then continue
```

Audit → pick a gap → teach it → it sticks. The teaching machinery is fully intact; it's just *fed by* the auditor instead of a mission interview.

## Core flows

**AUDIT (default, in a repo):**
1. Scan: dependency manifest(s) + `git log --since` + file tree.
2. For each candidate gap, **grep to verify it actually exists** (e.g. dep present in manifest AND companion-pattern absent in code). Never assert from the manifest alone.
3. Output 2-4 candidate gaps, each with **inline evidence** (`file:line`) and a confidence note. Propose, never auto-pick.
4. User picks one → offer to `teach` it (creates/updates a learning record + lesson).
5. The audit output itself is a clean, copy-pasteable artifact (this is the shareable unit).

**TEACH (session loop):**
1. Load state: `MISSION.md`, `NOTES.md`; `praxis due` for the review queue.
2. **Recall warm-up** (if records exist): the queue from `praxis due` — forgotten-first → never-tested → longest-untested. Re-teach anything lost before new material.
3. Teach ONE concept → self-contained HTML lesson ending in a Recall quiz (`<details>` answers). Lessons **cite `RESOURCES.md` inline**; flag low-confidence claims.
4. `praxis record <id> --result recalled|forgotten` after each tested item (the CLI does the math; the model never hand-edits streak/date/box).
5. **(--deep only)** Advance only when a **discrete N-of-5 probe checklist** passes (explain / apply to a novel case / identify when it does-or-doesn't apply / critique alternatives / teach back). No "80%" — pass/fail probes with rubrics.
6. Queue next-best lesson in `NOTES.md > ## Next up`.

## State — owned by `praxis.py`, NOT hand-edited (Eng-critical)

A deterministic algorithm (Leitner boxes, streaks, date math) must not run as prose over hand-edited YAML — it silently corrupts within weeks. So:

- **`praxis.py`** (Python stdlib, zero deps) owns ALL state mutation. The model *reads* records freely but *writes* only via the CLI.
- **`learning-records/events.jsonl`** is the append-only source of truth (one line per tested event). Per-record `.md` frontmatter is a **derived cache** the script rebuilds (`praxis rebuild`). Any corruption is recoverable.
- **Validate-on-read** (`praxis lint`): schema drift surfaces loudly in session 13, not session 50.

This is a CLI over markdown — **not** an app or a database. It does not violate the OUT-of-scope list.

### `praxis.py` commands
| cmd | does |
|---|---|
| `praxis due [--count] [--quiet]` | print the ordered review queue (forgotten → never-tested → longest-untested); `--quiet` no-ops cleanly when no workspace |
| `praxis record <id> --result recalled\|forgotten [--date YYYY-MM-DD]` | append event, recompute that record's box/streak/last_tested atomically |
| `praxis new --title "..." [--deep]` | create next `NNNN-slug.md` record with valid frontmatter |
| `praxis map` | mastery map: every record with box, streak, last-tested, due |
| `praxis rebuild` | recompute ALL frontmatter from `events.jsonl` |
| `praxis lint` | validate every record's frontmatter against the fixed schema |

### Workspace layout (per-directory, single source of truth)
```
<workspace>/
  MISSION.md                   # why you're learning; grounds teach
  NOTES.md                     # prefs + "## Next up"
  GLOSSARY.md
  RESOURCES.md                 # high-trust sources (public seed ships in repo)
  audits/NNNN-*.md             # saved audit reports (the shareable artifact)
  lessons/NNNN-*.html          # one-concept, light-theme, printable
  learning-records/
    events.jsonl               # append-only source of truth
    NNNN-*.md                  # derived-cache frontmatter + lesson notes
```

## First run IS the demo (fixes disuse + the README GIF in one move)

Fresh clone, zero authored files → `/praxis` detects no state and immediately **audits the skill's own repo and teaches one gap, execution-graded**. Onboarding = wow moment = the demo GIF. No setup wall, and the differentiator shows on first contact (not the syllabus fallback).

## Execution-grading (trust-bounded)

The agent grades by running **skill-authored tests** against what the user writes — never arbitrary student-authored side-effecting code. Inherits Claude Code's normal command-approval prompts (never bypasses them). README states the trust model: "runs code in your repo; point it at repos you trust."

## SessionStart hook (opt-in, off by default)

Project-scoped (`.claude/settings.json` in the workspace, never global), pure-script (`praxis due --quiet --count`), **no-op with empty output when no workspace exists**, hard timeout, no model calls / no network. README documents the exact snippet + warns against installing it globally.

## Public repo + private overlay

- **Public repo** = the full skill (audit + teach + deep + opt-in hook). Complete, not crippled.
- **Private overlay** (gitignored, NOT a fork): a local config the skill reads *if present* — Kay's project registry, default stacks, seeded resources, his workspaces. **Detected silently: zero user-facing references when absent.**
- **Public seed `RESOURCES.md`** ships so the public version honors its own "cite your sources" rule (resolves the parametric-knowledge contradiction).

## Reputation deliverables (first-class)
- README leads with ONE plain sentence: *"Point praxis at your repo. It finds what's missing or wrong, then teaches you until you own it."* → demo GIF → 3-line "why not the other forks" → install. Schema/attribution/license below the fold.
- Demo GIF MUST show: real repo → praxis finds a real gap with evidence → user writes the fix → test runs green/red.
- MIT LICENSE + credits to Matt Pocock, Tanish Girotra, adamos486 (Bloom's deep-mode idea reimplemented, not copied).
- **Distribution motion** (the gap the review flagged): post audit outputs run on recognizable OSS repos; reply-with-receipts to the 3 original authors; submit to Awesome Claude Code; 30-day kill date if zero external signal.

## v1 scope (ship this) vs deferred

**v1 (build now):** `praxis.py` (full state CLI + events.jsonl) · SKILL.md with **audit** + **teach** (light) · per-directory workspace + format docs · public seed RESOURCES.md · honest README + one hand-verified example workspace · LICENSE.

**Deferred to v1.x / v2 (built, gated, after the core proves out):** `--deep` mastery mode · execution-grading · the SessionStart hook · Anki export. Each is real but is the highest "won't-run-reliably-from-prose" / trust-surface risk — layer them once the core holds over a few weeks.

## Explicitly OUT
- No app, no web service, no database (a stdlib CLI over markdown is allowed).
- No custom SRS algorithm beyond Leitner (Anki export is the escape hatch, deferred).
- No multi-user / accounts / sync. No audio/voice. No always-on hooks.

---

## /autoplan REVIEW REPORT — 2026-06-23

Three independent voices (CEO/strategy, Eng/architecture, DX/developer-experience). Design phase skipped (no product UI). Auto-decided with the 6 principles; the premise challenge was put to the user, who chose **Option 2 (reframe to audit-led)**.

### Review scores
- **CEO:** Reframe (not build-as-spec). A 4th /teach fork can't carry the reputation goal; the audit primitive can. → **adopted (Option 2).**
- **Eng:** Deterministic algorithm as prose over hand-edited YAML corrupts within weeks. → **adopted: `praxis.py` + events.jsonl owns state.**
- **DX:** 5.5/10 as-spec; first run shows the undifferentiated path. → **adopted: first run IS the demo.**

### Cross-phase themes (independently flagged by 2+ voices)
1. Flashy features over-funded for v1 → **deferred deep/exec/hook/Anki.**
2. Disuse is the named death → **first run is the demo.**
3. Differentiator real but fragile/mis-worded → **audit-led framing + evidence-first gap detection.**

### Auto-decided (folded into this revision)
AD1 `praxis.py` owns state + events.jsonl truth · AD2 N-of-5 probes not "80%" · AD3 propose-with-evidence + grep-to-verify · AD4 hook project-scoped/no-op/timeout · AD5 execution-grading runs skill-authored tests + inherits approval · AD6 first run is the demo · AD7 public seed RESOURCES + silent overlay · AD8 README leads with the plain sentence.

### Taste decision — resolved
T1 Name → **praxis** (brandable) + invocation `/praxis` (avoids `/teach` collision); keyword carried in the description/README for discovery.
