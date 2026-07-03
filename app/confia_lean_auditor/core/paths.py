from __future__ import annotations

import os
import re
from pathlib import Path


VALID_PROBLEM_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class InvalidProblemId(ValueError):
    pass


def get_repo_root() -> Path:
    env_root = os.environ.get("CONFIA_LEAN_AUDITOR_ROOT")
    if env_root:
        return Path(env_root).resolve()

    # paths.py fica em:
    # repo/app/confia_lean_auditor/core/paths.py
    return Path(__file__).resolve().parents[3]


def validate_problem_id(problem_id: str) -> str:
    if not VALID_PROBLEM_ID_RE.fullmatch(problem_id):
        raise InvalidProblemId(
            "Invalid problem_id. Use only letters, numbers, underscore and hyphen."
        )

    return problem_id


def get_problem_dir(repo_root: Path, problem_id: str) -> Path:
    safe_problem_id = validate_problem_id(problem_id)

    problems_root = (repo_root / "problems").resolve()
    problem_dir = (problems_root / safe_problem_id).resolve()

    try:
        problem_dir.relative_to(problems_root)
    except ValueError as exc:
        raise InvalidProblemId("Invalid problem_id path.") from exc

    return problem_dir
