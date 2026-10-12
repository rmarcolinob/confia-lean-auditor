"""GOV-01 public boundary: real HTTP routes, controlled engines, temp storage."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

import pytest
from fastapi import HTTPException

import confia_lean_auditor.main as main
from confia_lean_auditor.core.public_audit import (
    HIDDEN_LOCAL_PATH, PublicReproducibilityMetadata,
    sanitize_public_payload, sanitize_public_text,
)
from confia_lean_auditor.reproducibility import collector, service
from confia_lean_auditor.reproducibility.canonical import canonical_bytes
from confia_lean_auditor.submission_audits import router as audits
from confia_lean_auditor.submissions.integrity import model_sha256
from test_reproducibility import project, pipeline, PROBLEM
from test_submission_audits import source, accept, execute, persisted_run
from test_submissions import payload
from test_cap04_global_semantics import step
from public_privacy import assert_no_local_paths


EMBEDDED_PATHS = [
    "[/Users/teste/projeto/.venv/lib/diagnostic]",
    "(/Users/teste/projeto/file)",
    '"path=/Users/teste/projeto/file"',
    "erro em /home/aluno/confia/file",
    r"C:\Users\Aluno\confia\file",
    r"error=[C:\private\file]",
    "file:///Users/aluno/confia/file",
    "prefixo [/private/tmp/foo] sufixo",
    "arquivos=[/tmp/foo, /home/aluno/confia/file]",
    "erro em /Users/Aluno Com Espaços/confia/private file.txt",
    "arquivo={/custom-root/project/diagnostic}",
    r"erro \\server\private\diagnostic",
]


@pytest.mark.parametrize("value", EMBEDDED_PATHS)
def test_embedded_text_is_fully_hidden(value):
    assert sanitize_public_text(value) == HIDDEN_LOCAL_PATH
    assert_no_local_paths(sanitize_public_text(value))


@pytest.mark.parametrize("value", ["1.2.3", "leanprover/lean4:v4.28.0", "formal_steps/foo.lean",
                                     "a/b + 2/3", "x / y", "SHA-256", "https://example.org/docs"])
def test_nonlocal_text_and_math_remain_unchanged(value):
    assert sanitize_public_text(value) == value


def test_recursive_projection_does_not_mutate_input_or_drop_colliding_keys():
    value = {"a": {"b": [f"texto {EMBEDDED_PATHS[0]}", (EMBEDDED_PATHS[4], 3, None, True)]},
        **{name: [{"nested": {"value": EMBEDDED_PATHS[index]}}] for index, name in enumerate((
            "warnings", "errors", "feedback", "formal_steps", "required_artifacts", "reproducibility"))},
        "/Users/private/key": "first", "/home/private/key": "second"}
    original = deepcopy(value)
    result = sanitize_public_payload(value)
    assert_no_local_paths(result)
    assert value == original and result is not value and result["a"] is not value["a"]
    assert result["a"]["b"][1] == [HIDDEN_LOCAL_PATH, 3, None, True]
    assert len(result) == len(value)
    assert "first" in result.values() and "second" in result.values()


def snapshot_files(root):
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("private", EMBEDDED_PATHS)
def test_every_http_route_projects_complete_payload_and_keeps_internal_hashes(pipeline, project, monkeypatch, caplog, private):
    original_engine = main.execute_audit
    monkeypatch.setattr(collector.platform, "release", lambda: private)
    def engine(request):
        value = original_engine(request)
        value.feedback = private
        value.pedagogical_report.summary = private
        value.pedagogical_report.attention_points = [private]
        value.lean_certificate.stderr = private
        witness = Path(value.artifact_dir, "formal_steps", "privacy.lean")
        witness.parent.mkdir(exist_ok=True)
        witness.write_text("controlled witness")
        formal = step(witness)
        formal.description = private
        formal.id = private  # Also exercise required_artifacts[*].relation_id.
        value.formal_steps.append(formal)
        value.student_claim_checks.append({"id": "private-diagnostic", "status": "unverified",
            "lean_file": "/Users/teste/not-an-authorized-artifact", "nested": {"warnings": [private], "errors": [private]}})
        Path(value.artifact_dir, "audit.json").write_text(value.model_dump_json())
        return value
    monkeypatch.setattr(main, "execute_audit", engine)
    body = payload()
    submission = json.loads(body["snapshot_json"])
    submission["problem_id"] = PROBLEM
    body["snapshot_json"] = json.dumps(submission)
    sid, revision = source(pipeline, request_payload=body)
    request = accept(pipeline, sid, revision)
    textual = pipeline.post("/audit", json={"problem_id": PROBLEM, "solution": "x=1"})
    first = execute(pipeline, sid, request)
    assert textual.status_code == first.status_code == 200
    run = first.json()
    assert run["status"] == "COMPLETED", run
    before = snapshot_files(project)
    stored = persisted_run(run)
    responses = [textual, first, pipeline.get(f'/submission-audits/{run["audit_run_id"]}'),
        pipeline.get(f'/submissions/{sid}/audits'), execute(pipeline, sid, request),
        pipeline.get(f'/submission-audits/{run["audit_run_id"]}/reproducibility')]
    for response in responses:
        assert response.status_code == 200, response.text
        assert_no_local_paths(response.json(), private_roots=[project])
        assert response.headers["Cache-Control"] == "no-store"
    metadata = PublicReproducibilityMetadata.model_validate(responses[-1].json())
    assert metadata.model_dump(mode="json") == run["result"]["reproducibility"]
    assert metadata.status == "recorded" and metadata.integrity_scope == "persisted_internal_record"
    assert metadata.record.manifest.python_environment.release == HIDDEN_LOCAL_PATH
    assert metadata.public_warnings == ["LOCAL_REFERENCE_WITHHELD"]
    assert run["result"]["feedback"] == HIDDEN_LOCAL_PATH
    assert "formal_steps/privacy.lean" in {a["file"] for a in run["required_artifacts"]}
    internal = audits.service()._read(run["audit_run_id"])
    assert service.verify(internal.result.reproducibility, internal.artifact_dir).status == "recorded"
    assert stored["result"]["feedback"] == private
    assert stored["result"]["reproducibility"]["record"]["manifest"]["python_environment"]["release"] == private
    assert run["result_sha256"] == model_sha256(internal.result)
    assert metadata.record.manifest_sha256 == stored["reproducibility_manifest_sha256"]
    assert hashlib.sha256(canonical_bytes(metadata.record.manifest)).hexdigest() != metadata.record.manifest_sha256
    assert snapshot_files(project) == before  # Includes acceptance, manifests, dependencies and all artifact hashes.
    assert private not in caplog.text and str(project) not in caplog.text
    if private == EMBEDDED_PATHS[0]:
        # Feed an actual projected HTTP payload into the teacher renderer,
        # without writing an intermediate file or starting a browser/server.
        script = r'''
const assert = require('node:assert/strict');
const {page} = require('./tests/js/workspace-dom.cjs');
const {element} = require('./tests/js/ui-dom.cjs');
const data = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
(async () => {
  const ui = await page(), panel = element('div');
  ui.window.ConfIAReport.render(data, panel, {context:'teacher'});
  assert(!/\/Users\/|\/home\/|\/private\/|\/tmp\/|file:\/\/|[A-Za-z]:[\\/]/.test(panel.textContent));
  assert(panel.textContent.includes('[local path hidden]'));
  assert(panel.textContent.includes('registro interno'));
})().catch(error => { console.error(error); process.exitCode = 1; });
'''
        rendered = subprocess.run(["node", "-e", script], input=json.dumps(run["result"]),
            text=True, capture_output=True, cwd=Path(__file__).resolve().parents[1], timeout=15)
        assert rendered.returncode == 0, rendered.stderr


@pytest.mark.parametrize("filename", ["rubric.json", "problem.json", "microclaims.json"])
def test_missing_asset_error_is_fixed_and_safe(pipeline, project, caplog, filename):
    (project / "problems" / PROBLEM / filename).unlink()
    response = pipeline.post("/audit", json={"problem_id": PROBLEM, "solution": "x=1"})
    assert response.status_code == 400
    assert response.json() == {
        "error_code": "REQUIRED_PROBLEM_ASSET_MISSING",
        "message": "Um arquivo obrigatório da questão não está disponível.",
        "detail": "Um arquivo obrigatório da questão não está disponível.",
    }
    assert_no_local_paths(response.json(), private_roots=[project])
    assert str(project) not in caplog.text and "Traceback" not in response.text


def test_invalid_asset_error_does_not_echo_validator_input(pipeline, project, caplog):
    (project / "problems" / PROBLEM / "rubric.json").write_text("[/Users/teste/private invalid json")
    response = pipeline.post("/audit", json={"problem_id": PROBLEM, "solution": "x=1"})
    assert response.status_code == 400 and response.json()["error_code"] == "INVALID_PROBLEM_ASSET"
    assert_no_local_paths(response.json(), private_roots=[project])
    assert "private invalid json" not in response.text + caplog.text


@pytest.mark.parametrize("error,status", [(RuntimeError("TOKEN=fake-secret [/Users/private/data]"), 500),
                                           (HTTPException(503, "PASSWORD=fake-secret /home/private/data"), 503)])
def test_unmapped_exception_uses_generic_message_and_category_only_log(pipeline, monkeypatch, caplog, error, status):
    def fail(*args):
        raise error
    monkeypatch.setattr(main, "execute_audit", fail)
    response = pipeline.post("/audit", json={"problem_id": PROBLEM, "solution": "x=1"})
    assert response.status_code == status
    assert response.json()["message"] == "Não foi possível concluir a operação."
    assert response.json()["error_code"] == "AUDIT_OPERATION_FAILED"
    assert_no_local_paths(response.json())
    assert "fake-secret" not in response.text + caplog.text
    assert "AUDIT_OPERATION_FAILED" in caplog.text


def test_validation_and_method_errors_before_endpoint_are_safe(pipeline):
    for response in (pipeline.post("/audit", json={"problem_id": "/Users/private/data", "solution": []}),
                     pipeline.post("/submissions/sub_missing/audits", json={"revision_number": "/home/private/data"})):
        assert response.status_code == 422
        assert response.json()["error_code"] == "INVALID_AUDIT_REQUEST"
        assert_no_local_paths(response.json())
    response = pipeline.get("/audit")
    assert response.status_code == 405
    assert_no_local_paths(response.json())


def test_gov_endpoint_advertises_public_dto_in_openapi(pipeline):
    spec = pipeline.get("/openapi.json").json()
    schema = spec["paths"]["/submission-audits/{audit_run_id}/reproducibility"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["$ref"].endswith("/PublicReproducibilityMetadata")
    assert "integrity_scope" in spec["components"]["schemas"]["PublicReproducibilityMetadata"]["properties"]
