"""Existing protocol tests exercise the explicitly supported legacy development mode.

CORE-AUTH-01 tests opt back into the default authenticated mode per test.
"""
import pytest


@pytest.fixture(autouse=True)
def legacy_protocol_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "0")
    monkeypatch.setenv("CONFIA_TEACHER_DECISIONS_DIR", str(tmp_path / "teacher_decisions"))
    # Unit/protocol tests never spend real API credits. Scoring-policy tests inject
    # an explicit adjudicator; unavailable-provider tests exercise the null path.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
