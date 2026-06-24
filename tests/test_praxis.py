"""Tests for praxis.py — the deterministic state engine.

Stdlib unittest, no deps. Each test runs in an isolated temp workspace.
Covers the things that silently corrupt state if wrong: Leitner promote/reset,
box cap, due-ordering, the seq tiebreaker (ordering survives a reordered log),
rebuild idempotence, lint drift-catch, id normalization, and the hook's silence.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "praxis")
sys.path.insert(0, SKILL_DIR)

import praxis  # noqa: E402


def run(*argv):
    """Invoke the CLI, swallow stdout, return the exit code."""
    with contextlib.redirect_stdout(io.StringIO()):
        return praxis.main(list(argv))


def capture(*argv):
    """Invoke the CLI, return (exit_code, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = praxis.main(list(argv))
    return code, buf.getvalue()


def read_text(path):
    with open(path) as f:
        return f.read()


def write_text(path, text):
    with open(path, "w") as f:
        f.write(text)


class PraxisTest(unittest.TestCase):
    def setUp(self):
        self.old = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="praxis-test-")
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.old)
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- helpers --------------------------------------------------------
    def records_dir(self):
        return os.path.join(self.tmp, "learning-records")

    def events_path(self):
        return os.path.join(self.records_dir(), "events.jsonl")

    def state(self, rid="0001", ref="2026-07-01"):
        recs = praxis.load_records(self.records_dir(), self.events_path(), ref)
        return next(r for r in recs if r["id"] == rid)

    # -- tests ----------------------------------------------------------
    def test_promote_then_reset(self):
        run("new", "--title", "t", "--date", "2026-06-20")
        run("record", "1", "--result", "recalled", "--date", "2026-06-20")
        self.assertEqual(self.state()["box"], 2)
        run("record", "1", "--result", "recalled", "--date", "2026-06-21")
        s = self.state()
        self.assertEqual(s["box"], 3)
        self.assertEqual(s["streak"], 2)
        run("record", "1", "--result", "forgotten", "--date", "2026-06-22")
        s = self.state()
        self.assertEqual(s["box"], 1, "forgotten must reset to box 1")
        self.assertEqual(s["streak"], 0, "forgotten must reset streak")

    def test_box_caps_at_five(self):
        run("new", "--title", "t", "--date", "2026-06-20")
        for i in range(8):
            run("record", "1", "--result", "recalled", "--date", "2026-07-%02d" % (i + 1))
        self.assertEqual(self.state()["box"], praxis.MAX_BOX)

    def test_seq_tiebreaker_survives_reorder(self):
        # Two same-date events; forgotten is last → box1/streak0.
        run("new", "--title", "t", "--date", "2026-06-23")
        run("record", "1", "--result", "recalled", "--date", "2026-06-23")
        run("record", "1", "--result", "forgotten", "--date", "2026-06-23")
        self.assertEqual(self.state()["box"], 1)
        # Reverse the event lines and rebuild; seq must preserve order.
        lines = read_text(self.events_path()).splitlines()
        write_text(self.events_path(), "\n".join(reversed(lines)) + "\n")
        run("rebuild", "--date", "2026-06-23")
        s = self.state()
        self.assertEqual(s["box"], 1, "seq must keep forgotten last after reorder")
        self.assertEqual(s["streak"], 0)

    def test_due_ordering(self):
        # 0001 forgotten, 0002 never tested, 0003 recalled long ago.
        run("new", "--title", "forgot", "--date", "2026-06-01")
        run("new", "--title", "never", "--date", "2026-06-01")
        run("new", "--title", "old", "--date", "2026-06-01")
        run("record", "3", "--result", "recalled", "--date", "2026-06-02")
        run("record", "1", "--result", "forgotten", "--date", "2026-06-10")
        recs = praxis.load_records(self.records_dir(), self.events_path(), "2026-07-01")
        queue = praxis.review_queue(recs)
        order = [r["id"] for r in queue]
        self.assertEqual(order[0], "0001", "forgotten first")
        self.assertEqual(order[1], "0002", "never-tested second")
        self.assertEqual(order[2], "0003", "longest-untested last")

    def test_rebuild_is_idempotent(self):
        run("new", "--title", "t", "--date", "2026-06-20")
        run("record", "1", "--result", "recalled", "--date", "2026-06-20")
        run("rebuild", "--date", "2026-06-21")
        path = praxis.record_files(self.records_dir())[0]
        first = read_text(path)
        run("rebuild", "--date", "2026-06-21")
        self.assertEqual(first, read_text(path), "rebuild must be idempotent")

    def test_lint_catches_derived_drift(self):
        run("new", "--title", "t", "--date", "2026-06-20")
        run("record", "1", "--result", "recalled", "--date", "2026-06-20")
        path = praxis.record_files(self.records_dir())[0]
        write_text(path, read_text(path).replace("box: 2", "box: 99"))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(run("lint"), 1, "lint must fail on drifted derived block")
        run("rebuild", "--date", "2026-06-20")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(run("lint"), 0, "rebuild must repair drift")

    def test_unpadded_handappended_id_matches(self):
        run("new", "--title", "t", "--date", "2026-06-20")
        run("record", "1", "--result", "recalled", "--date", "2026-06-20")
        with open(self.events_path(), "a") as f:
            f.write(json.dumps({"date": "2026-06-21", "id": "1", "result": "recalled"}) + "\n")
        run("rebuild", "--date", "2026-06-22")
        self.assertEqual(self.state()["times_tested"], 2,
                         "hand-appended unpadded id '1' must count toward 0001")

    def test_hook_quiet_is_silent(self):
        # No workspace: silent.
        code, out = capture("due", "--quiet", "--count")
        self.assertEqual(out, "")
        # Workspace, nothing due (just recalled today → box2, not due same day): silent.
        run("new", "--title", "t", "--date", "2026-06-23")
        run("record", "1", "--result", "recalled", "--date", "2026-06-23")
        code, out = capture("due", "--quiet", "--count", "--date", "2026-06-23")
        self.assertEqual(out, "", "hook must stay silent when nothing is due")
        # Later, due → prints the count.
        code, out = capture("due", "--quiet", "--count", "--date", "2026-06-30")
        self.assertEqual(out.strip(), "1")

    def test_record_unknown_id_fails(self):
        run("new", "--title", "t", "--date", "2026-06-20")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(run("record", "0099", "--result", "recalled"), 1)


if __name__ == "__main__":
    unittest.main()
