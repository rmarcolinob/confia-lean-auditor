"""Manual transcription only; acceptance is not mathematical correction or audit."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from confia_lean_auditor.main import app
from confia_lean_auditor.submissions import router
from confia_lean_auditor.submissions import body_limit
from confia_lean_auditor.submissions.schemas import (
    CreateTranscriptionRequest,
    TranscriptionSegment,
)
from confia_lean_auditor.submissions.store import SubmissionStore
from test_submissions import payload


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    return TestClient(app)


def segments(math="2 + 2 = 5"):
    return [
        {"segment_id": "seg:text", "page_index": 0, "order": 0, "kind": "text", "text": "Cálculo do aluno"},
        {"segment_id": "seg:math", "page_index": 0, "order": 1, "kind": "math", "latex": math},
        {"segment_id": "seg:mixed", "page_index": 0, "order": 2, "kind": "mixed", "text": "logo", "latex": "x=1"},
    ]


def create_submission(client):
    response = client.post("/submissions", json=payload())
    assert response.status_code == 201
    return response.json()["submission_id"]


def create_transcription(client, submission_id, values=None):
    response = client.post(
        f"/submissions/{submission_id}/transcriptions",
        json={
            "source": "manual",
            "reviewer_reference": "professor-teste-01",
            "reviewer_identity_verified": False,
            "segments": values or segments(),
            "status": "NEEDS_REVIEW",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_manual_transcription_contract_kinds_optional_confidence_and_extra_fields(client):
    submission_id = create_submission(client)
    revision = create_transcription(client, submission_id)
    assert revision["revision_number"] == 1
    assert revision["based_on_revision_number"] is None
    assert revision["source"] == "manual"
    assert revision["recognizer"] is None and revision["recognizer_version"] is None
    assert [item["kind"] for item in revision["segments"]] == ["text", "math", "mixed"]
    assert all(item["confidence"] is None for item in revision["segments"])
    assert all(item["source_region"] is None for item in revision["segments"])
    assert all(item["source_stroke_refs"] is None for item in revision["segments"])

    with pytest.raises(ValidationError):
        TranscriptionSegment.model_validate({**segments()[0], "score": 10})
    with pytest.raises(ValidationError):
        CreateTranscriptionRequest.model_validate({
            "reviewer_reference": "professor-teste-01", "segments": segments(), "verdict": "correct",
        })
    invalid = client.post(
        f"/submissions/{submission_id}/transcriptions",
        json={"reviewer_reference": "professor-teste-01", "segments": segments(), "extra": True},
    )
    assert invalid.status_code == 422


def test_second_revision_preserves_first_and_history_after_store_restart(client):
    submission_id = create_submission(client)
    first = create_transcription(client, submission_id)
    corrected = segments("2 + 2 = 5")
    corrected[0]["text"] = "Cálculo manuscrito do aluno"
    response = client.post(
        f'/transcriptions/{first["transcription_id"]}/revisions',
        json={
            "based_on_revision_number": 1,
            "reviewer_reference": "professor-teste-01",
            "reviewer_identity_verified": False,
            "change_type": "reading_correction",
            "change_reason": "Corrige somente uma palavra lida incorretamente.",
            "segments": corrected,
            "status": "NEEDS_REVIEW",
        },
    )
    assert response.status_code == 201, response.text
    second = response.json()
    assert second["revision_number"] == 2 and second["based_on_revision_number"] == 1
    assert second["segments"][1]["latex"] == "2 + 2 = 5"

    history = client.get(f'/transcriptions/{first["transcription_id"]}').json()
    assert [item["revision_number"] for item in history["revisions"]] == [1, 2]
    assert history["revisions"][0]["segments"][0]["text"] == "Cálculo do aluno"
    assert history["revisions"][1]["segments"][0]["text"] == "Cálculo manuscrito do aluno"
    restarted = SubmissionStore(router.store().root).transcription_history(first["transcription_id"])
    assert [item.revision_number for item in restarted.revisions] == [1, 2]


def test_acceptance_means_fidelity_and_keeps_false_mathematics_verbatim(client):
    submission_id = create_submission(client)
    first = create_transcription(client, submission_id)
    response = client.post(
        f'/transcriptions/{first["transcription_id"]}/accept',
        json={
            "revision_number": 1,
            "reviewer_reference": "professor-teste-01",
            "reviewer_identity_verified": False,
            "acceptance_note": "Conferida visualmente com o manuscrito.",
        },
    )
    assert response.status_code == 200, response.text
    accepted = response.json()
    assert accepted["revision"]["status"] == "ACCEPTED"
    assert accepted["revision"]["segments"][1]["latex"] == "2 + 2 = 5"
    assert accepted["acceptance"]["meaning"] == "faithful_representation_of_manuscript_only"
    assert accepted["acceptance"]["mathematical_validity_assessed"] is False
    serialized = str(accepted).lower()
    assert not any(name in serialized for name in ("score", "verdict", "grade", "rubric", "lean"))

    history = client.get(f'/transcriptions/{first["transcription_id"]}').json()
    assert history["revisions"][0]["status"] == "ACCEPTED"
    assert len(history["acceptances"]) == 1
    listing = client.get(f"/submissions/{submission_id}/transcriptions").json()
    assert listing[0]["latest_revision"]["status"] == "ACCEPTED"


def test_missing_resources_conflicts_and_submission_binding(client):
    assert client.post(
        "/submissions/sub_" + "0" * 32 + "/transcriptions",
        json={"reviewer_reference": "professor-teste-01", "segments": segments()},
    ).status_code == 404
    assert client.get("/transcriptions/tr_" + "0" * 32).status_code == 404
    submission_id = create_submission(client)
    first = create_transcription(client, submission_id)
    stale = client.post(
        f'/transcriptions/{first["transcription_id"]}/revisions',
        json={"based_on_revision_number": 9, "reviewer_reference": "professor-teste-01", "segments": segments()},
    )
    assert stale.status_code == 409
    invalid_page = segments()
    invalid_page[0]["page_index"] = 2
    assert client.post(
        f'/transcriptions/{first["transcription_id"]}/revisions',
        json={"based_on_revision_number": 1, "reviewer_reference": "professor-teste-01", "segments": invalid_page},
    ).status_code == 422


def test_original_snapshot_and_png_remain_byte_identical_and_flow_never_audits(client, monkeypatch):
    submission_id = create_submission(client)
    folder = router.store().root / submission_id
    before = {name: (folder / name).read_bytes() for name in ("snapshot.json", "page_1.png")}

    def forbidden(*args, **kwargs):
        raise AssertionError("No Lean execution or mathematical audit is authorized")

    import confia_lean_auditor.main as main
    monkeypatch.setattr(main, "run_lean_file", forbidden)
    first = create_transcription(client, submission_id)
    client.post(
        f'/transcriptions/{first["transcription_id"]}/accept',
        json={"revision_number": 1, "reviewer_reference": "professor-teste-01"},
    )
    assert {name: (folder / name).read_bytes() for name in before} == before
    sources = "\n".join(path.read_text() for path in Path(router.__file__).parent.glob("*.py"))
    assert "run_lean" not in sources and '"/audit"' not in sources


def original_hashes(folder):
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in folder.iterdir() if path.is_file()}


def persisted_files(folder):
    return {str(path.relative_to(folder)): path.read_bytes()
            for path in folder.rglob("*") if path.is_file()}


def mutation_request(operation, submission_id, transcription_id=None):
    if operation == "create":
        return f"/submissions/{submission_id}/transcriptions", {
            "reviewer_reference": "professor-teste-01", "segments": segments(),
        }
    if operation == "revision":
        return f"/transcriptions/{transcription_id}/revisions", {
            "based_on_revision_number": 1,
            "reviewer_reference": "professor-teste-01", "segments": segments(),
        }
    return f"/transcriptions/{transcription_id}/accept", {
        "revision_number": 1, "reviewer_reference": "professor-teste-01",
    }


@pytest.mark.parametrize("operation", ["create", "revision", "accept"])
@pytest.mark.parametrize("corruption", [
    "png_changed", "snapshot_changed", "png_missing", "snapshot_missing",
    "metadata_mismatch", "page_refs_inconsistent", "invalid_snapshot_structure", "receipt_missing",
    "submission_missing", "snapshot_binding_inconsistent",
])
def test_integrity_conflict_blocks_every_mutation_without_publishing(client, operation, corruption):
    receipt = client.post("/submissions", json=payload(2)).json()
    submission_id = receipt["submission_id"]
    folder = router.store().root / submission_id
    first = create_transcription(client, submission_id) if operation != "create" else None
    if corruption == "png_changed":
        # Verify every expected PNG, including one other than the first page.
        (folder / "page_2.png").write_bytes(b"tampered PNG")
    elif corruption == "snapshot_changed":
        (folder / "snapshot.json").write_bytes(b"tampered snapshot")
    elif corruption == "png_missing":
        (folder / "page_2.png").unlink()
    elif corruption == "snapshot_missing":
        (folder / "snapshot.json").unlink()
    elif corruption == "receipt_missing":
        (folder / "receipt.json").unlink()
    elif corruption == "submission_missing":
        (folder / "submission.json").unlink()
    elif corruption == "metadata_mismatch":
        record = json.loads((folder / "submission.json").read_bytes())
        record["snapshot_id"] = "snapshot:different"
        (folder / "submission.json").write_text(json.dumps(record))
    else:
        record = json.loads((folder / "submission.json").read_bytes())
        if corruption == "snapshot_binding_inconsistent":
            record["snapshot_id"] = "snapshot:wrong-binding"
        elif corruption == "page_refs_inconsistent":
            record["page_images"][1]["page_id"] = "page:nonexistent"
        else:
            raw = b'{}'
            (folder / "snapshot.json").write_bytes(raw)
            record["snapshot"]["sha256"] = hashlib.sha256(raw).hexdigest()
            record["snapshot"]["size_bytes"] = len(raw)
        # Even internally matching metadata must describe a coherent snapshot graph.
        (folder / "submission.json").write_text(json.dumps(record))
        (folder / "receipt.json").write_text(json.dumps({**record, "receipt_version": "1.0"}))

    before = persisted_files(folder)
    url, body = mutation_request(operation, submission_id, first["transcription_id"] if first else None)
    response = client.post(url, json=body)
    assert response.status_code == 409, response.text
    assert "Integridade" in response.json()["detail"]
    assert persisted_files(folder) == before  # No repairs, partial or complete new publications.
    assert not list(folder.rglob("*.pending"))
    assert not list(folder.glob("transcriptions/.pending-*"))
    if corruption in {"png_changed", "snapshot_changed", "png_missing", "snapshot_missing"}:
        detail = client.get(f"/submissions/{submission_id}")
        assert detail.status_code == 200
        assert not all(item["matches"] for item in detail.json()["integrity"])
        if first:
            assert client.get(f'/transcriptions/{first["transcription_id"]}').status_code == 200


@pytest.mark.parametrize("third_status", ["DRAFT", "NEEDS_REVIEW"])
def test_accepted_second_revision_survives_third_revision_and_restart(client, third_status):
    receipt = client.post("/submissions", json=payload(2)).json()
    submission_id = receipt["submission_id"]
    folder = router.store().root / submission_id
    hashes = original_hashes(folder)
    first = create_transcription(client, submission_id)
    assert original_hashes(folder) == hashes
    transcription_id = first["transcription_id"]
    url, body = mutation_request("revision", submission_id, transcription_id)
    second_response = client.post(url, json=body)
    assert second_response.status_code == 201
    assert original_hashes(folder) == hashes
    transcription_folder = folder / "transcriptions" / transcription_id
    old_revisions = persisted_files(transcription_folder / "revisions")

    accept_url, accept_body = mutation_request("accept", submission_id, transcription_id)
    accept_body["revision_number"] = 2
    accepted_response = client.post(accept_url, json=accept_body)
    assert accepted_response.status_code == 200
    acceptance = accepted_response.json()["acceptance"]
    assert acceptance["revision_number"] == 2
    assert acceptance["meaning"] == "faithful_representation_of_manuscript_only"
    assert acceptance["mathematical_validity_assessed"] is False
    assert original_hashes(folder) == hashes
    assert persisted_files(transcription_folder / "revisions") == old_revisions
    acceptance_files = persisted_files(transcription_folder / "acceptances")

    before_conflict = persisted_files(folder)
    stale = client.post(url, json=body)  # Revision 2 already exists, but base remains 1.
    assert stale.status_code == 409
    assert persisted_files(folder) == before_conflict
    body.update(based_on_revision_number=2, status=third_status)
    third = client.post(url, json=body)
    assert third.status_code == 201
    assert original_hashes(folder) == hashes
    assert persisted_files(transcription_folder / "acceptances") == acceptance_files
    for name, data in old_revisions.items():
        assert (transcription_folder / "revisions" / name).read_bytes() == data

    history = client.get(f"/transcriptions/{transcription_id}").json()
    assert [item["revision_number"] for item in history["revisions"]] == [1, 2, 3]
    assert [item["status"] for item in history["revisions"]] == ["NEEDS_REVIEW", "ACCEPTED", third_status]
    assert history["acceptances"] == [acceptance]
    assert all(item["segments"][1]["latex"] == "2 + 2 = 5" for item in history["revisions"])
    assert SubmissionStore(router.store().root).transcription_history(transcription_id).model_dump(mode="json") == history


@pytest.mark.parametrize("operation", ["create", "revision", "accept"])
def test_failed_write_keeps_all_originals_and_history_without_partial_files(client, monkeypatch, operation):
    submission_id = create_submission(client)
    folder = router.store().root / submission_id
    first = create_transcription(client, submission_id) if operation != "create" else None
    before = persisted_files(folder)
    original_write = SubmissionStore._write

    def fail_write(path, data):
        # Inject failure after a partial write inside the unpublished temporary file.
        original_write(path, data[:10])
        raise OSError("simulated full disk")

    monkeypatch.setattr(SubmissionStore, "_write", staticmethod(fail_write))
    url, body = mutation_request(operation, submission_id, first["transcription_id"] if first else None)
    assert client.post(url, json=body).status_code == 503
    assert persisted_files(folder) == before
    assert not list(folder.glob("transcriptions/.pending-*"))


def test_rejected_mutations_leave_originals_and_history_unchanged(client):
    submission_id = create_submission(client)
    first = create_transcription(client, submission_id)
    folder = router.store().root / submission_id
    before = persisted_files(folder)
    url, body = mutation_request("revision", submission_id, first["transcription_id"])
    body["segments"][0]["page_index"] = 2
    assert client.post(url, json=body).status_code == 422
    assert persisted_files(folder) == before
    url, body = mutation_request("accept", submission_id, first["transcription_id"])
    body["revision_number"] = 99
    assert client.post(url, json=body).status_code == 404
    assert persisted_files(folder) == before


def test_concurrent_revisions_on_same_base_publish_one_linear_successor(client):
    submission_id = create_submission(client)
    first = create_transcription(client, submission_id)
    folder = router.store().root / submission_id
    before = original_hashes(folder)
    url, body = mutation_request("revision", submission_id, first["transcription_id"])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post(url, json=body), range(2)))
    assert sorted(response.status_code for response in results) == [201, 409]
    history = client.get(f'/transcriptions/{first["transcription_id"]}').json()
    assert [item["revision_number"] for item in history["revisions"]] == [1, 2]
    assert original_hashes(folder) == before


async def send_asgi_body(url, raw, declared_length=None, tail=b""):
    """Exercise actual ASGI chunks, including inaccurate/missing Content-Length."""
    headers = [(b"content-type", b"application/json")]
    if declared_length is not None:
        headers.append((b"content-length", str(declared_length).encode()))
    chunks = [raw[index:index + 64 * 1024] for index in range(0, len(raw), 64 * 1024)]
    if tail:
        chunks.append(tail)
    consumed = 0
    sent = []

    async def receive():
        nonlocal consumed
        if consumed >= len(chunks):
            return {"type": "http.disconnect"}
        chunk = chunks[consumed]
        consumed += 1
        return {"type": "http.request", "body": chunk, "more_body": consumed < len(chunks)}

    async def send(message):
        sent.append(message)

    await app({
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": "POST", "scheme": "http", "path": url, "raw_path": url.encode(),
        "query_string": b"", "root_path": "", "headers": headers,
        "server": ("testserver", 80), "client": ("testclient", 123),
    }, receive, send)
    status = next(message["status"] for message in sent if message["type"] == "http.response.start")
    return status, consumed, len(chunks)


@pytest.mark.parametrize("operation", ["create", "revision", "accept"])
@pytest.mark.parametrize("boundary", ["below", "near", "exact", "above"])
@pytest.mark.parametrize("declared_length", [None, 1, 20 * 1024 * 1024])
def test_body_limit_counts_bytes_before_store_and_keeps_boundary_inclusive(
    client, monkeypatch, operation, boundary, declared_length,
):
    submission_id = create_submission(client)
    first = create_transcription(client, submission_id) if operation != "create" else None
    folder = router.store().root / submission_id
    before = persisted_files(folder)
    url, body = mutation_request(operation, submission_id, first["transcription_id"] if first else None)
    raw = json.dumps(body).encode()
    limit = body_limit.MAX_TRANSCRIPTION_BODY_BYTES
    if boundary != "below":
        target = limit + {"near": -1, "exact": 0, "above": 1}[boundary]
        raw += b" " * (target - len(raw))  # Valid JSON at the exact byte boundary.

    if boundary == "above":
        def forbidden(*args, **kwargs):
            raise AssertionError("The store must not execute after an oversized body")
        for name in ("create_transcription", "create_transcription_revision", "accept_transcription"):
            monkeypatch.setattr(SubmissionStore, name, forbidden)
    status, consumed, chunk_count = asyncio.run(send_asgi_body(
        url, raw, declared_length, tail=b"unread after the over-limit chunk" if boundary == "above" else b"",
    ))
    if boundary == "above":
        assert status == 413
        assert consumed < chunk_count  # Stop receiving immediately, without draining the tail.
        assert persisted_files(folder) == before
    else:
        assert status == (200 if operation == "accept" else 201)


def test_oversized_body_with_content_length_matching_bytes(client, monkeypatch):
    submission_id = create_submission(client)
    folder = router.store().root / submission_id
    before = persisted_files(folder)
    raw = b" " * (body_limit.MAX_TRANSCRIPTION_BODY_BYTES + 1)
    response = client.post(
        f"/submissions/{submission_id}/transcriptions", content=raw,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert persisted_files(folder) == before
