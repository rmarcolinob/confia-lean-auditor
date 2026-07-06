from pathlib import Path
import json
import shutil

import pytest

from confia_lean_auditor.core.paths import get_problem_dir, get_repo_root
from confia_lean_auditor.core.problem_assets import (
    ProblemAssetValidationError,
    validate_problem_assets,
)


def copy_problem_dir(tmp_path: Path, problem_id: str) -> Path:
    root = get_repo_root()
    source = get_problem_dir(root, problem_id)
    target = tmp_path / problem_id
    shutil.copytree(source, target)
    return target


def test_ita2025q1_problem_assets_are_valid():
    root = get_repo_root()
    problem_dir = get_problem_dir(root, "ITA2025Q1")

    validate_problem_assets(problem_dir, "ITA2025Q1")


def test_invalid_rubric_missing_items_is_diagnosed(tmp_path):
    problem_dir = copy_problem_dir(tmp_path, "ITA2025Q1")

    rubric_path = problem_dir / "rubric.json"
    rubric = json.loads(rubric_path.read_text())
    rubric.pop("items")
    rubric_path.write_text(json.dumps(rubric))

    with pytest.raises(ProblemAssetValidationError) as excinfo:
        validate_problem_assets(problem_dir, "ITA2025Q1")

    assert "rubric.json" in str(excinfo.value)
    assert "items" in str(excinfo.value)


def test_invalid_microclaim_dependency_is_diagnosed(tmp_path):
    problem_dir = copy_problem_dir(tmp_path, "ITA2025Q1")

    microclaims_path = problem_dir / "microclaims.json"
    data = json.loads(microclaims_path.read_text())
    data["microclaims"][0]["depends_on_microclaim_ids"] = ["mc_inexistente"]
    microclaims_path.write_text(json.dumps(data))

    with pytest.raises(ProblemAssetValidationError) as excinfo:
        validate_problem_assets(problem_dir, "ITA2025Q1")

    assert "mc_inexistente" in str(excinfo.value)
