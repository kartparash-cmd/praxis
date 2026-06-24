#!/usr/bin/env python3
"""praxis — state bookkeeping for the praxis learning skill.

The LLM teaches and judges; this script owns every deterministic thing:
Leitner scheduling, streak/box math, date arithmetic, and atomic single-record
writes. The model reads records freely but mutates state ONLY through here.

Source of truth: learning-records/events.jsonl (append-only). Per-record .md
frontmatter is a derived cache rebuilt from the log, so any corruption is
recoverable with `praxis rebuild`.

Stdlib only. No dependencies. Not an app, not a database — a CLI over markdown.
"""

import argparse
import datetime
import json
import os
import re
import sys
import tempfile

RECORDS_DIRNAME = os.path.join("learning-records")
EVENTS_FILENAME = "events.jsonl"

# Leitner boxes 1..5. Interval (days) before a box is due again. Box 1 = daily,
# box 5 = roughly monthly. A "forgotten" result resets to box 1; "recalled"
# promotes one box (capped at 5).
BOX_INTERVALS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 21}
MAX_BOX = 5

# Frontmatter fields the script owns (derived). The model owns title/created/
# mastery_level/notes; it must never write the derived block by hand.
DERIVED_FIELDS = ("box", "streak", "last_tested", "times_tested", "due")
SCHEMA_FIELDS = ("id", "title", "created") + DERIVED_FIELDS


# ---------- small helpers ----------

def today(args=None):
    if args is not None and getattr(args, "date", None):
        return args.date
    return datetime.date.today().isoformat()


def now_iso():
    """Wall-clock timestamp stamped on every event so ordering survives a
    rebuild. `date` drives Leitner logic (and is --date-overridable for tests);
    `ts` only breaks ties between same-date events."""
    return datetime.datetime.now().isoformat(timespec="seconds")


def norm_id(value):
    """Normalize an id so a hand-appended {"id":"1"} matches record 0001."""
    s = str(value)
    return s.zfill(4) if s.isdigit() else s


def workspace_paths(start="."):
    """Return (records_dir, events_path) for the workspace rooted at start."""
    records_dir = os.path.join(start, RECORDS_DIRNAME)
    events_path = os.path.join(records_dir, EVENTS_FILENAME)
    return records_dir, events_path


def has_workspace(start="."):
    records_dir, _ = workspace_paths(start)
    return os.path.isdir(records_dir)


def parse_frontmatter(text):
    """Parse a leading --- ... --- YAML-ish block into a dict. Flat key: value
    only (we never need nesting). Returns (frontmatter_dict, body_str)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]
    fm = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()
    return fm, body


def dump_frontmatter(fm, body):
    lines = ["---"]
    # Stable, human-readable field order.
    order = [k for k in SCHEMA_FIELDS if k in fm]
    order += [k for k in fm if k not in SCHEMA_FIELDS]
    for k in order:
        lines.append("{}: {}".format(k, fm[k]))
    lines.append("---")
    return "\n".join(lines) + "\n" + body


def atomic_write(path, text):
    """Write text to path atomically (temp file + os.replace)."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".praxis-tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())  # durable contents before the atomic rename
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def record_files(records_dir):
    if not os.path.isdir(records_dir):
        return []
    out = []
    for name in sorted(os.listdir(records_dir)):
        if re.match(r"^\d{4}-.*\.md$", name):
            out.append(os.path.join(records_dir, name))
    return out


def record_id_from_path(path):
    name = os.path.basename(path)
    m = re.match(r"^(\d{4})-", name)
    return m.group(1) if m else None


def read_events(events_path):
    events = []
    if not os.path.exists(events_path):
        return events
    with open(events_path) as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                sys.stderr.write(
                    "praxis: warning: corrupt event on line {} of {}\n".format(
                        ln, events_path))
    return events


def append_event(events_path, event):
    os.makedirs(os.path.dirname(events_path), exist_ok=True)
    # `seq` is a monotonic, in-data tiebreaker. `ts` (wall clock) collides at
    # sub-second granularity, so seq — not ts — guarantees that two same-date
    # events keep a deterministic order that survives a rebuild or a file
    # reordering. Without an ordering key in the data, same-day box/streak
    # would be unrecoverable.
    existing = read_events(events_path)
    next_seq = max((int(e.get("seq", 0)) for e in existing), default=0) + 1
    event.setdefault("ts", now_iso())
    event.setdefault("seq", next_seq)
    with open(events_path, "a") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())  # harden the source of truth against a torn append


# ---------- derivation (the only place scheduling math lives) ----------

def derive_state(rid, events):
    """Compute (box, streak, last_tested, times_tested) for a record id from
    its tested events in chronological order."""
    tested = [e for e in events
              if norm_id(e.get("id")) == rid and e.get("result") in ("recalled", "forgotten")]
    tested.sort(key=lambda e: (e.get("date", ""), int(e.get("seq", 0)), e.get("ts", "")))
    box, streak = 1, 0
    last_tested, times = "", 0
    for e in tested:
        times += 1
        last_tested = e.get("date", last_tested)
        if e["result"] == "recalled":
            box = min(box + 1, MAX_BOX)
            streak += 1
        else:
            box = 1
            streak = 0
    return box, streak, last_tested, times


def is_due(box, last_tested, ref_date):
    if not last_tested:
        return True  # never tested → always due
    interval = BOX_INTERVALS.get(box, 0)
    try:
        last = datetime.date.fromisoformat(last_tested)
        ref = datetime.date.fromisoformat(ref_date)
    except ValueError:
        return True
    return (ref - last).days >= interval


def load_records(records_dir, events_path, ref_date):
    """Return a list of record dicts with derived state merged in."""
    events = read_events(events_path)
    out = []
    for path in record_files(records_dir):
        rid = record_id_from_path(path)
        with open(path) as f:
            fm, body = parse_frontmatter(f.read())
        box, streak, last_tested, times = derive_state(rid, events)
        due = is_due(box, last_tested, ref_date)
        out.append({
            "id": rid,
            "path": path,
            "title": fm.get("title", "(untitled)"),
            "mastery": fm.get("mastery_level", ""),
            "box": box,
            "streak": streak,
            "last_tested": last_tested,
            "times_tested": times,
            "due": due,
            "last_result": _last_result(rid, events),
            "fm": fm,
            "body": body,
        })
    return out


def _last_result(rid, events):
    tested = [e for e in events
              if norm_id(e.get("id")) == rid and e.get("result") in ("recalled", "forgotten")]
    tested.sort(key=lambda e: (e.get("date", ""), int(e.get("seq", 0)), e.get("ts", "")))
    return tested[-1]["result"] if tested else ""


def write_derived(rec):
    """Re-stamp a record file's frontmatter derived block atomically."""
    fm = dict(rec["fm"])
    fm.setdefault("id", rec["id"])
    fm.setdefault("title", rec["title"])
    fm["box"] = str(rec["box"])
    fm["streak"] = str(rec["streak"])
    fm["last_tested"] = rec["last_tested"] or "never"
    fm["times_tested"] = str(rec["times_tested"])
    fm["due"] = "yes" if rec["due"] else "no"
    atomic_write(rec["path"], dump_frontmatter(fm, rec["body"]))


# ---------- review-queue ordering ----------

def review_queue(records):
    """Forgotten-first → never-tested → longest-untested. Only due records."""
    due = [r for r in records if r["due"]]

    def rank(r):
        if r["last_result"] == "forgotten":
            tier = 0
        elif r["times_tested"] == 0:
            tier = 1
        else:
            tier = 2
        # within tier, oldest last_tested first ("" sorts first = never)
        return (tier, r["last_tested"] or "")

    return sorted(due, key=rank)


# ---------- commands ----------

def cmd_due(args):
    if not has_workspace():
        if args.quiet:
            return 0
        print("praxis: no workspace here (no ./learning-records/).")
        return 0
    records_dir, events_path = workspace_paths()
    records = load_records(records_dir, events_path, today(args))
    queue = review_queue(records)
    if args.count:
        # In hook mode (--quiet), stay silent when nothing is due so a
        # SessionStart hook injects nothing on a quiet day.
        if args.quiet and not queue:
            return 0
        print(len(queue))
        return 0
    if args.quiet:
        # hook-friendly: print nothing when nothing is due
        if queue:
            print("praxis: {} review(s) due".format(len(queue)))
        return 0
    if not queue:
        print("Nothing due. {} record(s) tracked.".format(len(records)))
        return 0
    print("Review queue ({} due):".format(len(queue)))
    for r in queue:
        flag = "FORGOT" if r["last_result"] == "forgotten" else (
            "NEW" if r["times_tested"] == 0 else "box{}".format(r["box"]))
        print("  [{}] {} — {}  (last: {})".format(
            r["id"], flag, r["title"], r["last_tested"] or "never"))
    return 0


def cmd_record(args):
    records_dir, events_path = workspace_paths()
    if not has_workspace():
        sys.stderr.write("praxis: no workspace here.\n")
        return 1
    rid = args.id.zfill(4) if args.id.isdigit() else args.id
    paths = {record_id_from_path(p): p for p in record_files(records_dir)}
    if rid not in paths:
        sys.stderr.write("praxis: no record with id {}.\n".format(rid))
        return 1
    append_event(events_path, {"id": rid, "date": today(args), "result": args.result})
    # Recompute just this record and re-stamp it.
    records = load_records(records_dir, events_path, today(args))
    rec = next((r for r in records if r["id"] == rid), None)
    if rec is None:
        sys.stderr.write("praxis: record {} vanished mid-write.\n".format(rid))
        return 1
    write_derived(rec)
    print("Recorded {} for [{}] {} → box {}, streak {}.".format(
        args.result, rid, rec["title"], rec["box"], rec["streak"]))
    return 0


def _next_id(records_dir):
    ids = [int(record_id_from_path(p)) for p in record_files(records_dir)]
    return "{:04d}".format((max(ids) + 1) if ids else 1)


def cmd_new(args):
    records_dir, events_path = workspace_paths()
    os.makedirs(records_dir, exist_ok=True)
    rid = _next_id(records_dir)
    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")[:48] or "untitled"
    path = os.path.join(records_dir, "{}-{}.md".format(rid, slug))
    fm = {"id": rid, "title": args.title, "created": today(args)}
    if args.deep:
        fm["mastery_level"] = "probing"  # probing | mastered
    body = ("\n## What this record captures\n\n"
            "_Written only when understanding is demonstrated, not when covered._\n\n"
            "## Recall questions\n\n- \n")
    atomic_write(path, dump_frontmatter(fm, body))
    # Stamp derived fields so the record lints clean immediately.
    records = load_records(records_dir, events_path, today(args))
    rec = next((r for r in records if r["id"] == rid), None)
    if rec is not None:
        write_derived(rec)
    print("Created {}".format(path))
    return 0


def cmd_map(args):
    if not has_workspace():
        print("praxis: no workspace here.")
        return 0
    records_dir, events_path = workspace_paths()
    records = load_records(records_dir, events_path, today(args))
    if not records:
        print("No records yet.")
        return 0
    print("Mastery map ({} records):".format(len(records)))
    print("  id   box streak  due  last        title")
    for r in sorted(records, key=lambda r: r["id"]):
        print("  {}  {:>3} {:>6}  {:>3}  {:<11} {}".format(
            r["id"], r["box"], r["streak"], "yes" if r["due"] else "no",
            r["last_tested"] or "never", r["title"]))
    return 0


def cmd_rebuild(args):
    if not has_workspace():
        sys.stderr.write("praxis: no workspace here.\n")
        return 1
    records_dir, events_path = workspace_paths()
    records = load_records(records_dir, events_path, today(args))
    for r in records:
        write_derived(r)
    print("Rebuilt derived frontmatter for {} record(s) from {}.".format(
        len(records), EVENTS_FILENAME))
    return 0


def cmd_lint(args):
    if not has_workspace():
        sys.stderr.write("praxis: no workspace here.\n")
        return 1
    records_dir, events_path = workspace_paths()
    problems = 0
    # Required base fields + id/filename agreement.
    for path in record_files(records_dir):
        with open(path) as f:
            fm, _ = parse_frontmatter(f.read())
        for field in ("id", "title", "created"):
            if field not in fm:
                problems += 1
                sys.stderr.write("praxis: {} missing '{}'\n".format(path, field))
        if fm.get("id") and fm["id"] != record_id_from_path(path):
            problems += 1
            sys.stderr.write("praxis: {} id mismatch ({} vs filename)\n".format(
                path, fm["id"]))

    # Drift detection: stored derived block must equal what events.jsonl implies.
    # This is the schema-drift / hand-edit failure the whole design exists to catch.
    # NOTE: `due` is intentionally excluded — it is date-relative (a function of
    # "today", not of the event log), so a record stamped one day legitimately
    # reads differently the next. It's a cosmetic snapshot recomputed live
    # everywhere; only the date-invariant fields are true state worth validating.
    records = load_records(records_dir, events_path, today(args))
    for r in records:
        fm = r["fm"]
        recomputed = {
            "box": str(r["box"]), "streak": str(r["streak"]),
            "last_tested": r["last_tested"] or "never",
            "times_tested": str(r["times_tested"]),
        }
        for field, want in recomputed.items():
            if field in fm and fm[field] != want:
                problems += 1
                sys.stderr.write(
                    "praxis: {} derived '{}' drifted ({} stored, {} from log)\n".format(
                        r["path"], field, fm[field], want))

    # Orphaned events: ids in the log with no matching record file.
    known = {record_id_from_path(p) for p in record_files(records_dir)}
    seen = {norm_id(e.get("id")) for e in read_events(events_path)}
    for orphan in sorted(seen - known):
        problems += 1
        sys.stderr.write("praxis: event id {} has no record file\n".format(orphan))

    if problems:
        sys.stderr.write("praxis: {} problem(s). Run `praxis rebuild`.\n".format(problems))
        return 1
    print("OK: {} record(s) valid.".format(len(record_files(records_dir))))
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="praxis", description="State for the praxis skill.")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("due", help="print the review queue")
    d.add_argument("--count", action="store_true", help="print only the count")
    d.add_argument("--quiet", action="store_true", help="hook mode: silent unless due")
    d.add_argument("--date", help="reference date YYYY-MM-DD (testing)")
    d.set_defaults(func=cmd_due)

    r = sub.add_parser("record", help="record a recall result")
    r.add_argument("id")
    r.add_argument("--result", required=True, choices=("recalled", "forgotten"))
    r.add_argument("--date", help="event date YYYY-MM-DD (testing)")
    r.set_defaults(func=cmd_record)

    n = sub.add_parser("new", help="create a new learning record")
    n.add_argument("--title", required=True)
    n.add_argument("--deep", action="store_true", help="mark for mastery probing")
    n.add_argument("--date", help="created date YYYY-MM-DD (testing)")
    n.set_defaults(func=cmd_new)

    m = sub.add_parser("map", help="show the mastery map")
    m.add_argument("--date", help="reference date YYYY-MM-DD (testing)")
    m.set_defaults(func=cmd_map)

    rb = sub.add_parser("rebuild", help="recompute all frontmatter from events.jsonl")
    rb.add_argument("--date", help="reference date YYYY-MM-DD (testing)")
    rb.set_defaults(func=cmd_rebuild)

    lt = sub.add_parser("lint", help="validate record frontmatter")
    lt.set_defaults(func=cmd_lint)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
