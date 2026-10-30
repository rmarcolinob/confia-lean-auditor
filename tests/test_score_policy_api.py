"""Full engine/API boundary with isolated files and explicit fake external services."""
from pathlib import Path
from types import SimpleNamespace
import json

import pytest
from fastapi.testclient import TestClient

import confia_lean_auditor.main as main
import confia_lean_auditor.lean.formal_step_evaluator as formal
from confia_lean_auditor.rubric import secondary_adjudicator as secondary
from confia_lean_auditor.core.schemas import AuditRequest, AuditResponse
from tests.audit_contract import assert_score_contract

ROOT = Path(__file__).resolve().parents[1]
REAL_ADJUDICATE = secondary.adjudicate


@pytest.fixture
def isolated_engine(tmp_path, monkeypatch):
    (tmp_path / "problems").symlink_to(ROOT / "problems", target_is_directory=True)
    monkeypatch.setattr(main, "repo_root", lambda: tmp_path)
    verified = lambda *a, **k: {"status": "verified", "compiled": True, "exit_code": 0,
        "uses_forbidden_token": False, "forbidden_tokens_found": []}
    monkeypatch.setattr(main, "run_lean_file", verified)
    monkeypatch.setattr(formal, "run_lean_file", verified)
    monkeypatch.setattr(main, "check_student_claims_for_problem", lambda **k: [])
    def provider(payload):
        return {c["id"]: {"suggested_points": c["max_points"],
                "evidence": [payload["solution_text"]], "decision": "award",
                "rationale": secondary.rationale_options(c)["award"][0]}
                for c in payload["pending_criteria"]}, {"provider": "test"}
    monkeypatch.setattr(secondary, "adjudicate", provider)
    return tmp_path


def test_public_api_exposes_suggestion_and_keeps_verification(isolated_engine):
    client = TestClient(main.app)
    response = client.post("/audit", json={"problem_id": "ITA2025Q3", "solution": "Conclusão escrita com outras palavras."})
    assert response.status_code == 200
    data = response.json()
    assert_score_contract(data)
    assert data["score"] == 10 and data["verdict"] == "correto"
    assert data["coverage"] == 0 and data["estimated_points"] == 10 and data["needs_review"]
    assert data["evaluated_score"] == 0 and data["scoring_policy"] == "SCORE-POLICY-02"
    assert data["pedagogical_report"]["score"] == 10
    assert data["rubric_assessment"]["assessment_status"] == "indeterminate"
    assert all(i["points"] is None and i["suggested_points"] is not None
               for i in data["rubric_assessment"]["items"])
    assert "teacher_final_points" not in data and "final_points" not in data
    assert data["artifact_dir"] is None


def test_empty_engine_response_is_explicitly_unscorable(isolated_engine):
    result = main.execute_audit(AuditRequest(problem_id="ITA2025Q3", solution=" \n"))
    assert result.score is None and result.unscorable_reason == "EMPTY_SOLUTION"
    assert result.verdict == "inconclusivo" and result.needs_review
    raw = json.loads((Path(result.artifact_dir) / "audit.json").read_text())
    assert AuditResponse.model_validate(raw).model_dump(mode="json") == raw
    trace=json.loads((Path(result.artifact_dir)/"secondary_adjudication.json").read_text())
    assert trace["schema_version"]==secondary.SCHEMA_VERSION
    assert all(c["validation_status"]=="not_requested" for c in trace["criteria"])


def test_engine_persists_bounded_failure_trace(isolated_engine,monkeypatch):
    from tests.test_secondary_adjudicator_contract import fake_client
    from tests.secondary_selection_helpers import selection
    def invalid(call):
        payload=json.loads(call["input"]);result=selection(payload)
        for value in result.values():value["evidence_ids"]=["E999"]
        return result
    monkeypatch.setattr(secondary,"adjudicate",REAL_ADJUDICATE)
    seen,_=fake_client(monkeypatch,[invalid,invalid])
    result=main.execute_audit(AuditRequest(problem_id="ITA2025Q3",solution="Não sei resolver."))
    trace=json.loads((Path(result.artifact_dir)/"secondary_adjudication.json").read_text())
    assert result.score is None and result.unscorable_reason=="ADJUDICATOR_INVALID_RESPONSE"
    assert trace["retry_count"]==1 and trace["validation_status"]=="rejected"
    assert trace["attempt_details"][0]["validation_error"]["reason"]=="unknown_id"
    assert all(c['candidate_evidence'] for c in trace['criteria'])
    assert len(seen)==2 and all(c["suggested_points"] is None for c in trace["criteria"])


@pytest.mark.parametrize("problem,status", [("DOES_NOT_EXIST", 404), ("../invalid", 400)])
def test_invalid_problem_keeps_existing_error_contract(isolated_engine, problem, status):
    response = TestClient(main.app).post("/audit", json={"problem_id": problem, "solution": "Some text"})
    assert response.status_code == status
    assert "score" not in response.json()


def test_provider_uses_structured_schema_and_original_candidate_text(monkeypatch):
    import openai
    from tests.secondary_selection_helpers import selection
    seen = []
    payload = {"solution_text": "Trecho literal com 9.", "pending_criteria": [
        {"id": "criterion", "max_points": 3, "allowed_points": [0, 3]}]}
    decision = selection(payload)
    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = self
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def create(self, **kwargs):
            seen.append(kwargs)
            return SimpleNamespace(status="completed", output_text=json.dumps(decision), id="test", model="test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-not-a-key")
    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    decisions, metadata = secondary.adjudicate(payload)
    assert {k:{f:v for f,v in d.items() if f!='evidence'} for k,d in decisions.items()} == decision and metadata["request_sha256"]
    assert decisions['criterion']['evidence']==[payload['solution_text']]
    call = seen[0]
    wire=json.loads(call['input']);assert 'solution_text' not in wire and call["store"] is False
    assert wire['pending_criteria'][0]['candidate_evidence'][0]['source_text']==payload['solution_text']
    assert call["text"]["format"]["strict"] is True
    branches=call["text"]["format"]["schema"]["properties"]["criterion"]['anyOf']
    assert {b['properties']['suggested_points']['enum'][0] for b in branches}=={0,3}
    assert all('evidence' not in b['properties'] for b in branches)
