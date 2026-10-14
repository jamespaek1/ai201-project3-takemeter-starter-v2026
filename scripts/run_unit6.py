"""Run the starter's three-seed experiment without rewriting Unit 5 evidence.

Before: .venv/bin/python scripts/run_unit6.py --phase before
After:  .venv/bin/python scripts/run_unit6.py --phase after --epochs N

The after run requires a committed evidence/unit6/improvement_plan.json naming
EPOCHS as the single change and recording the original labels/criteria hashes.
No label judgments or criteria are changed; scores come from executed training.
"""

import argparse
import ast
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import traceback

from run_notebook import Tee, code_with_overrides, validate_assignment_ready, validate_label_values


ROOT = Path(__file__).resolve().parents[1]
SEEDS = [42, 7, 2024]
DEFAULTS = {
    "LABELS": ["request", "grounded", "ungrounded"],
    "BASE_MODEL": "distilbert-base-uncased",
    "EPOCHS": 3,
    "LEARNING_RATE": 2e-5,
    "BATCH_SIZE": 16,
    "MAX_LENGTH": 128,
    "SEED": 42,
}
PROTECTED = (
    "labels.csv", "criteria.md", "results.json", "test_split.csv",
    "takemeter.ipynb", "executed-notebook.ipynb",
    "data/review_completed.json", "evidence/assignment-summary.json",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    """Exclusive creation prevents accidentally replacing previous evidence."""
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def definitions_only(source):
    """Load starter imports/functions; omit its Unit 5 training/output calls."""
    tree = ast.parse(source)
    tree.body = [node for node in tree.body if isinstance(
        node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef)
    )]
    return "# Only starter imports and function definitions loaded for Unit 6.\n" + ast.unparse(tree) + "\n"


def require_committed(path, root):
    relative = str(path.relative_to(root))
    try:
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=root, check=True, capture_output=True, text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", relative],
            cwd=root, check=True, capture_output=True, text=True,
        ).stdout
        if status.strip():
            raise ValueError(f"Commit {relative} before running this experiment.")
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"Commit {relative} before running this experiment.") from exc


def validate_phase(phase, epochs, root=ROOT):
    review = validate_assignment_ready(root / "labels.csv", root)
    original = json.loads((root / "evidence/assignment-summary.json").read_text())
    if original.get("status") != "completed":
        raise ValueError("The original Unit 5 run must be completed.")
    for key in ("labels_sha256", "criteria_sha256"):
        if review[key] != original[key]:
            raise ValueError(f"Unit 6 must preserve the original Unit 5 {key}.")
    if original["settings"] != DEFAULTS:
        raise ValueError("The original Unit 5 settings differ from this runner's documented defaults.")
    settings = dict(DEFAULTS)
    evidence = root / "evidence/unit6"
    if phase == "before":
        if epochs not in (None, DEFAULTS["EPOCHS"]):
            raise ValueError("The before run must use the original three epochs.")
        return review, settings, None
    if phase != "after":
        raise ValueError(f"Unknown phase: {phase}")
    if type(epochs) is not int or epochs <= 0 or epochs == DEFAULTS["EPOCHS"]:
        raise ValueError("The after run needs a positive --epochs value different from three.")
    plan_path = evidence / "improvement_plan.json"
    if not plan_path.is_file():
        raise ValueError("Write and commit the diagnosed improvement_plan.json before the after run.")
    plan = json.loads(plan_path.read_text())
    if plan.get("change") != "EPOCHS" or plan.get("before") != 3 or plan.get("after") != epochs:
        raise ValueError("The after epoch count must exactly match the declared EPOCHS-only change.")
    if not isinstance(plan.get("reason"), str) or not plan["reason"].strip():
        raise ValueError("The improvement plan must explain the evidence-based reason.")
    for key in ("labels_sha256", "criteria_sha256"):
        if plan.get(key) != review[key]:
            raise ValueError(f"The improvement plan must preserve the original {key}.")
    require_committed(plan_path, root)
    before = json.loads((evidence / "before-summary.json").read_text())
    if before.get("status") != "completed" or before.get("seeds") != SEEDS:
        raise ValueError("Complete all three before seeds before the after run.")
    if before.get("settings") != DEFAULTS:
        raise ValueError("The before settings do not match the original Unit 5 settings.")
    if before.get("source_notebook_sha256") != digest(root / "takemeter.ipynb"):
        raise ValueError("Before and after must execute the same source notebook.")
    if before.get("splits_sha256") != digest(evidence / "before-splits.json"):
        raise ValueError("The before split evidence no longer matches its run summary.")
    for key in ("labels_sha256", "criteria_sha256"):
        if before.get(key) != review[key]:
            raise ValueError(f"Before and after must use the same {key}.")
    settings["EPOCHS"] = epochs
    return review, settings, before


def row_identity(text, row_number, gold):
    return {
        "row_id": f"row-{row_number:03d}",
        "csv_line": row_number + 1,
        "text_sha256": hashlib.sha256(str(text).encode()).hexdigest(),
        "gold": gold,
    }


def install_evidence_wrappers(namespace, phase, evidence_dir, before_splits):
    """Observe starter splits/predict outputs without changing training or scoring."""
    frame = namespace["df"]
    if frame["text"].duplicated().any():
        raise ValueError("Unique text is required for unambiguous split evidence.")
    row_lookup = {
        str(row["text"]): row_identity(row["text"], i + 1, row["label"])
        for i, row in frame.iterrows()
    }
    original_split = namespace["split_dataset"]
    original_evaluate = namespace["evaluate"]
    splits = {}
    completed_predictions = []

    def observed_split(df, seed, *args, **kwargs):
        if seed not in SEEDS or str(seed) in splits:
            raise ValueError(f"Unexpected or duplicate seed: {seed}")
        frames = original_split(df, seed, *args, **kwargs)
        record = {}
        for name, part in zip(("train", "val", "test"), frames):
            rows = [row_lookup[str(text)] for text in part["text"]]
            record[name] = {
                "n_rows": len(rows), "rows": rows,
                "membership_sha256": hashlib.sha256(
                    json.dumps(rows, sort_keys=True).encode()
                ).hexdigest(),
            }
        if before_splits is not None and before_splits.get(str(seed)) != record:
            raise ValueError(f"After split differs from the recorded before split for seed {seed}.")
        splits[str(seed)] = record
        return frames

    def observed_evaluate(trainer, tokenizer, test_df, labels, seed=None):
        captured = []
        original_predict = trainer.predict

        def observed_predict(*args, **kwargs):
            output = original_predict(*args, **kwargs)
            captured.append(output)
            return output

        trainer.predict = observed_predict
        try:
            result = original_evaluate(trainer, tokenizer, test_df, labels, seed=seed)
        finally:
            trainer.predict = original_predict
        if len(captured) != 1:
            raise RuntimeError("Expected exactly one starter predict call per seed.")
        np = namespace["np"]
        logits = captured[0].predictions
        exp = np.exp(logits - logits.max(axis=-1, keepdims=True))
        probabilities = exp / exp.sum(axis=-1, keepdims=True)
        predicted = np.argmax(logits, axis=-1)
        rows = []
        for i, (_, row) in enumerate(test_df.iterrows()):
            identity = row_lookup[str(row["text"])]
            match = re.search(r"source=(https?://[^;\s]+)", str(row.get("note", "")))
            rows.append({
                **identity, "text": row["text"],
                "source_url": match.group(1) if match else None,
                "prediction": labels[int(predicted[i])],
                "correct": bool(row["label"] == labels[int(predicted[i])]),
                "confidence": float(probabilities[i].max()),
                "probabilities": {label: float(probabilities[i, j]) for j, label in enumerate(labels)},
            })
        save_json(evidence_dir / f"{phase}-predictions-{seed}.json", {
            "seed": seed, "labels": labels, "rows": rows,
            "method": "Observed the starter evaluate() call's existing Trainer.predict output; no extra predictions.",
        })
        completed_predictions.append(seed)
        return result

    namespace["split_dataset"] = observed_split
    namespace["evaluate"] = observed_evaluate
    return splits, completed_predictions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=("before", "after"))
    parser.add_argument("--epochs", type=int)
    args = parser.parse_args()
    try:
        review, settings, before = validate_phase(args.phase, args.epochs)
        validate_label_values(ROOT / "labels.csv", settings["LABELS"])
        protected = {name: digest(ROOT / name) for name in PROTECTED}
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    phase = args.phase
    evidence_dir = ROOT / "evidence/unit6"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    targets = [
        evidence_dir / f"{phase}-{suffix}"
        for suffix in ("run.log", "summary.json", "executed.ipynb", "splits.json")
    ] + [evidence_dir / f"{phase}-predictions-{seed}.json" for seed in SEEDS]
    result_path = ROOT / f"results_three_seeds_{phase}.json"
    model_dir = ROOT / "models/unit6_after"
    for path in [*targets, result_path] + ([model_dir] if phase == "after" else []):
        if path.exists():
            parser.error(f"Preserve existing evidence before running again: {path}")
    before_splits = None
    if before is not None:
        before_splits = json.loads((evidence_dir / "before-splits.json").read_text())
    os.environ.setdefault("HF_HOME", str(ROOT / ".cache/huggingface"))
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    notebook_bytes = (ROOT / "takemeter.ipynb").read_bytes()
    notebook = json.loads(notebook_bytes)
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell["execution_count"], cell["outputs"] = None, []
    metadata = {
        "scope": "Unit 6 instructor AI-assisted example; labels/criteria retain the disclosed Unit 5 AI annotation provenance, with no human review claimed.",
        "phase": phase, "status": "running", "seeds": SEEDS,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(),
        "package_versions": {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "datasets", "accelerate", "numpy", "pandas", "scikit-learn")
        },
        "settings": settings, "protected_unit5_hashes": protected,
        "runner_sha256": digest(Path(__file__)),
        "source_notebook_sha256": hashlib.sha256(notebook_bytes).hexdigest(),
        "executed_cell_indices": [], "definitions_only_cell_indices": [12, 14, 16],
        "command": sys.argv, **review,
    }
    if phase == "after":
        metadata["improvement_plan_sha256"] = digest(evidence_dir / "improvement_plan.json")
    notebook["metadata"]["unit6_runner"] = {
        "runner": "scripts/run_unit6.py", "sha256": metadata["runner_sha256"],
        "instrumentation": "Runner wrappers only record splits and existing predict output; training/evaluate algorithm is the starter's unchanged code.",
    }
    started = time.monotonic()
    namespace = {"__name__": "__main__"}
    splits, predictions = {}, []
    exit_code = 0
    os.chdir(ROOT)
    with targets[0].open("x", encoding="utf-8") as log:
        with redirect_stdout(Tee(sys.stdout, log)), redirect_stderr(Tee(sys.stderr, log)):
            print(json.dumps(metadata, indent=2))
            try:
                for count, index in enumerate((2, 4, 6, 8, 10, 12, 14, 16, 19, 21, 23), 1):
                    cell = notebook["cells"][index]
                    source = "".join(cell["source"])
                    if index in (12, 14, 16):
                        source = definitions_only(source)
                    overrides = settings if index == 6 else ({"RUN_LABEL": phase, "SEEDS": SEEDS} if index == 19 else {})
                    executable, source = code_with_overrides(source, overrides, f"takemeter.ipynb cell {index}")
                    if index == 19:
                        splits, predictions = install_evidence_wrappers(namespace, phase, evidence_dir, before_splits)
                    cell["source"] = source.splitlines(keepends=True)
                    captured = io.StringIO()
                    print(f"\n--- Executing Unit 6 notebook cell {index} ---")
                    with redirect_stdout(Tee(sys.stdout, captured)), redirect_stderr(Tee(sys.stderr, captured)):
                        exec(executable, namespace)
                    cell["execution_count"] = count
                    cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": captured.getvalue().splitlines(keepends=True)}]
                    metadata["executed_cell_indices"].append(index)
                    if index == 2:
                        metadata.update(device=namespace["DEVICE"], device_name=namespace["DEVICE_NAME"])
                        if before is not None and metadata["device"] != before["device"]:
                            raise ValueError("Before and after must run on the same device backend.")
                    if index == 10 and namespace["problems"]:
                        raise ValueError(f"Dataset validation failed: {namespace['problems']}")
                if predictions != SEEDS:
                    raise RuntimeError("Not all three seeds produced prediction evidence.")
                if phase == "after":
                    namespace["t"].save_model(str(model_dir))
                    namespace["tok"].save_pretrained(str(model_dir))
                    metadata["saved_final_seed_model"] = str(model_dir.relative_to(ROOT))
                metadata["results"] = namespace["all_results"]
                metadata["results_sha256"] = digest(result_path)
                metadata["status"] = "completed"
            except BaseException as exc:
                metadata.update(status="failed", error=f"{type(exc).__name__}: {exc}")
                traceback.print_exc()
                exit_code = 1
            finally:
                changed = [name for name, value in protected.items() if not (ROOT / name).is_file() or digest(ROOT / name) != value]
                metadata["unit5_files_unchanged"] = not changed
                if changed:
                    metadata.update(status="failed", preservation_error=f"Unit 5 files changed: {changed}")
                    exit_code = 1
                metadata["completed_prediction_seeds"] = predictions
                metadata["elapsed_seconds"] = round(time.monotonic() - started, 3)
                metadata["finished_utc"] = datetime.now(timezone.utc).isoformat()
                split_path = evidence_dir / f"{phase}-splits.json"
                save_json(split_path, splits)
                metadata["splits_sha256"] = digest(split_path)
                save_json(evidence_dir / f"{phase}-summary.json", metadata)
                save_json(evidence_dir / f"{phase}-executed.ipynb", notebook)
                print(f"\nUnit 6 {phase}: {metadata['status']}; Unit 5 evidence unchanged: {not changed}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
