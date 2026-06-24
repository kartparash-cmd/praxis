# Changelog

All notable changes to praxis are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [0.1.0] — 2026-06-23

First public cut. Audit-led learning skill for Claude Code.

### Added
- **Audit mode** — `/praxis` scans a repo and proposes 2-4 evidence-backed gaps
  (`file:line` + confidence), verified by grep, never asserted from the manifest.
- **Teach mode** — spaced-retrieval lessons (Leitner), one concept each, HTML
  lessons ending in recall quizzes; sources cited from `RESOURCES.md`.
- **Deep mode (`--deep`)** — 5-probe mastery checklist (explain / apply / identify
  / critique / teach-back), pass/fail not a fabricated percentage.
- **Execution-grading protocol** — scratch-isolated, skill-authored test shown
  first, runs through Claude Code's approval prompt, with guardrails to decline
  unsafe or untrusted runs.
- **No-gap fallback** — proactive topic suggestions from mission / stack / recent
  git work instead of a blank prompt.
- **`praxis.py`** — stdlib state CLI (`due`, `record`, `new`, `map`, `rebuild`,
  `lint`). `events.jsonl` is the append-only source of truth with a monotonic
  `seq` tiebreaker; `.md` frontmatter is a rebuildable cache; `lint` detects drift.
- Opt-in project-scoped SessionStart hook (off by default).
- Test suite + CI; worked example workspace; MIT + attribution to Matt Pocock,
  Tanish Girotra, adamos486.
