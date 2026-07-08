import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from confia_lean_auditor.core.problem_assets import ProblemConfig


def test_problem_config_rejects_unknown_fields():
    data = json.loads(Path("problems/ITA2025Q3/problem.json").read_text(encoding="utf-8"))
    data["unknown_contract_field"] = "should fail"

    with pytest.raises(ValidationError):
        ProblemConfig.model_validate(data)


def test_problem_assets_do_not_allow_extra_fields_textually():
    text = Path("app/confia_lean_auditor/core/problem_assets.py").read_text(encoding="utf-8")

    assert 'extra="allow"' not in text
    assert "extra='allow'" not in text
    assert "extra=\"forbid\"" in text or "extra='forbid'" in text
