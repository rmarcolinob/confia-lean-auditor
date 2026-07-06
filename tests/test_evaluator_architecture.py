from pathlib import Path


def test_evaluators_do_not_parse_raw_json_directly():
    files = [
        Path("app/confia_lean_auditor/rubric/rubric_evaluator.py"),
        Path("app/confia_lean_auditor/lean/microclaim_evaluator.py"),
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")

        assert "import json" not in text
        assert "json.loads" not in text
