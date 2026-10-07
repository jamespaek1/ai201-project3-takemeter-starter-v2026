"""Capture the starter checks and notebook Section 1 without loading data/models.

Run from the repository root with: .venv/bin/python scripts/check_environment.py
"""

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if Path.cwd().resolve() != ROOT:
    raise SystemExit("Run this script from the repository root.")

output = io.StringIO()
with redirect_stdout(output), redirect_stderr(output):
    print("TakeMeter environment evidence")
    print(f"Recorded UTC: {datetime.now(timezone.utc).isoformat()}")
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print("Scope: starter test.py and notebook Section 1 only.")
    print("No training, model download, label loading, or results inspection.")
    print("\nCommand: .venv/bin/python test.py")
    check = subprocess.run(
        [sys.executable, "test.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(check.stdout)
    print(f"test.py exit code: {check.returncode}")
    notebook = json.loads((ROOT / "takemeter.ipynb").read_text())
    namespace = {"__name__": "__main__"}
    for cell_index in (2, 4):
        cell = notebook["cells"][cell_index]
        if cell["cell_type"] != "code":
            raise RuntimeError(f"Expected Section 1 code cell at index {cell_index}")
        print(f"\nNotebook Section 1: code cell index {cell_index}")
        exec(compile("".join(cell["source"]), f"takemeter.ipynb cell {cell_index}", "exec"), namespace)
    print("\nInstalled versions (full lock recorded separately):")
    for package in (
        "pandas", "transformers", "datasets", "accelerate", "torch", "scikit-learn"
    ):
        print(f"{package}=={importlib.metadata.version(package)}")

evidence_path = ROOT / "evidence" / "environment.txt"
evidence_path.parent.mkdir(exist_ok=True)
evidence_path.write_text(output.getvalue(), encoding="utf-8")
print(output.getvalue(), end="")
raise SystemExit(check.returncode)
