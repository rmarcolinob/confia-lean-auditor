"""Adversarial storage changes must fail before the accepted-source engine."""
import json

import pytest

from confia_lean_auditor.core.schemas import AuditResponse, RubricAssessment, RubricItemResult
from confia_lean_auditor.reports.report_builder import build_pedagogical_report
from confia_lean_auditor.submission_audits import router as audits
from confia_lean_auditor.submissions import router as submissions
from confia_lean_auditor.submissions.integrity import model_sha256
from test_submission_audits import setup, source, accept, execute


@pytest.mark.parametrize("mutation", ["kind", "order", "page_index", "text", "math", "revision_metadata", "reviewer_reference",
                                      "acceptance_note", "revision_digest", "receipt", "missing_receipt"])
def test_post_acceptance_tampering_blocks_engine_without_repair(setup, mutation):
    client, calls = setup
    sid, revision = source(client)
    request = accept(client, sid, revision)
    folder = submissions.store()._transcription_folder(revision["transcription_id"])
    revision_fields = {"kind", "order", "page_index", "text", "math", "revision_metadata"}
    if mutation in revision_fields:
        path = folder / "revisions" / "revision_000001.json"
        data = json.loads(path.read_text())
        if mutation == "kind":
            data["segments"][0]["kind"] = "mixed"
        elif mutation == "order":
            data["segments"][0]["order"], data["segments"][1]["order"] = 1, 0
        elif mutation == "page_index":
            data["segments"][0]["page_index"] = 1
        elif mutation == "text":
            data["segments"][0]["text"] = "Texto adulterado"
        elif mutation == "math":
            data["segments"][1]["latex"] = "2 + 2 = 4"
        else:
            data["reviewer_reference"] = "outro-professor"
        from confia_lean_auditor.submissions.schemas import TranscriptionRevision
        original_digest = json.loads((folder / "acceptances" / "acceptance_000001.json").read_text())["accepted_revision_sha256"]
        assert model_sha256(TranscriptionRevision.model_validate(data)) != original_digest
    elif mutation in {"receipt", "missing_receipt"}:
        path = folder / "acceptance_receipts" / "acceptance_000001.json"
        data = json.loads(path.read_text())
        data["acceptance_sha256"] = "0" * 64
    else:
        path = folder / "acceptances" / "acceptance_000001.json"
        data = json.loads(path.read_text())
        field = "accepted_revision_sha256" if mutation == "revision_digest" else mutation
        data[field] = "0" * 64 if mutation == "revision_digest" else "Alterado depois do aceite"
    if mutation == "missing_receipt":
        path.unlink()
    else:
        path.write_text(json.dumps(data))
    before = {p: p.read_bytes() for p in folder.rglob("*") if p.is_file()}
    response = execute(client, sid, request)
    assert response.status_code == 409, response.text
    assert "Integridade da revisão ou do aceite" in response.json()["detail"]
    assert calls == [] and list(audits.service().root.glob("aud_*.json")) == []
    assert {p: p.read_bytes() for p in before} == before


def test_intact_acceptance_receipt_binds_exact_persisted_revision(setup):
    client, calls = setup
    sid, revision = source(client)
    request = accept(client, sid, revision)
    store = submissions.store()
    folder = store._transcription_folder(revision["transcription_id"])
    persisted = store._read_revisions(folder)[0]
    acceptance = store._read_acceptances(folder)[0]
    receipt = store.assert_acceptance_integrity(folder, persisted, acceptance)
    assert acceptance.accepted_revision_sha256 == model_sha256(persisted)
    assert receipt.acceptance_sha256 == model_sha256(acceptance)
    run = execute(client, sid, request).json()
    assert run["status"] == "COMPLETED" and len(calls) == 1
    assert run["source"]["provenance"]["revision"] == persisted.model_dump(mode="json")
    assert run["source"]["provenance"]["acceptance_receipt"] == receipt.model_dump(mode="json")


def test_interrupted_acceptance_publication_never_projects_accepted_or_repairs(setup, monkeypatch):
    from confia_lean_auditor.submissions.store import SubmissionStore
    client, calls = setup
    sid, revision = source(client)
    write = SubmissionStore._write_atomic_new
    def interrupted(path, data):
        if path.parent.name == "acceptances":
            raise OSError("interrupted publication")
        return write(path, data)
    monkeypatch.setattr(SubmissionStore, "_write_atomic_new", staticmethod(interrupted))
    body = {"revision_number": 1, "reviewer_reference": "professor-teste-01"}
    url = f'/transcriptions/{revision["transcription_id"]}/accept'
    assert client.post(url, json=body).status_code == 503
    history = client.get(f'/transcriptions/{revision["transcription_id"]}').json()
    assert history["revisions"][0]["status"] == "NEEDS_REVIEW" and history["acceptances"] == []
    monkeypatch.setattr(SubmissionStore, "_write_atomic_new", staticmethod(write))
    folder = submissions.store()._transcription_folder(revision["transcription_id"])
    before = {p: p.read_bytes() for p in folder.rglob("*") if p.is_file()}
    assert client.post(url, json=body).status_code == 409
    assert {p: p.read_bytes() for p in before} == before
    request = {"transcription_id": revision["transcription_id"], "revision_number": 1,
               "acceptance_id": "acc_" + "0" * 32}
    assert execute(client, sid, request).status_code == 409 and calls == []


def test_legacy_event_stays_readable_but_requires_new_human_review(setup):
    from test_transcriptions import segments
    client, calls = setup
    sid, revision = source(client)
    old_request = accept(client, sid, revision)
    store = submissions.store()
    folder = store._transcription_folder(revision["transcription_id"])
    path = store._acceptance_path(folder, 1)
    data = json.loads(path.read_text())
    del data["accepted_revision_sha256"]
    path.write_text(json.dumps(data))
    store._acceptance_receipt_path(folder, 1).unlink()
    before = path.read_bytes()
    history = client.get(f'/transcriptions/{revision["transcription_id"]}')
    assert history.status_code == 200 and history.json()["revisions"][0]["status"] == "NEEDS_REVIEW"
    assert execute(client, sid, old_request).status_code == 409 and calls == []
    assert client.post(f'/transcriptions/{revision["transcription_id"]}/accept', json={
        "revision_number": 1, "reviewer_reference": "professor-teste-01"}).status_code == 409
    new_revision = client.post(f'/transcriptions/{revision["transcription_id"]}/revisions', json={
        "based_on_revision_number": 1, "reviewer_reference": "professor-teste-01", "segments": segments()}).json()
    new_request = accept(client, sid, new_revision)
    assert execute(client, sid, new_request).json()["status"] == "COMPLETED"
    assert len(calls) == 1 and path.read_bytes() == before


def test_receipt_directory_symlink_blocks_publication_without_external_writes(setup):
    client, calls = setup
    sid, revision = source(client)
    store = submissions.store()
    folder = store._transcription_folder(revision["transcription_id"])
    outside = store.root.parent / "outside-receipts"
    outside.mkdir()
    store._acceptance_receipt_path(folder, 1).parent.symlink_to(outside, target_is_directory=True)
    response = client.post(f'/transcriptions/{revision["transcription_id"]}/accept', json={
        "revision_number": 1, "reviewer_reference": "professor-teste-01"})
    assert response.status_code == 409
    assert not store._acceptance_path(folder, 1).exists()
    assert list(outside.iterdir()) == [] and calls == []


@pytest.mark.parametrize("field", ["score", "subtotal", "verdict", "rubric_assessment",
    "evidence_items", "student_claim_checks", "formal_steps", "attention_points", "feedback"])
def test_result_tampering_is_detected_on_get_and_retry(setup, monkeypatch, field):
    import confia_lean_auditor.main as main
    from pathlib import Path
    from test_submission_audits import result
    client, calls = setup
    def engine(request):
        calls.append(request)
        response = result(request.problem_id)
        response.score = 10
        response.verdict = "correto"
        response.rubric_assessment = RubricAssessment(score=10, max_score=10,
            evaluated_score=10, evaluated_max_score=10, items=[RubricItemResult(
                id="criterion", description="Critério", detected=True, points=10,
                max_points=10, mathematical_status="supported")])
        response.pedagogical_report = build_pedagogical_report(score=10, max_score=10,
            verdict="correto", rubric=response.rubric_assessment, student_claims=[],
            student_claim_checks=[], microclaims=[], artifact_dir=response.artifact_dir)
        Path(response.artifact_dir, "audit.json").write_text(response.model_dump_json())
        return response
    monkeypatch.setattr(main, "execute_audit", engine)
    sid, rev = source(client)
    request = accept(client, sid, rev)
    run = execute(client, sid, request).json()
    path = audits.service()._path(run["audit_run_id"])
    data = json.loads(path.read_text())
    original_digest = data["result_sha256"]
    assert model_sha256(AuditResponse.model_validate(data["result"])) == original_digest
    result_data = data["result"]
    if field == "score":
        result_data["score"] = None
    elif field == "subtotal":
        result_data["rubric_assessment"]["evaluated_score"] = 7
    elif field == "verdict":
        result_data["verdict"] = "inconclusivo"
    elif field == "rubric_assessment":
        result_data["rubric_assessment"]["items"][0]["description"] = "Adulterado"
    elif field == "evidence_items":
        result_data["pedagogical_report"]["evidence_items"][0]["explanation"] = "Adulterado"
    elif field == "student_claim_checks":
        result_data["student_claim_checks"].append({"id": "adulterado", "status": "unverified"})
    elif field == "formal_steps":
        result_data["formal_steps"].append({"id": "adulterado", "type": "equality",
            "description": "Adulterado", "evidence": "a=a", "lhs": "a", "rhs": "a",
            "lean_method": "rfl", "lean_file": str(Path(result_data["artifact_dir"], "diagnostic.lean")),
            "status": "unverified", "compiled": False, "exit_code": 1})
    elif field == "attention_points":
        result_data["pedagogical_report"]["attention_points"].append("Limitação adulterada")
    else:
        result_data["feedback"] = "Adulterado"
    assert model_sha256(AuditResponse.model_validate(result_data)) != original_digest
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    assert client.get(f'/submission-audits/{run["audit_run_id"]}').status_code == 409
    assert client.get(f'/submissions/{sid}/audits').status_code == 409
    assert execute(client, sid, request).status_code == 409
    assert len(calls) == 1 and path.read_bytes() == before


@pytest.mark.parametrize("kind", ["null", "missing_directory", "missing_file"])
def test_missing_artifact_references_cannot_publish_completed(setup, monkeypatch, kind):
    import confia_lean_auditor.main as main
    from pathlib import Path
    from test_submission_audits import result
    client, calls = setup
    def engine(req):
        calls.append(req)
        response = result(req.problem_id)
        if kind == "missing_file":
            Path(response.artifact_dir, "audit.json").unlink()
            return response
        return response.model_copy(update={"artifact_dir": None if kind == "null" else "/nonexistent/confia/artifacts"})
    monkeypatch.setattr(main, "execute_audit", engine)
    sid, rev = source(client)
    run = execute(client, sid, accept(client, sid, rev)).json()
    assert run["status"] == "FAILED" and run["result"] is None
    assert run["artifact_dir"] is None and run["result_sha256"] is None
