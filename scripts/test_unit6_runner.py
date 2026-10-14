"""Unit 6 provenance/side-effect checks; no models are loaded or trained."""

import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np
import pandas as pd

from run_unit6 import (
    DEFAULTS, SEEDS, definitions_only, digest, install_evidence_wrappers,
    save_json, validate_phase,
)


class Unit6ReadinessTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "data").mkdir()
        self.evidence = self.root / "evidence/unit6"
        self.evidence.mkdir(parents=True)
        (self.root / "labels.csv").write_text("text,label,note\nExample,grounded,AI reviewed\n")
        (self.root / "criteria.md").write_text("Frozen criteria\n")
        (self.root / "takemeter.ipynb").write_text("{}\n")
        self.hashes = {f"{name}_sha256": digest(self.root / filename) for name, filename in (
            ("labels", "labels.csv"), ("criteria", "criteria.md"),
        )}
        save_json(self.root / "data/review_completed.json", {
            "completed": True, "review_mode": "instructor_ai_assisted", "reviewer": "Codex AI",
            "ai_labeled_reserved_count": 20, "ai_reviewed_draft_count": 180,
            "human_cold_count": 0, "human_reviewed_count": 0, **self.hashes,
        })
        save_json(self.root / "evidence/assignment-summary.json", {
            "status": "completed", "settings": DEFAULTS, **self.hashes,
        })
        save_json(self.evidence / "before-splits.json", {})
        save_json(self.evidence / "before-summary.json", {
            "status": "completed", "seeds": SEEDS, "settings": DEFAULTS,
            "source_notebook_sha256": digest(self.root / "takemeter.ipynb"),
            "splits_sha256": digest(self.evidence / "before-splits.json"), **self.hashes,
        })
        self.plan = {"change": "EPOCHS", "before": 3, "after": 8, "reason": "Fixture diagnosis", **self.hashes}
        self.git("init", "--quiet")
        self.commit()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True, text=True)

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Fixture preregistration")

    def write_plan(self, committed=True):
        save_json(self.evidence / "improvement_plan.json", self.plan)
        if committed:
            self.commit()

    def test_before_is_original_settings_and_disclosed_ai_scope(self):
        review, settings, before = validate_phase("before", None, self.root)
        self.assertEqual(settings, DEFAULTS)
        self.assertIsNone(before)
        self.assertFalse(review["human_review_completed"])
        with self.assertRaisesRegex(ValueError, "original three epochs"):
            validate_phase("before", 8, self.root)

    def test_after_requires_committed_epoch_plan(self):
        self.write_plan(committed=False)
        with self.assertRaisesRegex(ValueError, "Commit evidence/unit6/improvement_plan.json"):
            validate_phase("after", 8, self.root)
        self.commit()
        _, settings, _ = validate_phase("after", 8, self.root)
        self.assertEqual(settings, {**DEFAULTS, "EPOCHS": 8})
        with self.assertRaisesRegex(ValueError, "declared EPOCHS-only change"):
            validate_phase("after", 9, self.root)

    def test_after_rejects_altered_notebook_or_split_evidence(self):
        self.write_plan()
        for name, message in (("takemeter.ipynb", "same source notebook"), ("evidence/unit6/before-splits.json", "split evidence")):
            path = self.root / name
            original = path.read_bytes()
            path.write_text("changed")
            with self.assertRaisesRegex(ValueError, message):
                validate_phase("after", 8, self.root)
            path.write_bytes(original)

    def test_hashes_must_match_unit5_even_if_updated_review_matches(self):
        (self.root / "labels.csv").write_text("text,label,note\nChanged,grounded,AI reviewed\n")
        record_path = self.root / "data/review_completed.json"
        record = json.loads(record_path.read_text())
        record["labels_sha256"] = digest(self.root / "labels.csv")
        record_path.write_text(json.dumps(record))
        self.commit()
        with self.assertRaisesRegex(ValueError, "original Unit 5 labels_sha256"):
            validate_phase("before", None, self.root)


class Unit6ExecutionSafetyTests(unittest.TestCase):
    def test_definition_loader_never_runs_starter_side_effects(self):
        source = "import math\ndef f():\n    return math.sqrt(4)\nf()\nraise RuntimeError('training or writing happened')\n"
        namespace = {}
        exec(definitions_only(source), namespace)
        self.assertEqual(namespace["f"](), 2)
        self.assertNotIn("raise RuntimeError", definitions_only(source))

    def test_exclusive_evidence_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "evidence.json"
            save_json(path, {"original": True})
            with self.assertRaises(FileExistsError):
                save_json(path, {"replacement": True})
            self.assertEqual(json.loads(path.read_text()), {"original": True})

    def test_wrappers_capture_same_prediction_call_and_detect_changed_split(self):
        frame = pd.DataFrame({"text": ["A", "B"], "label": ["grounded", "request"], "note": ["", ""]})
        output = SimpleNamespace(predictions=np.array([[2., 1.], [0., 3.]]), label_ids=np.array([0, 1]))
        calls = []
        trainer = SimpleNamespace(predict=lambda data: calls.append(data) or output)
        original_predict = trainer.predict
        def evaluate(trainer, tokenizer, test_df, labels, seed=None):
            trainer.predict(test_df)
            return {"seed": seed, "accuracy": 1.0}
        def namespace():
            return {"df": frame, "split_dataset": lambda df, seed: (df, df, df), "evaluate": evaluate, "np": np}
        with tempfile.TemporaryDirectory() as temp:
            ns = namespace()
            splits, completed = install_evidence_wrappers(ns, "before", Path(temp), None)
            _, _, test = ns["split_dataset"](frame, 42)
            result = ns["evaluate"](trainer, None, test, ["grounded", "request"], seed=42)
            self.assertEqual(result["accuracy"], 1.0)
            self.assertEqual(len(calls), 1)
            self.assertIs(trainer.predict, original_predict)
            self.assertEqual(completed, [42])
            predictions = json.loads((Path(temp) / "before-predictions-42.json").read_text())
            self.assertEqual([row["prediction"] for row in predictions["rows"]], ["grounded", "request"])
            ns_after = namespace()
            install_evidence_wrappers(ns_after, "after", Path(temp), splits)
            ns_after["split_dataset"](frame, 42)
            ns_changed = namespace()
            ns_changed["split_dataset"] = lambda df, seed: (df.iloc[::-1], df, df)
            install_evidence_wrappers(ns_changed, "after", Path(temp), splits)
            with self.assertRaisesRegex(ValueError, "After split differs"):
                ns_changed["split_dataset"](frame, 42)


if __name__ == "__main__":
    unittest.main()
