"""Accepted-source bridge contracts; only the explicit integration test runs Lean."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from uuid import uuid4
from pathlib import Path
from threading import Event

from fastapi.testclient import TestClient
import pytest

import confia_lean_auditor.main as main
from confia_lean_auditor.core.schemas import AuditResponse
from confia_lean_auditor.submission_audits import router as audits
from confia_lean_auditor.submissions import router as submissions
from test_submissions import payload
from test_transcriptions import segments, persisted_files
from public_privacy import assert_no_local_paths


def result(problem_id):
    directory = Path(os.environ["CONFIA_SUBMISSION_AUDITS_DIR"]).parent / "engine-artifacts" / uuid4().hex
    directory.mkdir(parents=True)
    for name in ("solution.txt", "claims.json", "student_claims.json", "student_claim_checks.json", "Attempt.lean"):
        (directory / name).write_text("test artifact")
    response = AuditResponse(problem_id=problem_id, score=0, max_score=10, verdict="insuficiente",
        extracted_claims={"problem_id": problem_id, "claims": []}, formal_steps=[],
        rubric_assessment={"score": 0, "max_score": 10, "items": []},
        lean_certificate={"status": "unverified", "compiled": False, "exit_code": 0,
                          "uses_forbidden_token": False, "forbidden_tokens_found": [], "lean_file": str(directory / "Attempt.lean")},
        microclaims=[], feedback="Teste do contrato", artifact_dir=str(directory))
    (directory / "audit.json").write_text(response.model_dump_json())
    return response


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(tmp_path / "audits"))
    calls = []
    def engine(request):
        calls.append(request)
        return result(request.problem_id)
    monkeypatch.setattr(main, "execute_audit", engine)
    return TestClient(main.app), calls


def source(client, state="NEEDS_REVIEW", values=None, request_payload=None):
    sid = client.post("/submissions", json=request_payload or payload()).json()["submission_id"]
    revision = client.post(f"/submissions/{sid}/transcriptions", json={
        "reviewer_reference": "professor-teste-01", "segments": values or segments(), "status": state,
    }).json()
    return sid, revision


def accept(client, sid, revision):
    acceptance = client.post(f'/transcriptions/{revision["transcription_id"]}/accept', json={
        "revision_number": revision["revision_number"], "reviewer_reference": "professor-teste-01",
    }).json()["acceptance"]
    return {"transcription_id": revision["transcription_id"], "revision_number": revision["revision_number"],
            "acceptance_id": acceptance["acceptance_id"]}


def execute(client, sid, request):
    return client.post(f"/submissions/{sid}/audits", json=request)


def persisted_run(run):
    return json.loads(audits.service()._path(run["audit_run_id"]).read_bytes())


def run_files():
    return list(audits.service().root.glob("aud_*.json"))


@pytest.mark.parametrize("state", ["DRAFT", "NEEDS_REVIEW"])
def test_unaccepted_revision_never_enters_engine_or_creates_run(setup, state):
    client, calls = setup
    sid, rev = source(client, state)
    response = execute(client, sid, {"transcription_id": rev["transcription_id"], "revision_number": 1,
                                   "acceptance_id": "acc_" + "0" * 32})
    assert response.status_code == 409
    assert response.json()["detail"] == "A transcrição precisa ser conferida antes da análise."
    assert calls == [] and run_files() == []


def test_exact_accepted_source_lossless_hash_persistence_and_retry(setup):
    client, calls = setup
    sid, rev = source(client)
    request = accept(client, sid, rev)
    folder = submissions.store().root / sid
    before = persisted_files(folder)
    first = execute(client, sid, request)
    assert first.status_code == 200, first.text
    run = first.json()
    assert calls[0].solution == "Cálculo do aluno\n2 + 2 = 5\nlogo\nx=1"
    assert calls[0].problem_id == run["problem_id"]
    assert run["status"] == "COMPLETED" and run["stale"] is False
    assert run["auditor_version"] is None
    assert all(run[key] == request[key] for key in request)
    assert run["source"]["provenance"]["revision"]["segments"] == rev["segments"]
    assert run["source"]["solution_text"] == calls[0].solution
    assert run["source"]["provenance"]["acceptance"]["mathematical_validity_assessed"] is False
    canonical = {k: v for k, v in run["source"].items() if k != "source_hash"}
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()
    assert digest == run["source_hash"]
    assert execute(client, sid, request).json() == run
    assert len(calls) == 1 and len(run_files()) == 1
    assert client.get(f'/submission-audits/{run["audit_run_id"]}').json() == run
    assert client.get(f"/submissions/{sid}/audits").json() == [run]
    assert persisted_files(folder) == before
    assert "TeacherDecision" not in run_files()[0].read_text()
    assert not any("decision" in str(path) for path in folder.rglob("*"))


@pytest.mark.parametrize("mismatch", ["revision", "acceptance", "submission", "stored_link", "symlink", "invalid_status", "page"])
def test_exact_binding_failures_block_pipeline(setup, mismatch):
    client, calls = setup
    sid, rev = source(client)
    request = accept(client, sid, rev)
    folder = submissions.store().root / sid / "transcriptions" / rev["transcription_id"]
    if mismatch == "revision":
        request["revision_number"] = 2
    elif mismatch == "acceptance":
        request["acceptance_id"] = "acc_" + "0" * 32
    elif mismatch == "submission":
        other_payload = payload()
        snapshot = json.loads(other_payload["snapshot_json"])
        snapshot["local_snapshot_id"] = "snapshot:other"
        other_payload["snapshot_json"] = json.dumps(snapshot)
        sid = client.post("/submissions", json=other_payload).json()["submission_id"]
    elif mismatch in ("stored_link", "symlink"):
        path = folder / "acceptances" / "acceptance_000001.json"
        if mismatch == "symlink":
            target = folder / "outside.json"
            target.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(target)
        else:
            data = json.loads(path.read_text())
            data["transcription_id"] = "tr_" + "0" * 32
            path.write_text(json.dumps(data))
    else:
        path = folder / "revisions" / "revision_000001.json"
        data = json.loads(path.read_text())
        if mismatch == "invalid_status":
            data["status"] = "ACCEPTED"
        else:
            data["segments"][0]["page_index"] = 2
        path.write_text(json.dumps(data))
    assert execute(client, sid, request).status_code == 409
    assert calls == [] and run_files() == []


@pytest.mark.parametrize("name", ["snapshot.json", "page_1.png", "receipt.json", "submission.json"])
def test_original_corruption_blocks_before_engine_and_run(setup, name):
    client, calls = setup
    sid, rev = source(client)
    request = accept(client, sid, rev)
    (submissions.store().root / sid / name).write_bytes(b"changed original")
    response = execute(client, sid, request)
    assert response.status_code == 409
    assert response.json()["detail"] == "A fonte desta análise não passou na verificação de integridade."
    assert response.json()["error_code"] == "SOURCE_INTEGRITY_MISMATCH"
    assert calls == [] and run_files() == []


def test_conversion_sorts_preserves_whitespace_latex_unknown_and_excludes_diagram(setup):
    client, calls = setup
    values = [
        {"segment_id": "d", "page_index": 0, "order": 3, "kind": "diagram", "text": "do not infer x=99"},
        {"segment_id": "u", "page_index": 0, "order": 2, "kind": "unknown", "text": "? 2 + 2 = 5"},
        {"segment_id": "m", "page_index": 0, "order": 1, "kind": "math", "latex": "\\frac{2}{0}=1"},
        {"segment_id": "t", "page_index": 0, "order": 0, "kind": "text", "text": "  aluno\n "},
        {"segment_id": "e", "page_index": 0, "order": 4, "kind": "text"},
    ]
    sid, rev = source(client, values=values)
    run = execute(client, sid, accept(client, sid, rev)).json()
    assert calls[0].solution == "  aluno\n \n\\frac{2}{0}=1\n[Segmento não identificado: u]\n? 2 + 2 = 5\n[Diagrama não analisado: d; página 1]\n[Segmento sem conteúdo: e]"
    assert [item["code"] for item in run["source"]["warnings"]] == ["UNKNOWN_SEGMENT", "DIAGRAM_NOT_ANALYZED", "EMPTY_SEGMENT"]
    assert run["source"]["provenance"]["revision"]["segments"] == rev["segments"]


def test_new_revision_stales_without_mutation_and_new_acceptance_creates_new_run(setup):
    client, calls = setup
    sid, rev = source(client)
    old = execute(client, sid, accept(client, sid, rev)).json()
    path = run_files()[0]
    before = path.read_bytes()
    new_rev = client.post(f'/transcriptions/{rev["transcription_id"]}/revisions', json={
        "based_on_revision_number": 1, "reviewer_reference": "professor-teste-01", "segments": segments("2 + 2 = 5, ainda errado"),
    }).json()
    assert client.get(f'/submission-audits/{old["audit_run_id"]}').json()["stale"] is True
    assert path.read_bytes() == before
    new = execute(client, sid, accept(client, sid, new_rev)).json()
    assert new["revision_number"] == 2 and new["stale"] is False
    assert new["audit_run_id"] != old["audit_run_id"] and new["source_hash"] != old["source_hash"]
    assert path.read_bytes() == before and len(calls) == 2


def test_explicit_execution_key_reruns_and_retries_deduplicate(setup):
    client, calls = setup
    sid, rev = source(client)
    request = accept(client, sid, rev)
    old = execute(client, sid, request).json()
    request["execution_key"] = "explicit-rerun-1"
    new = execute(client, sid, request).json()
    assert new["audit_run_id"] != old["audit_run_id"] and new["source_hash"] == old["source_hash"]
    assert execute(client, sid, request).json() == new and len(calls) == 2


def test_concurrent_double_click_executes_engine_once(setup, monkeypatch):
    client, calls = setup
    sid, rev = source(client)
    request = accept(client, sid, rev)
    entered, release = Event(), Event()
    def engine(req):
        calls.append(req)
        entered.set()
        assert release.wait(5)
        return result(req.problem_id)
    monkeypatch.setattr(main, "execute_audit", engine)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(execute, client, sid, request)
        assert entered.wait(5)
        second = pool.submit(execute, client, sid, request)
        release.set()
        assert first.result().json() == second.result().json()
    assert len(calls) == 1 and len(run_files()) == 1


def test_engine_failure_is_terminal_failure_without_success_result(setup, monkeypatch):
    client, calls = setup
    sid, rev = source(client)
    request = accept(client, sid, rev)
    def failed(req):
        calls.append(req)
        raise RuntimeError("private provider diagnostic")
    monkeypatch.setattr(main, "execute_audit", failed)
    run = execute(client, sid, request).json()
    assert run["status"] == "FAILED" and run["result"] is None and run["artifact_dir"] is None
    assert run["error_code"] == "AUDITOR_FAILED"
    assert "private provider" not in run_files()[0].read_text()
    assert execute(client, sid, request).json() == run and len(calls) == 1


def test_change_during_engine_blocks_publication(setup, monkeypatch):
    client, _ = setup
    sid, rev = source(client)
    request = accept(client, sid, rev)
    def engine(req):
        (submissions.store().root / sid / "page_1.png").write_bytes(b"changed while running")
        return result(req.problem_id)
    monkeypatch.setattr(main, "execute_audit", engine)
    assert execute(client, sid, request).status_code == 409
    assert run_files() == []


@pytest.mark.parametrize("extra", ["solution", "segments", "problem_id", "source_hash"])
def test_ui_content_cannot_replace_persisted_source(setup, extra):
    client, calls = setup
    sid, rev = source(client)
    request = accept(client, sid, rev)
    assert execute(client, sid, {**request, extra: "injected"}).status_code == 422
    assert calls == []


def test_legacy_audit_calls_same_engine_without_bridge_metadata(setup):
    client, calls = setup
    response = client.post("/audit", json={"problem_id": "ITA2025Q1", "solution": "2 + 2 = 5"})
    assert response.status_code == 200
    assert calls[0].solution == "2 + 2 = 5" and run_files() == []
    assert "source" not in response.json()


def test_bridge_contains_no_duplicate_lean_claim_or_rubric_pipeline():
    source_text = "\n".join(path.read_text() for path in Path(audits.__file__).parent.glob("*.py"))
    for forbidden in ("run_lean_file", "evaluate_formal_steps", "extract_claims(", "evaluate_rubric(", "httpx"):
        assert forbidden not in source_text


def test_acceptance_of_another_existing_revision_is_rejected(setup):
    client, calls = setup
    sid, rev = source(client)
    old = accept(client, sid, rev)
    second = client.post(f'/transcriptions/{rev["transcription_id"]}/revisions', json={
        "based_on_revision_number": 1, "reviewer_reference": "professor-teste-01", "segments": segments(),
    }).json()
    accept(client, sid, second)
    assert execute(client, sid, {**old, "revision_number": 2}).status_code == 409
    assert calls == [] and run_files() == []


def test_artificial_recognition_requires_acceptance_and_preserves_provenance(setup, monkeypatch):
    client, calls = setup
    monkeypatch.setenv("CONFIA_ENV", "test")
    sid = client.post("/submissions", json=payload()).json()["submission_id"]
    recognition = client.post(f"/submissions/{sid}/recognitions", json={
        "provider": "fake_test", "idempotency_key": "bridge-test",
    }).json()
    tid = recognition["transcription_id"]
    rev = client.get(f"/transcriptions/{tid}").json()["revisions"][0]
    request = {"transcription_id": tid, "revision_number": 1, "acceptance_id": "acc_" + "0" * 32}
    assert execute(client, sid, request).status_code == 409 and calls == []
    run = execute(client, sid, accept(client, sid, rev)).json()
    assert run["status"] == "COMPLETED"
    assert run["source"]["provenance"]["revision"]["provider"] == "fake_test"
    assert run["source"]["provenance"]["revision"]["provenance"] == rev["provenance"]


def test_new_transcription_stales_historical_run_without_rewriting_it(setup):
    client, _ = setup
    sid, rev = source(client)
    old = execute(client, sid, accept(client, sid, rev)).json()
    path = run_files()[0]
    before = path.read_bytes()
    client.post(f"/submissions/{sid}/transcriptions", json={
        "reviewer_reference": "professor-teste-01", "segments": segments(),
    })
    assert client.get(f'/submission-audits/{old["audit_run_id"]}').json()["stale"] is True
    assert path.read_bytes() == before


def test_tampered_persisted_hash_is_not_returned_as_a_valid_run(setup):
    client, _ = setup
    sid, rev = source(client)
    run = execute(client, sid, accept(client, sid, rev)).json()
    path = run_files()[0]
    data = json.loads(path.read_text())
    data["source"]["solution_text"] = "2 + 2 = 4"
    path.write_text(json.dumps(data))
    assert client.get(f'/submission-audits/{run["audit_run_id"]}').status_code == 409
    assert client.get(f"/submissions/{sid}/audits").status_code == 409


def test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(tmp_path / "audits"))
    client = TestClient(main.app)
    solution = "x^57=1; x^14=1-x; x^7=-x. Logo a=1 e b=1.\n2 + 2 = 5"
    request_payload = payload()
    sid, rev = source(client, values=[{"segment_id": "wrong", "page_index": 0, "order": 0,
                                     "kind": "mixed", "text": solution}], request_payload=request_payload)
    request = accept(client, sid, rev)
    folder = submissions.store().root / sid
    before = persisted_files(folder)
    response = execute(client, sid, request)
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["status"] == "COMPLETED", run
    internal = persisted_run(run)
    assert Path(internal["artifact_dir"], "solution.txt").read_text() == solution
    assert run["result"]["student_claim_checks"]
    assert any(item["status"] == "refuted" for item in run["result"]["student_claim_checks"])
    assert run["result"]["score"] is None
    assert run["result"]["verdict"] == "inconclusivo"
    assert any(item["mathematical_status"] == "refuted" for item in run["result"]["rubric_assessment"]["items"])
    # Public references are relative identifiers, not paths resolved against cwd.
    public_lean_file = run["result"]["lean_certificate"]["lean_file"]
    assert isinstance(public_lean_file, str) and public_lean_file
    public_path = Path(public_lean_file)
    assert not public_path.is_absolute() and ".." not in public_path.parts
    assert "\\" not in public_lean_file and ":" not in public_lean_file
    assert_no_local_paths(public_lean_file)

    # Locate the physical certificate exclusively from the persisted record.
    artifact_root = Path(internal["artifact_dir"])
    internal_lean_file = Path(internal["result"]["lean_certificate"]["lean_file"])
    assert artifact_root.is_absolute() and internal_lean_file.is_absolute()
    assert ".." not in internal_lean_file.parts
    assert internal_lean_file.relative_to(artifact_root).as_posix() == public_lean_file
    resolved_certificate = internal_lean_file.resolve(strict=True)
    resolved_certificate.relative_to(artifact_root.resolve(strict=True))
    assert resolved_certificate.is_file()
    assert persisted_files(folder) == before
