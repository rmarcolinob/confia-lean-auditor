"""Public privacy and domain errors: no Lean or production artifact writes."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import confia_lean_auditor.main as main
from confia_lean_auditor.core.public_audit import public_projection
from confia_lean_auditor.reproducibility.schemas import IdentifiedValue, MANIFEST_FILENAME, DEPENDENCIES_FILENAME
from confia_lean_auditor.submission_audits import router as audits
from confia_lean_auditor.submissions.integrity import model_sha256
from test_submission_audits import setup, source, accept, execute, result, persisted_run
from test_reproducibility import project, pipeline, pair
from public_privacy import assert_no_local_paths

PRIVATE_PATHS = ["/Users/teste/projeto/Attempt.lean", "/home/teste/projeto/Attempt.lean",
                 r"C:\Users\teste\projeto\Attempt.lean", "file:///Users/teste/Attempt.lean"]


@pytest.mark.parametrize("private", PRIVATE_PATHS)
def test_all_public_routes_hide_internal_paths(setup, monkeypatch, caplog, private):
    client, _ = setup
    def engine(request):
        value = result(request.problem_id)
        value.lean_certificate.stdout = f"compiler at {private}"
        value.lean_certificate.stderr = private
        value.student_claim_checks = [{"status": "unverified", "lean_file": private,
            "refutation_lean_file": private, "diagnostic": f"failure: {private}"}]
        Path(value.artifact_dir, "audit.json").write_text(value.model_dump_json())
        return value
    monkeypatch.setattr(main, "execute_audit", engine)
    sid, revision = source(client)
    request = accept(client, sid, revision)
    first = execute(client, sid, request)
    assert first.status_code == 200, first.text
    run = first.json()
    stored = persisted_run(run)
    before = audits.service()._path(run["audit_run_id"]).read_bytes()
    assert stored["result"]["student_claim_checks"][0]["lean_file"] == private
    assert run["artifact_dir"] is None and run["result"]["artifact_dir"] is None
    assert run["artifact_ref"] == f'audit-run:{run["audit_run_id"]}'
    assert run["integrity_scope"] == "persisted_internal_record"
    assert run["result"]["lean_certificate"]["lean_file"] == "Attempt.lean"
    assert run["result"]["student_claim_checks"][0]["lean_file"] is None
    assert public_projection({"lean_certificate": {"lean_file": private}}, stored["artifact_dir"])["lean_certificate"]["lean_file"] is None
    assert "ARTIFACT_REFERENCE_UNAVAILABLE" in run["public_warnings"]
    assert "audit.json" in {item["file"] for item in run["required_artifacts"]}
    assert run["result_sha256"] == model_sha256(main.AuditResponse.model_validate(stored["result"]))
    responses = [first, client.get(f'/submission-audits/{run["audit_run_id"]}'),
                 client.get(f'/submissions/{sid}/audits'), execute(client, sid, request),
                 client.get(f'/submission-audits/{run["audit_run_id"]}/reproducibility'),
                 client.post('/audit', json={"problem_id": stored["problem_id"], "solution": "x=1"})]
    for response in responses:
        assert response.status_code == 200, response.text
        assert_no_local_paths(response.json(), private_roots=[stored["artifact_dir"]])
        text = json.dumps(response.json(), ensure_ascii=False)
        for secret in (private, str(stored["artifact_dir"]), "/Users/", "/home/", "file://", "C:\\"):
            assert secret not in text
        assert json.dumps(private)[1:-1] not in text
    assert private not in caplog.text
    assert audits.service()._path(run["audit_run_id"]).read_bytes() == before


@pytest.mark.parametrize("kind", ["outside", "traversal", "symlink", "missing"])
def test_unsafe_reference_never_becomes_a_valid_basename(tmp_path, kind):
    root = tmp_path / "artifacts"
    root.mkdir()
    outside = tmp_path / "secret.lean"
    outside.write_text("secret")
    path = str(outside)
    if kind == "traversal":
        path = "../secret.lean"
    elif kind == "symlink":
        link = root / "formal_steps"
        link.symlink_to(tmp_path, target_is_directory=True)
        path = str(link / "secret.lean")
    elif kind == "missing":
        path = str(root / "missing.lean")
    public = public_projection({"lean_file": path}, str(root))
    assert public["lean_file"] is None
    assert public["public_warnings"] == ["ARTIFACT_REFERENCE_UNAVAILABLE"]


def test_relative_references_preserve_subdirectories_and_manifest_binding(tmp_path):
    paths = ["formal_steps/same.lean", "student_proofs/same.lean"]
    for relative in paths:
        path = tmp_path / relative
        path.parent.mkdir()
        path.write_text(relative)
    raw = {"formal_steps": [{"lean_file": str(tmp_path / paths[0])}],
           "required_artifacts": [{"relation_id": path, "file": str(tmp_path / path)} for path in paths]}
    public = public_projection(raw, str(tmp_path))
    assert [item["file"] for item in public["required_artifacts"]] == paths
    assert public["formal_steps"][0]["lean_file"] == public["required_artifacts"][0]["file"]
    assert public["public_warnings"] == []
    assert public_projection({"lean_file": paths[0]}, str(tmp_path))["lean_file"] == paths[0]
    assert raw["formal_steps"][0]["lean_file"] == str(tmp_path / paths[0])


@pytest.mark.parametrize("target", ["binding_hash", "binding_filename", "record_hash", "record_filename",
                                     "dependency_hash", "manifest", "dependencies"])
def test_metadata_tampering_has_own_safe_domain_error(pipeline, target, caplog):
    sid, request, run = pair(pipeline)
    path = audits.service()._path(run["audit_run_id"])
    stored = persisted_run(run)
    if target in {"manifest", "dependencies"}:
        Path(stored["artifact_dir"], MANIFEST_FILENAME if target == "manifest" else DEPENDENCIES_FILENAME).write_bytes(b"tampered")
    else:
        if target.startswith("binding"):
            field = "reproducibility_manifest_sha256" if target.endswith("hash") else "reproducibility_manifest_filename"
            stored[field] = "0" * 64 if target.endswith("hash") else PRIVATE_PATHS[0]
        else:
            record = stored["result"]["reproducibility"]["record"]
            if target == "dependency_hash":
                record["manifest"]["python_environment"]["dependency_manifest_sha256"] = "0" * 64
            else:
                record["manifest_sha256" if target.endswith("hash") else "filename"] = "0" * 64 if target.endswith("hash") else PRIVATE_PATHS[0]
        path.write_text(json.dumps(stored))
    before = path.read_bytes()
    responses = [pipeline.get(f'/submission-audits/{run["audit_run_id"]}'),
        pipeline.get(f'/submissions/{sid}/audits'), execute(pipeline, sid, request),
        pipeline.get(f'/submission-audits/{run["audit_run_id"]}/reproducibility')]
    for response in responses:
        assert response.status_code == 409
        assert_no_local_paths(response.json())
        assert response.json() == {"detail": "Não foi possível validar a integridade dos metadados desta análise.",
                                   "error_code": "REPRODUCIBILITY_INTEGRITY_MISMATCH"}
        assert response.headers["cache-control"] == "no-store"
    assert path.read_bytes() == before and PRIVATE_PATHS[0] not in caplog.text


@pytest.mark.parametrize("field,code", [("result_sha256", "RESULT_INTEGRITY_MISMATCH"),
    ("source_hash", "SOURCE_INTEGRITY_MISMATCH"), ("execution_key", "AUDIT_RUN_CONFLICT")])
def test_other_integrity_domains_remain_distinct(setup, field, code):
    client, _ = setup
    sid, revision = source(client)
    request = accept(client, sid, revision)
    run = execute(client, sid, request).json()
    stored = persisted_run(run)
    stored[field] = "0" * 64
    audits.service()._path(run["audit_run_id"]).write_text(json.dumps(stored))
    for response in (client.get(f'/submission-audits/{run["audit_run_id"]}'), execute(client, sid, request)):
        assert response.status_code == 409
        assert response.json()["error_code"] == code


def test_unaccepted_and_revision_conflict_have_distinct_codes(setup):
    client, _ = setup
    sid, revision = source(client)
    request = dict(transcription_id=revision["transcription_id"], revision_number=1, acceptance_id="acc_" + "0" * 32)
    assert execute(client, sid, request).json()["error_code"] == "TRANSCRIPTION_NOT_ACCEPTED"
    request = accept(client, sid, revision)
    response = execute(client, sid, {**request, "revision_number": 999})
    assert response.status_code == 409 and response.json()["error_code"] == "REVISION_CONFLICT"
    response = client.post(f'/transcriptions/{revision["transcription_id"]}/accept', json={
        "revision_number": 1, "reviewer_reference": "professor"})
    assert response.status_code == 409 and response.json()["error_code"] == "REVISION_CONFLICT"


@pytest.mark.parametrize("value", ["", " ", "\t\n", None])
def test_identified_value_rejects_missing_available_value(value):
    with pytest.raises(ValidationError):
        IdentifiedValue(value=value, metadata_source="package", reason=None)


def test_identified_value_preserves_valid_and_unavailable_contracts():
    assert IdentifiedValue().value is None
    assert IdentifiedValue(value="1.2.3", metadata_source="package", reason=None).value == "1.2.3"
    # Do not normalize already recorded values and thus change historical hashes.
    assert IdentifiedValue(value=" 1.2.3 ", metadata_source="package", reason=None).value == " 1.2.3 "
    for data in ({"value": "1.2.3"}, {"value": None, "reason": None},
                 {"value": "1.2.3", "metadata_source": "package", "reason": "not_available"}):
        with pytest.raises(ValidationError):
            IdentifiedValue(**data)
