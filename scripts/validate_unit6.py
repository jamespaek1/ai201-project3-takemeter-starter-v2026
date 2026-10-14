"""Cross-check saved Unit 6 evidence without loading models or changing inputs.

Run after both phases: .venv/bin/python scripts/validate_unit6.py
The only file written is evidence/unit6/validation.json.
"""

from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from run_unit6 import DEFAULTS, PROTECTED, SEEDS, digest, row_identity


ROOT = Path(__file__).resolve().parents[1]
LABELS = DEFAULTS["LABELS"]
STAFF_LABELS = {"analysis", "hot_take", "reaction"}


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def check(condition, message):
    if not condition:
        raise ValueError(message)


def same_metrics(actual, expected, context):
    """Compare only recomputed fields; retain notebook float32 tolerance."""
    if isinstance(expected, dict):
        check(isinstance(actual, dict), f"{context}: expected an object")
        for key, value in expected.items():
            check(key in actual, f"{context}: missing {key}")
            same_metrics(actual[key], value, f"{context}.{key}")
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        check(isinstance(actual, (int, float)) and math.isfinite(actual)
              and math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-7),
              f"{context}: {actual!r} differs from recomputed {expected!r}")
    else:
        check(actual == expected, f"{context}: {actual!r} differs from {expected!r}")


def recompute(rows, predicted_key="prediction", with_confidence=True):
    check(len(rows) == 30, "Every held-out evaluation must have exactly 30 posts")
    gold = [row["gold"] for row in rows]
    predicted = [row[predicted_key] for row in rows]
    check(set(gold) <= set(LABELS) and set(predicted) <= set(LABELS), "Invalid prediction/gold labels")
    matrix = {g: {p: 0 for p in LABELS} for g in LABELS}
    for g, p in zip(gold, predicted):
        matrix[g][p] += 1
    per_label = {}
    for label in LABELS:
        tp = matrix[label][label]
        support = sum(matrix[label].values())
        guessed = sum(matrix[g][label] for g in LABELS)
        precision, recall = (tp / guessed if guessed else 0.0), (tp / support if support else 0.0)
        per_label[label] = {
            "precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "support": support,
        }
    right = np.array([g == p for g, p in zip(gold, predicted)])
    result = {
        "accuracy": float(right.mean()),
        "f1_macro": sum(value["f1"] for value in per_label.values()) / len(LABELS),
        "per_label": per_label,
    }
    if with_confidence:
        confidence = np.asarray([row["confidence"] for row in rows], dtype=np.float32)
        check(bool(np.isfinite(confidence).all()), "Non-finite confidence")
        ranked = np.argsort(confidence)
        third = max(1, len(rows) // 3)
        result.update(n_test=len(rows), confusion=matrix, confidence={
            "mean_when_right": float(confidence[right].mean()) if right.any() else None,
            "mean_when_wrong": float(confidence[~right].mean()) if (~right).any() else None,
            "accuracy_most_confident_third": float(right[ranked[-third:]].mean()),
            "accuracy_least_confident_third": float(right[ranked[:third]].mean()),
            "n_per_third": third,
        })
    else:
        result["n"] = len(rows)
    return result


def verdict(condition):
    return "pass" if condition else "fail"


def criterion_verdicts(metrics, balance, agreement):
    confidence = metrics["confidence"]
    gap = confidence["accuracy_most_confident_third"] - confidence["accuracy_least_confident_third"]
    return {
        "1": {"verdict": verdict(metrics["accuracy"] >= 0.70), "accuracy": metrics["accuracy"], "target": 0.70},
        "2": {"verdict": verdict(all(v["f1"] >= 0.60 for v in metrics["per_label"].values())), "f1": {k: v["f1"] for k, v in metrics["per_label"].items()}, "target_each": 0.60},
        "3": balance,
        "4": agreement,
        "5": {"verdict": verdict(gap >= 0.15 - 1e-9), "accuracy_gap": gap, "target": 0.15, "n_per_third": confidence["n_per_third"]},
    }


def validate_staff(root):
    posts = read_csv(root / "data/staff_posts.csv")
    mine = read_csv(root / "my_staff_labels.csv")
    check(len(posts) == len(mine) == 30, "Staff exercise must contain exactly 30 posts")
    check(Counter(r["text"] for r in posts) == Counter(r["text"] for r in mine), "Staff labeling texts changed or are missing/duplicated")
    check(len({r["text"] for r in mine}) == 30, "Duplicate staff labeling text")
    check(all(r["label"] in STAFF_LABELS for r in mine), "Invalid staff-taxonomy label")
    key_path, result_path = root / "data/staff_labels.csv", root / "agreement_results.json"
    if not key_path.exists() or not result_path.exists():
        return {
            "verdict": "pending", "target": "24/30 before adjudication",
            "reason": "Official staff key and computed agreement results are both required; no agreement value inferred.",
            "official_key_present": key_path.exists(), "agreement_results_present": result_path.exists(),
        }
    key = read_csv(key_path)
    columns = ("label", "staff_label", "my_label", "your_label")
    label_key = next((column for column in columns if key and column in key[0]), None)
    check(label_key is not None, "Staff key has no label column")
    check(len(key) == 30 and {r["id"] for r in key} == {r["id"] for r in posts}, "Staff key IDs must match all 30 posts exactly")
    check(all(r[label_key] in STAFF_LABELS for r in key), "Invalid reference staff label")
    by_id = {r["id"]: r[label_key] for r in key}
    by_text = {r["text"]: r["label"] for r in mine}
    disagreements = [{"text": r["text"], "staff": by_id[r["id"]], "mine": by_text[r["text"]]}
                     for r in posts if by_id[r["id"]] != by_text[r["text"]]]
    agreed = 30 - len(disagreements)
    actual = json.loads(result_path.read_text())
    same_metrics(actual, {"compared": 30, "agreed": agreed, "agreement_rate": agreed / 30,
                          "staff_posts_not_in_mine": 0, "disagreements": disagreements}, "agreement_results")
    return {"verdict": verdict(agreed >= 24), "agreed": agreed, "compared": 30,
            "agreement_rate": agreed / 30, "target": "24/30 before adjudication",
            "staff_key_sha256": digest(key_path), "method": "AI-assisted annotation; not a human consistency claim"}


def validate(root=ROOT):
    evidence = root / "evidence/unit6"
    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(), "status": "checking", "errors": [],
        "notes": ["csv_line in prediction/split evidence means logical CSV record number including the header, not a physical text line.",
                  "Metric checks use saved predictions only; no models are loaded or rerun.",
                  "Confidence thirds use np.argsort on float32 confidences, matching the notebook; numerical tolerance is 1e-7 absolute / 1e-6 relative."],
    }
    try:
        labels = read_csv(root / "labels.csv")
        check(len(labels) == 200 and len({r["text"] for r in labels}) == 200, "Expected 200 unique labeled texts")
        check(all(r["label"] in LABELS for r in labels), "Dataset label outside original taxonomy")
        lookup = {f"row-{i + 1:03d}": row for i, row in enumerate(labels)}
        counts = Counter(r["label"] for r in labels)
        shares = {label: counts[label] / len(labels) for label in LABELS}
        balance = {"verdict": verdict(all(0.20 <= share <= 0.60 for share in shares.values())), "counts": dict(counts), "shares": shares, "target": "20%-60% for every label"}
        agreement = validate_staff(root)
        report["agreement"] = agreement
        original = json.loads((root / "evidence/assignment-summary.json").read_text())
        for filename, key in (("labels.csv", "labels_sha256"), ("criteria.md", "criteria_sha256"), ("takemeter.ipynb", "notebook_sha256")):
            check(digest(root / filename) == original[key], f"Original Unit 5 {filename} changed")
        check(json.loads((root / "results.json").read_text()) == original["results"], "Original Unit 5 results.json changed")
        heldout = read_csv(root / "test_split.csv")
        check(len(heldout) == 30, "Original held-out split must have 30 rows")
        heldout_pairs = [(r["text"], r["label"]) for r in heldout]
        report["baselines"] = {}
        for filename, definitions in (("baseline_results.json", True), ("baseline_bare_names_results.json", False)):
            baseline = json.loads((root / filename).read_text())
            check(baseline["n"] == 30 and baseline["seed"] == 42 and baseline["held_out"] is True, f"{filename}: must use the original 30 held-out posts")
            check(baseline["used_definitions"] is definitions, f"{filename}: definition condition incorrect")
            check([(r["text"], r["gold"]) for r in baseline["predictions"]] == heldout_pairs, f"{filename}: original held-out texts/golds differ")
            metrics = recompute(baseline["predictions"], "predicted", False)
            same_metrics(baseline["scores"], metrics, filename)
            report["baselines"][filename] = {"sha256": digest(root / filename), "recomputed_scores": metrics}
        plan = json.loads((evidence / "improvement_plan.json").read_text())
        check(plan["change"] == "EPOCHS" and plan["before"] == 3 and plan["after"] != 3, "Expected one declared EPOCHS change")
        for key in ("labels_sha256", "criteria_sha256"):
            check(plan[key] == original[key], f"Plan changed original {key}")
        phase_splits, phase_summaries = {}, {}
        report["phases"] = {}
        for phase in ("before", "after"):
            summary = json.loads((evidence / f"{phase}-summary.json").read_text())
            phase_summaries[phase] = summary
            check(summary["status"] == "completed" and summary["seeds"] == SEEDS, f"{phase}: all three seeds must be completed")
            check(summary["completed_prediction_seeds"] == SEEDS, f"{phase}: missing seed prediction evidence")
            check(summary["human_review_completed"] is False and summary["review_mode"] == "instructor_ai_assisted", f"{phase}: inaccurate annotation provenance")
            expected_settings = {**DEFAULTS, "EPOCHS": plan[phase]}
            check(summary["settings"] == expected_settings, f"{phase}: settings do not match the single declared change")
            check(summary["source_notebook_sha256"] == original["notebook_sha256"], f"{phase}: source notebook changed")
            check(set(summary["protected_unit5_hashes"]) == set(PROTECTED), f"{phase}: incomplete Unit 5 preservation inventory")
            check(summary["unit5_files_unchanged"] is True, f"{phase}: Unit 5 preservation failed")
            for filename, value in summary["protected_unit5_hashes"].items():
                check(digest(root / filename) == value, f"{phase}: protected file changed: {filename}")
            split_path = evidence / f"{phase}-splits.json"
            check(digest(split_path) == summary["splits_sha256"], f"{phase}: split artifact hash mismatch")
            splits = json.loads(split_path.read_text())
            phase_splits[phase] = splits
            check(list(splits) == [str(seed) for seed in SEEDS], f"{phase}: incorrect seed splits")
            result_path = root / f"results_three_seeds_{phase}.json"
            results = json.loads(result_path.read_text())
            check(digest(result_path) == summary["results_sha256"] and results == summary["results"], f"{phase}: saved result mismatch")
            check([r["seed"] for r in results] == SEEDS, f"{phase}: result seed order mismatch")
            per_seed = {}
            for result in results:
                seed = result["seed"]
                split = splits[str(seed)]
                id_sets = []
                for name in ("train", "val", "test"):
                    part = split[name]
                    rows = part["rows"]
                    ids = [r["row_id"] for r in rows]
                    check(part["n_rows"] == len(rows) == len(set(ids)), f"{phase}/{seed}/{name}: duplicate IDs/count mismatch")
                    check(part["membership_sha256"] == hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(), f"{phase}/{seed}/{name}: membership hash mismatch")
                    for row in rows:
                        item = lookup[row["row_id"]]
                        number = int(row["row_id"].removeprefix("row-"))
                        check(row == row_identity(item["text"], number, item["label"]), f"{phase}/{seed}/{name}: changed dataset row identity")
                    id_sets.append(set(ids))
                check(not (id_sets[0] & id_sets[1] or id_sets[0] & id_sets[2] or id_sets[1] & id_sets[2]), f"{phase}/{seed}: split leakage")
                check(set.union(*id_sets) == set(lookup) and len(id_sets[2]) == 30, f"{phase}/{seed}: splits do not partition all 200 rows with 30 test posts")
                prediction = json.loads((evidence / f"{phase}-predictions-{seed}.json").read_text())
                rows = prediction["rows"]
                check(prediction["seed"] == seed and prediction["labels"] == LABELS, f"{phase}/{seed}: prediction metadata mismatch")
                check([r["row_id"] for r in rows] == [r["row_id"] for r in split["test"]["rows"]], f"{phase}/{seed}: predictions differ from test split")
                for row in rows:
                    source = lookup[row["row_id"]]
                    check((row["text"], row["gold"]) == (source["text"], source["label"]), f"{phase}/{seed}: changed prediction text/gold")
                    probabilities = [row["probabilities"][label] for label in LABELS]
                    check(all(math.isfinite(p) and 0 <= p <= 1 for p in probabilities) and abs(sum(probabilities) - 1) < 1e-6, f"{phase}/{seed}: invalid probabilities")
                    check(row["prediction"] == LABELS[int(np.argmax(probabilities))], f"{phase}/{seed}: prediction differs from highest probability")
                    check(row["correct"] is (row["gold"] == row["prediction"]), f"{phase}/{seed}: incorrect correctness flag")
                    same_metrics(row["confidence"], max(probabilities), f"{phase}/{seed} confidence")
                if seed == 42:
                    check([(r["text"], r["gold"]) for r in rows] == heldout_pairs, f"{phase}: seed 42 differs from original test_split.csv")
                metrics = recompute(rows)
                same_metrics(result, metrics, f"{phase}/{seed}")
                per_seed[str(seed)] = {"recomputed_metrics": metrics, "criteria": criterion_verdicts(metrics, balance, agreement)}
            all_seeds = {}
            for number in ("1", "2", "3", "4", "5"):
                values = [per_seed[str(seed)]["criteria"][number]["verdict"] for seed in SEEDS]
                all_seeds[number] = "fail" if "fail" in values else ("pending" if "pending" in values else "pass")
            report["phases"][phase] = {"per_seed": per_seed, "criteria_all_seeds": all_seeds}
        check(phase_splits["before"] == phase_splits["after"], "Before and after splits differ")
        check(phase_summaries["before"]["device"] == phase_summaries["after"]["device"], "Before and after device backends differ")
        check(phase_summaries["before"]["protected_unit5_hashes"] == phase_summaries["after"]["protected_unit5_hashes"], "Unit 5 files changed between phases")
        check(phase_summaries["after"]["improvement_plan_sha256"] == digest(evidence / "improvement_plan.json"), "Improvement plan changed after the run")
        report["status"] = "passed_with_pending_agreement" if agreement["verdict"] == "pending" else "passed"
        report["unit5_files_unchanged"] = True
        report["same_before_after_splits"] = True
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        report["status"] = "failed"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    return report


def main():
    report = validate()
    path = ROOT / "evidence/unit6/validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "errors": report["errors"], "output": str(path)}, indent=2))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
