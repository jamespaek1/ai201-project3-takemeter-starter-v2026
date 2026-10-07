"""Exercise the review/provenance gates without loading a model or training."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from run_notebook import run_scope, validate_assignment_ready


class ReviewReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        (self.root / "labels.csv").write_text("text,label,note\nExample,grounded,AI reviewed\n")
        (self.root / "criteria.md").write_text("Example preregistered criteria\n")
        self.git("init", "--quiet")
        self.git("add", "criteria.md", "labels.csv")
        self.git(
            "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Preregister fixture",
        )
        self.record = {
            "completed": True,
            "review_mode": "instructor_ai_assisted",
            "reviewer": "Codex AI",
            "ai_labeled_reserved_count": 20,
            "ai_reviewed_draft_count": 180,
            "human_cold_count": 0,
            "human_reviewed_count": 0,
        }
        for filename, key in (("labels.csv", "labels_sha256"), ("criteria.md", "criteria_sha256")):
            self.record[key] = hashlib.sha256((self.root / filename).read_bytes()).hexdigest()

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root, check=True, capture_output=True, text=True,
        ).stdout.strip()

    def validate(self, record=None):
        (self.root / "data/review_completed.json").write_text(json.dumps(record or self.record))
        return validate_assignment_ready(self.root / "labels.csv", self.root)

    def test_instructor_review_retains_ai_disclosure_and_preregistration(self):
        metadata = self.validate()
        self.assertEqual(metadata["preregistered_commit"], self.git("rev-parse", "HEAD"))
        self.assertEqual(metadata["review_mode"], "instructor_ai_assisted")
        self.assertEqual(metadata["reviewer"], "Codex AI")
        self.assertIs(metadata["human_review_completed"], False)
        self.assertEqual(metadata["ai_labeled_reserved_count"], 20)
        self.assertEqual(metadata["ai_reviewed_draft_count"], 180)
        scope = run_scope(False, metadata)
        self.assertIn("Instructor AI-assisted example", scope)
        self.assertIn("no human cold-labeling or human label review claimed", scope)
        self.assertNotIn("Personal assignment", scope)

    def test_counts_are_required_exact_integers(self):
        for key in ("ai_labeled_reserved_count", "ai_reviewed_draft_count", "human_cold_count", "human_reviewed_count"):
            for value in (None, "0", False, self.record[key] + 1):
                with self.subTest(key=key, value=value):
                    with self.assertRaisesRegex(ValueError, key):
                        self.validate({**self.record, key: value})

    def test_instructor_reviewer_is_disclosed(self):
        with self.assertRaisesRegex(ValueError, "reviewer as Codex AI"):
            self.validate({**self.record, "reviewer": "Student"})

    def test_instructor_record_cannot_also_claim_human_review(self):
        for key, value in (("human_review_completed", True), ("cold_count", 20), ("student_reviewed_ai_count", 180)):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "cannot claim"):
                    self.validate({**self.record, key: value})

    def test_unknown_mode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported review_mode"):
            self.validate({**self.record, "review_mode": "unreviewed"})

    def test_incomplete_review_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not marked completed"):
            self.validate({**self.record, "completed": False})

    def test_hash_mismatch_is_rejected_for_both_files(self):
        for key in ("labels_sha256", "criteria_sha256"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "no longer matches"):
                    self.validate({**self.record, key: "wrong"})

    def test_matching_review_does_not_bypass_commit_gate(self):
        path = self.root / "criteria.md"
        path.write_text("Changed criteria\n")
        self.record["criteria_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "Commit criteria.md and labels.csv"):
            self.validate()

    def test_original_student_worksheet_record_stays_supported(self):
        record = {
            key: self.record[key]
            for key in ("completed", "labels_sha256", "criteria_sha256")
        }
        record.update(cold_count=20, student_reviewed_ai_count=180)
        metadata = self.validate(record)
        self.assertEqual(metadata["review_mode"], "student_human_review")
        self.assertIs(metadata["human_review_completed"], True)
        self.assertIn("Student assignment run", run_scope(False, metadata))

    def test_practice_scope_needs_no_review(self):
        self.assertTrue(run_scope(True, {}).startswith("PRACTICE ONLY"))


if __name__ == "__main__":
    unittest.main()
