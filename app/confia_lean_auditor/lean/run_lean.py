from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from confia_lean_auditor.core.paths import InvalidProblemId, get_problem_dir


FORBIDDEN_TOKENS = [
    "sorry",
    "admit",
    "unsafe",
    "axiom",
]


def strip_lean_comments(source: str) -> str:
    source = re.sub(r"/-.*?-/", "", source, flags=re.DOTALL)
    source = re.sub(r"--.*?$", "", source, flags=re.MULTILINE)
    return source


def detect_forbidden_tokens(source: str) -> List[str]:
    clean = strip_lean_comments(source).lower()
    found = []

    for token in FORBIDDEN_TOKENS:
        if re.search(r"\b" + re.escape(token) + r"\b", clean):
            found.append(token)

    return found


def classify(exit_code: int, forbidden: List[str], stdout: str, stderr: str) -> str:
    combined = (stdout + "\n" + stderr).lower()

    if forbidden:
        return "invalid_forbidden_token"

    if "declaration uses 'sorry'" in combined:
        return "invalid_uses_sorry"

    if exit_code == 0:
        return "verified"

    if "unknown identifier" in combined:
        return "lean_error_unknown_identifier"

    if "unsolved goals" in combined:
        return "lean_error_unsolved_goals"

    if "failed to synthesize" in combined:
        return "lean_error_synthesis_failed"

    if "timeout" in combined:
        return "lean_timeout"

    return "lean_error"


def run_lean_file(repo_root: Path, lean_file: Path, timeout_seconds: int = 30) -> Dict[str, Any]:
    source = lean_file.read_text(encoding="utf-8")
    forbidden = detect_forbidden_tokens(source)

    cmd = ["lake", "env", "lean", str(lean_file)]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout or ""
        stderr = exc.stderr or "Lean timeout"

    status = classify(exit_code, forbidden, stdout, stderr)

    return {
        "status": status,
        "compiled": exit_code == 0,
        "exit_code": exit_code,
        "uses_forbidden_token": bool(forbidden),
        "forbidden_tokens_found": forbidden,
        "stdout": stdout,
        "stderr": stderr,
    }


def run_problem(repo_root: Path, problem_id: str) -> Dict[str, Any]:
    try:
        problem_dir = get_problem_dir(repo_root, problem_id)
    except InvalidProblemId as exc:
        return {
            "status": "invalid_problem_id",
            "compiled": False,
            "exit_code": -1,
            "uses_forbidden_token": False,
            "forbidden_tokens_found": [],
            "stdout": "",
            "stderr": str(exc),
        }

    lean_file = problem_dir / "certificate" / "Statement.lean"

    if not lean_file.exists():
        return {
            "status": "lean_file_missing",
            "compiled": False,
            "exit_code": -1,
            "uses_forbidden_token": False,
            "forbidden_tokens_found": [],
            "stdout": "",
            "stderr": "Lean file not found: " + str(lean_file),
        }

    return run_lean_file(repo_root=repo_root, lean_file=lean_file)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem-id", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    result = run_problem(Path(args.repo_root).resolve(), args.problem_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
