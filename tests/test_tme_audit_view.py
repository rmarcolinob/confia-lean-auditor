"""The pilot exposes the full persisted audit through the same public boundary."""
import json
from pathlib import Path

import pytest

import confia_lean_auditor.main as main
from confia_lean_auditor.core.schemas import AuditResponse
from confia_lean_auditor.submission_audits import router as audits
from test_submission_audits import result, persisted_run
from test_tme_pilot import setup, create_case, scan_payload
from test_submissions import payload

FIXTURE = Path(__file__).parent / "fixtures" / "rich_audit_response.json"


def rich_result(problem_id):
    base = result(problem_id)
    folder = Path(base.artifact_dir)
    data = json.loads(FIXTURE.read_text())
    data["problem_id"] = data["extracted_claims"]["problem_id"] = problem_id
    data["artifact_dir"] = str(folder)
    entries = [data["lean_certificate"], *data["formal_steps"], *data["student_claim_checks"]]
    for entry in entries:
        if entry.get("lean_file"):
            target = folder / entry["lean_file"]
            target.write_text("-- synthetic formal artifact for presentation contracts\n")
            entry["lean_file"] = str(target)
    full = AuditResponse.model_validate(data)
    (folder / "audit.json").write_text(full.model_dump_json())
    return full


@pytest.mark.parametrize("mode", ["DIGITAL_INK", "IMAGE_SCAN"])
def test_full_run_survives_pilot_post_list_school_read_and_manual_decision(setup, monkeypatch, mode):
    client, _, _ = setup
    monkeypatch.setattr(main, "execute_audit", rich_result_for_request)
    case = create_case(client, mode)
    base = f'/tme/cases/{case["case_id"]}'
    body = payload()
    body["student_reference"] = None
    source = client.post(f"{base}/scan", json=scan_payload(1)) if mode == "IMAGE_SCAN" else client.post(f"{base}/digital-submission", json=body)
    assert source.status_code == 201, source.text
    sid = source.json()["submission_id"]
    response = client.post(f"/submissions/{sid}/transcriptions", json={"reviewer_reference": "test-evaluator", "segments": [
        {"segment_id": "same", "page_index": 0, "order": 0, "kind": "text", "text": "2 + 2 = 4"}
    ]})
    assert response.status_code == 201, response.text
    revision = response.json()
    tid = revision["transcription_id"]
    acceptance = client.post(f"{base}/transcriptions/{tid}/accept", json={"revision_number": 1}).json()["acceptance"]
    response = client.post(f"{base}/audits", json={"transcription_id": tid, "revision_number": 1,
        "acceptance_id": acceptance["acceptance_id"]})
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["status"] == "COMPLETED"
    stored = persisted_run(run)
    assert run["result"]["score"] is None
    assert len(run["result"]["rubric_assessment"]["items"]) == 4
    for field in ("rubric_assessment", "extracted_claims", "pedagogical_report", "score", "max_score", "verdict"):
        assert run["result"][field] == stored["result"][field]
    assert [c["status"] for c in run["result"]["student_claim_checks"]] == ["verified", "technical_error", "unverified"]
    assert run["result"]["formal_steps"][0]["status"] == "verified"
    assert run["required_artifacts"] and run["artifact_manifest_sha256"]
    assert run["result_sha256"] == stored["result_sha256"]
    before = audits.service()._path(run["audit_run_id"]).read_bytes()
    # Test fixture uses the existing legacy auth-off setup only to compare route payloads.
    # Anonymous-school-access isolation is covered by test_tme_demo_auth.
    assert client.get(f"{base}/audits").json() == [run]
    assert client.get(f"/submissions/{sid}/audits").json() == [run]
    assert client.get(f'/submission-audits/{run["audit_run_id"]}').json() == run
    assert audits.service()._path(run["audit_run_id"]).read_bytes() == before
    decision = client.post(f"{base}/decision", json={"audit_run_id": run["audit_run_id"], "max_points": 10,
        "final_points": 8, "feedback": "Decisão humana após leitura da análise completa."})
    assert decision.status_code == 201, decision.text
    assert decision.json()["suggested_points"] is None
    assert float(decision.json()["final_points"]) == 8
    assert audits.service()._path(run["audit_run_id"]).read_bytes() == before


def rich_result_for_request(request):
    return rich_result(request.problem_id)


def test_both_shells_load_the_shared_renderer_before_consumers():
    static = Path(main.STATIC_DIR)
    for page, consumer in (("index.html", "app.js"), ("tme/index.html", "tme/tme.js")):
        html = (static / page).read_text()
        assert html.index('/static/audit-view.js') < html.index('/static/' + consumer)
        assert '/static/audit-view.css' in html
    for file in ("submissions/teacher.js", "tme/tme.js"):
        source = (static / file).read_text()
        assert 'ConfIAReport.render(' in source and 'auditRun: run' in source
