"""Execute only Unit 5 notebook sections 1-5, with an auditable local log.

Practice: .venv/bin/python scripts/run_notebook.py --practice

For a future assignment run, first finish the personally authored criteria
and required cold-labeling exercise. Then supply --csv labels.csv --labels
followed by the actual label names. No criteria or labels are generated here.
Practice results stay under .cache/practice-run; they are never the project's
root results.json or test_split.csv.
"""

import argparse
import ast
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]
CELLS = (2, 4, 6, 8, 10, 12, 14, 16)


class Tee(io.TextIOBase):
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)
            stream.flush()
        return len(text)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def code_with_overrides(source, overrides, filename):
    """Return executable code and the same source with requested assignments."""
    tree = ast.parse(source, filename=filename)
    changed = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in overrides:
                node.value = ast.parse(repr(overrides[target.id]), mode="eval").body
                changed.add(target.id)
    if changed != set(overrides):
        raise ValueError(f"Missing assignment override(s): {set(overrides) - changed}")
    updated_source = ast.unparse(ast.fix_missing_locations(tree)) + "\n" if overrides else source
    return compile(updated_source, filename, "exec"), updated_source


def validate_assignment_ready(csv_path, root=ROOT):
    """Require the reviewed, committed dataset and preregistered criteria."""
    if csv_path.resolve() != (root / "labels.csv").resolve():
        raise ValueError("Assignment training must use this repository's reviewed labels.csv.")
    record_path = root / "data/review_completed.json"
    if not record_path.is_file():
        raise ValueError(
            "Finish the personal criteria, cold-labeling exercise, and draft-label review, "
            "then import the review to create data/review_completed.json before training."
        )
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read the completed review record: {exc}") from exc
    if not isinstance(record, dict) or record.get("completed") is not True:
        raise ValueError("The human review record is not marked completed: true.")
    hashes = {}
    for filename, key in (("labels.csv", "labels_sha256"), ("criteria.md", "criteria_sha256")):
        path = root / filename
        if not path.is_file():
            raise ValueError(f"Missing reviewed assignment file: {filename}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if record.get(key) != digest:
            raise ValueError(f"{filename} no longer matches the completed human review. Review and import it again.")
        hashes[key] = digest
    try:
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", "criteria.md", "labels.csv"],
            cwd=root, check=True, capture_output=True, text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", "criteria.md", "labels.csv"],
            cwd=root, check=True, capture_output=True, text=True,
        ).stdout
        if status.strip():
            raise ValueError("Commit criteria.md and labels.csv before training to preserve preregistration.")
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise ValueError("Commit criteria.md and labels.csv in this repository before training.") from exc
    return {**hashes, "preregistered_commit": commit, "human_review_completed": True}


def validate_label_values(csv_path, labels):
    """Catch pandas null labels, blanks, and taxonomy mismatches before models load."""
    import pandas as pd

    if not labels or any(not label.strip() for label in labels) or len(set(labels)) != len(labels):
        raise ValueError("Label names must be nonblank and unique.")
    frame = pd.read_csv(csv_path)
    if "label" not in frame.columns:
        raise ValueError("The dataset is missing its label column.")
    blank = frame["label"].isna() | frame["label"].astype(str).str.strip().eq("")
    if blank.any():
        rows = [int(index) + 2 for index in frame.index[blank]]
        raise ValueError(f"The dataset contains missing/blank labels at CSV rows {rows}.")
    unknown = sorted(set(frame["label"].astype(str).str.strip()) - set(labels))
    if unknown:
        raise ValueError(f"Dataset labels are absent from --labels: {unknown}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--practice", action="store_true")
    source.add_argument("--csv", type=Path)
    parser.add_argument("--labels", nargs="+")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--name", default="James Paek")
    parser.add_argument("--email", default="121907336+jamespaek1@users.noreply.github.com")
    args = parser.parse_args()
    if args.practice and args.labels:
        parser.error("Practice uses the starter taxonomy unchanged; omit --labels.")
    if not args.practice and not args.labels:
        parser.error("A personal dataset run requires explicit --labels.")

    csv_path = (ROOT / "data/practice_labels.csv") if args.practice else args.csv.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else (
        ROOT / ".cache/practice-run" if args.practice else ROOT
    )
    if args.practice and output_dir == ROOT:
        parser.error("Practice may not write results into the repository root.")
    if not csv_path.is_file():
        parser.error(f"CSV not found: {csv_path}")
    review_metadata = {}
    if not args.practice:
        try:
            review_metadata = validate_assignment_ready(csv_path)
            validate_label_values(csv_path, args.labels)
        except ValueError as exc:
            parser.error(str(exc))
    model_dir = ROOT / "models/unit5"
    if not args.practice and model_dir.exists():
        parser.error(f"An assignment model already exists; preserve it before rerunning: {model_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in ("results.json", "test_split.csv", "executed-notebook.ipynb"):
        if (output_dir / name).exists():
            parser.error(f"Existing output would be overwritten: {output_dir / name}")

    # Both the model and all training execute locally. This public model needs
    # no authentication; suppress implicit tokens and optional hub telemetry.
    os.environ.setdefault("HF_HOME", str(ROOT / ".cache/huggingface"))
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    prefix = "practice" if args.practice else "assignment"
    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    log_path = evidence_dir / f"{prefix}-run.log"
    summary_path = evidence_dir / f"{prefix}-summary.json"
    if log_path.exists() or summary_path.exists():
        parser.error("Evidence already exists; preserve it before starting another run.")
    notebook_bytes = (ROOT / "takemeter.ipynb").read_bytes()
    notebook = json.loads(notebook_bytes)
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
    metadata = {
        "scope": "PRACTICE ONLY — supplied 60-row practice data; not project submission evidence" if args.practice else "Personal assignment run",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "notebook_sha256": hashlib.sha256(notebook_bytes).hexdigest(),
        "csv": str(csv_path.relative_to(ROOT)) if csv_path.is_relative_to(ROOT) else str(csv_path),
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "output_dir": str(output_dir.relative_to(ROOT)) if output_dir.is_relative_to(ROOT) else str(output_dir),
        "executed_cell_indices": [],
        "command": " ".join(sys.argv),
        "status": "running",
        **review_metadata,
    }
    namespace = {"__name__": "__main__"}
    started = time.monotonic()
    exit_code = 0
    os.chdir(ROOT)
    with log_path.open("w", encoding="utf-8") as log:
        with redirect_stdout(Tee(sys.stdout, log)), redirect_stderr(Tee(sys.stderr, log)):
            print(metadata["scope"])
            print(json.dumps(metadata, indent=2))
            try:
                for count, index in enumerate(CELLS, start=1):
                    cell = notebook["cells"][index]
                    overrides = {}
                    if index == 4:
                        overrides = {"NAME": args.name, "EMAIL": args.email}
                    elif index == 6:
                        overrides = {"LABELS": ["analysis", "hot_take", "reaction"] if args.practice else args.labels}
                    elif index == 8:
                        overrides = {"CSV": str(csv_path)}
                        os.chdir(output_dir)
                    print(f"\n--- Executing notebook code cell index {index}; overrides: {overrides} ---")
                    executable, executed_source = code_with_overrides(
                        "".join(cell["source"]), overrides, f"takemeter.ipynb cell {index}"
                    )
                    cell["source"] = executed_source.splitlines(keepends=True)
                    captured = io.StringIO()
                    with redirect_stdout(Tee(sys.stdout, captured)), redirect_stderr(Tee(sys.stderr, captured)):
                        exec(executable, namespace)
                    cell["execution_count"] = count
                    cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": captured.getvalue().splitlines(keepends=True)}]
                    metadata["executed_cell_indices"].append(index)
                    if index == 10 and namespace.get("problems"):
                        raise RuntimeError("Dataset validation reported problems; training stopped.")
                    if index == 8:
                        validate_label_values(csv_path, namespace["LABELS"])
                if not args.practice:
                    namespace["trainer"].save_model(str(model_dir))
                    namespace["tokenizer"].save_pretrained(str(model_dir))
                    metadata["saved_model_dir"] = str(model_dir.relative_to(ROOT))
                    print(f"Saved local fine-tuned model and tokenizer to {model_dir}")
                metadata["status"] = "completed"
                metadata["results"] = namespace["results"]
                metadata["settings"] = {key: namespace[key] for key in (
                    "LABELS", "BASE_MODEL", "EPOCHS", "LEARNING_RATE", "BATCH_SIZE", "MAX_LENGTH", "SEED"
                )}
                metadata["n_rows"] = len(namespace["df"])
                metadata["split_sizes"] = {key: len(namespace[f"{key}_df"]) for key in ("train", "val", "test")}
                print(f"\n{metadata['scope']}\nCompleted successfully.")
            except BaseException as exc:
                metadata["status"] = "failed"
                metadata["error"] = f"{type(exc).__name__}: {exc}"
                traceback.print_exc()
                exit_code = 1
            finally:
                metadata["elapsed_seconds"] = round(time.monotonic() - started, 3)
                metadata["finished_utc"] = datetime.now(timezone.utc).isoformat()
                summary_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
                (output_dir / "executed-notebook.ipynb").write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
