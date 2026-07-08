from pathlib import Path


def test_microclaim_dependencies_do_not_default_to_true():
    text = Path(
        "app/confia_lean_auditor/lean/microclaim_evaluator.py"
    ).read_text(encoding="utf-8")

    assert "dependencies_verified=True" not in text
