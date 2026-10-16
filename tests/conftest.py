"""Existing protocol tests exercise the explicitly supported legacy development mode.

CORE-AUTH-01 tests opt back into the default authenticated mode per test.
"""
import pytest


@pytest.fixture(autouse=True)
def legacy_protocol_mode(monkeypatch):
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "0")
