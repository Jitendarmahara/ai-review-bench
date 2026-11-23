import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark import db, coverage, report, grade
from benchmark.config import conditions_for, all_cells


class HarnessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.path = self.tmp.name
        db.init(self.path)
        self.conn = db.connect(self.path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.path)

    def test_schema_tables_exist(self):
        names = {r["name"] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"providers", "runs", "reviews", "findings", "scores",
                         "answer_key"} <= names)

    def test_config_cells(self):
        self.assertEqual(len(list(all_cells())), 11)
        self.assertEqual(conditions_for("01"), ("code_only",))
        self.assertEqual(conditions_for("04"), ("code_only", "with_snapshot"))

    def test_run_ids_are_stable_and_sequential(self):
        db.add_provider(self.conn, "coderabbit", "github_bot", "coderabbitai[bot]")
        r1 = db.create_run(self.conn, "coderabbit", "03", "code_only", repo="o/r", pr_number=1)
        r2 = db.create_run(self.conn, "coderabbit", "03", "code_only", repo="o/r",
                           pr_number=2, is_retry=1)
        self.assertEqual(r1, "coderabbit-03-code_only-1")
        self.assertEqual(r2, "coderabbit-03-code_only-2")

    def test_capture_sets_completed(self):
        db.add_provider(self.conn, "proofline", "github_bot", "proofline[bot]")
        rid = db.create_run(self.conn, "proofline", "01", "code_only", repo="o/r", pr_number=9)
        self.assertEqual(db.get_run(self.conn, rid)["outcome"], "pending")
        db.save_review(self.conn, rid, "Looks correct; no issues.", "http://x/1")
        self.assertEqual(db.get_run(self.conn, rid)["outcome"], "completed")

    def test_outcome_validation(self):
        db.add_provider(self.conn, "greptile", "github_bot", "greptile[bot]")
        rid = db.create_run(self.conn, "greptile", "01", "code_only", repo="o/r", pr_number=1)
        with self.assertRaises(ValueError):
            db.set_outcome(self.conn, rid, "banana")
        db.set_outcome(self.conn, rid, "quota_stop")
        self.assertEqual(db.get_run(self.conn, rid)["outcome"], "quota_stop")

    def test_bucket_validation(self):
        db.add_provider(self.conn, "cr", "github_bot", "cr[bot]")
        rid = db.create_run(self.conn, "cr", "03", "code_only", repo="o/r", pr_number=1)
        fid = db.add_finding(self.conn, rid, "drops final partial batch")
        with self.assertRaises(ValueError):
            db.score_finding(self.conn, fid, "not_a_bucket", "x")
        db.score_finding(self.conn, fid, "correct_bug", "matches key")
        self.assertEqual(
            self.conn.execute("SELECT bucket FROM scores WHERE finding_id=?", (fid,)).fetchone()["bucket"],
            "correct_bug")

    def test_blind_grade_roundtrip_hides_provider(self):
        db.add_provider(self.conn, "cr", "github_bot", "cr[bot]")
        db.freeze_key(self.conn, "03", "code_only", 0, "drops final partial batch")
        rid = db.create_run(self.conn, "cr", "03", "code_only", repo="o/r", pr_number=1)
        db.save_review(self.conn, rid, "partial batch dropped")
        db.add_finding(self.conn, rid, "final partial batch never delivered")
        gfile = self.path + ".grade.json"
        self.assertEqual(grade.export(self.conn, gfile), 1)
        with open(gfile) as fh:
            payload = json.load(fh)
        self.assertNotIn("cr", json.dumps(payload["items"]))
        self.assertIn("expected", payload["items"][0])
        self.assertEqual(payload["items"][0]["change_is_safe"], 0)
        payload["items"][0]["bucket"] = "correct_bug"
        payload["items"][0]["reason"] = "matches frozen defect"
        with open(gfile, "w") as fh:
            json.dump(payload, fh)
        self.assertEqual(grade.import_(self.conn, gfile), 1)
        self.assertEqual(len(db.ungraded_findings(self.conn)), 0)
        os.unlink(gfile)

    def test_missed_defect_detection(self):
        db.add_provider(self.conn, "q", "github_bot", "q[bot]")
        db.freeze_key(self.conn, "03", "code_only", 0, "drops final partial batch")
        rid = db.create_run(self.conn, "q", "03", "code_only", repo="o/r", pr_number=1)
        db.save_review(self.conn, rid, "LGTM")
        missed = report.missed_defects(self.conn)
        self.assertIn("q", missed)
        self.assertIn("03/code_only", missed["q"])

    def test_quiet_review_on_safe_change_is_not_missed(self):
        db.add_provider(self.conn, "q", "github_bot", "q[bot]")
        db.freeze_key(self.conn, "01", "code_only", 1, "pagination correct")
        rid = db.create_run(self.conn, "q", "01", "code_only", repo="o/r", pr_number=1)
        db.save_review(self.conn, rid, "No issues.")
        self.assertNotIn("q", report.missed_defects(self.conn))

    def test_coverage_and_report_render(self):
        for p in ("proofline", "coderabbit"):
            db.add_provider(self.conn, p, "github_bot", f"{p}[bot]")
        rid = db.create_run(self.conn, "proofline", "04", "with_snapshot", repo="o/r", pr_number=1)
        db.save_review(self.conn, rid, "column still read by site B")
        cov = coverage.render(self.conn)
        self.assertIn("Condition: code_only", cov)
        self.assertIn("Condition: with_snapshot", cov)
        self.assertIn("proofline", cov)
        rep = report.render(self.conn)
        self.assertIn("Coverage", rep)
        self.assertIn("Scored findings", rep)


if __name__ == "__main__":
    unittest.main()
