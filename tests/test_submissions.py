"""Artifact transport/integrity only: never run an audit for this increment."""
import base64
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import struct
import zlib

from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from confia_lean_auditor.main import app
from confia_lean_auditor.submissions import router
from confia_lean_auditor.submissions.schemas import SubmissionRequest, SubmissionRecord
from confia_lean_auditor.submissions.store import SubmissionStore
from test_capture_contracts import valid_document


def png(width=1200, height=1600, shade=255):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    rows = (b"\0" + bytes([shade, shade, shade, 255]) * width) * height
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def payload(pages=1):
    snapshot = valid_document()
    snapshot["document_kind"] = "local_snapshot"
    snapshot["local_snapshot_id"] = "snapshot:test-01"
    for index in range(1, pages):
        page = copy.deepcopy(snapshot["pages"][0])
        page.update(page_id=f"page:{index + 1}", index=index)
        snapshot["pages"].append(page)
    return {"snapshot_json": json.dumps(snapshot, ensure_ascii=False, indent=2),
            "pages": [{"page_id": page["page_id"], "png_base64": base64.b64encode(png(shade=255-index)).decode()}
                      for index, page in enumerate(snapshot["pages"])],
            "student_reference": "aluno-teste-01"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    return TestClient(app)


def test_received_original_bytes_hashes_receipt_and_all_pages(client, tmp_path):
    request = payload(3)
    response = client.post("/submissions", json=request)
    assert response.status_code == 201, response.text
    receipt = response.json()
    assert re.fullmatch(r"sub_[0-9a-f]{32}", receipt["submission_id"])
    assert receipt["snapshot_id"] == "snapshot:test-01"
    assert receipt["problem_id"] == "ITA2025F2Q1"
    assert receipt["status"] == "RECEIVED"
    assert receipt["source"] == "tablet"
    assert receipt["capture_schema_version"] == receipt["receipt_version"] == "1.0"
    assert receipt["received_at"]
    assert receipt["student_reference_verified"] is False
    folder = tmp_path / "submissions" / receipt["submission_id"]
    snapshot = request["snapshot_json"].encode()
    assert (folder / "snapshot.json").read_bytes() == snapshot
    assert receipt["snapshot"]["sha256"] == hashlib.sha256(snapshot).hexdigest()
    assert json.loads((folder / "receipt.json").read_bytes()) == receipt
    record = json.loads((folder / "submission.json").read_bytes())
    assert record == {key: value for key, value in receipt.items() if key != "receipt_version"}
    assert not {"score", "verdict", "rubric", "lean", "transcription", "claims"} & record.keys()
    for index, ref in enumerate(receipt["page_images"]):
        original = base64.b64decode(request["pages"][index]["png_base64"])
        assert (folder / ref["filename"]).read_bytes() == original
        assert ref["sha256"] == hashlib.sha256(original).hexdigest()
        assert ref["page_index"] == index
        image = client.get(f'/submissions/{receipt["submission_id"]}/pages/{index}')
        assert image.status_code == 200
        assert image.content == original
        assert image.headers["content-type"] == "image/png"
    assert client.get(f'/submissions/{receipt["submission_id"]}/snapshot').content == snapshot


def test_list_detail_integrity_and_persistence_after_store_recreation(client):
    assert client.get("/submissions").json() == []
    receipt = client.post("/submissions", json=payload()).json()
    listing = client.get("/submissions")
    assert listing.headers["cache-control"] == "no-store"
    assert [row["submission_id"] for row in listing.json()] == [receipt["submission_id"]]
    detail = client.get(f'/submissions/{receipt["submission_id"]}').json()
    assert detail["receipt"] == receipt
    assert all(artifact["matches"] for artifact in detail["integrity"])
    assert len(detail["integrity"]) == 2
    assert SubmissionStore(router.store().root).detail(receipt["submission_id"]).receipt.model_dump(mode="json") == receipt


def test_identical_retry_returns_same_receipt_without_duplicate(client):
    request = payload()
    first = client.post("/submissions", json=request)
    second = client.post("/submissions", json=request)
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json() == second.json()
    assert len(client.get("/submissions").json()) == 1


def test_parallel_retry_publishes_exactly_one_submission(client):
    request = payload()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post("/submissions", json=request), range(2)))
    assert sorted(item.status_code for item in results) == [200, 201]
    assert results[0].json() == results[1].json()


@pytest.mark.parametrize("change", ["snapshot", "png", "reference", "format"])
def test_same_snapshot_id_different_content_conflicts(client, change):
    request = payload()
    assert client.post("/submissions", json=request).status_code == 201
    if change == "snapshot":
        snapshot = json.loads(request["snapshot_json"])
        snapshot["strokes"][0]["points"][0]["x"] = 11
        request["snapshot_json"] = json.dumps(snapshot)
    elif change == "png":
        request["pages"][0]["png_base64"] = base64.b64encode(png(shade=200)).decode()
    elif change == "reference":
        request["student_reference"] = "aluno-teste-02"
    else:
        request["snapshot_json"] = json.dumps(json.loads(request["snapshot_json"]), separators=(",", ":"))
    assert client.post("/submissions", json=request).status_code == 409
    assert len(client.get("/submissions").json()) == 1


@pytest.mark.parametrize("change", ["draft", "missing_id", "problem", "extra", "extra_stroke", "bounds", "missing_png", "duplicate_png", "wrong_page", "base64", "not_png", "dimensions", "crc", "truncated", "pages"])
def test_rejects_invalid_payload_without_publishing(client, change):
    request = payload()
    snapshot = json.loads(request["snapshot_json"])
    expected = 422
    if change == "draft":
        snapshot["document_kind"] = "draft"
        snapshot["local_snapshot_id"] = None
    elif change == "missing_id":
        snapshot["local_snapshot_id"] = None
    elif change == "problem":
        snapshot["problem_id"] = "NOT_IN_CATALOG"
        expected = 400
    elif change == "extra":
        request["destination"] = "../../unsafe"
    elif change == "extra_stroke":
        snapshot["strokes"][0]["score"] = 10
    elif change == "bounds":
        snapshot["strokes"][0]["points"][0]["x"] = 1201
    elif change == "missing_png":
        request["pages"] = []
    elif change == "duplicate_png":
        request["pages"].append(copy.deepcopy(request["pages"][0]))
    elif change == "wrong_page":
        request["pages"][0]["page_id"] = "page:unknown"
    elif change == "base64":
        request["pages"][0]["png_base64"] = "!invalid!"
    elif change == "not_png":
        request["pages"][0]["png_base64"] = base64.b64encode(b"not an image").decode()
    elif change == "dimensions":
        request["pages"][0]["png_base64"] = base64.b64encode(png(10, 10)).decode()
    elif change in {"crc", "truncated"}:
        data = bytearray(png())
        if change == "crc":
            data[30] ^= 1
        else:
            data = data[:-12]
        request["pages"][0]["png_base64"] = base64.b64encode(data).decode()
    else:
        request = payload(4)
        snapshot = json.loads(request["snapshot_json"])
    request["snapshot_json"] = json.dumps(snapshot)
    response = client.post("/submissions", json=request)
    assert response.status_code == expected, response.text
    assert "pressure_reported" not in response.text
    assert client.get("/submissions").json() == []


def test_size_limits_content_type_and_malformed_json(client, monkeypatch):
    assert client.post("/submissions", content="{}", headers={"Content-Type": "text/plain"}).status_code == 415
    assert client.post("/submissions", content="{", headers={"Content-Type": "application/json"}).status_code == 422
    monkeypatch.setattr(router, "MAX_REQUEST_BYTES", 100)
    assert client.post("/submissions", json=payload()).status_code == 413
    assert client.post("/submissions", content=(b"a" * 60 for _ in range(2)), headers={"Content-Type": "application/json"}).status_code == 413


def test_decoded_png_and_utf8_snapshot_limits(client, monkeypatch):
    from confia_lean_auditor.submissions import store
    monkeypatch.setattr(store, "MAX_PNG_BYTES", 10)
    assert client.post("/submissions", json=payload()).status_code == 413
    monkeypatch.setattr(store, "MAX_PNG_BYTES", 8 * 1024 * 1024)
    monkeypatch.setattr(store, "MAX_IMPORT_BYTES", 100)
    assert client.post("/submissions", json=payload()).status_code == 413


def test_write_failure_never_publishes_received_and_retry_recovers(client, monkeypatch):
    original = SubmissionStore._write
    def fail(path, data):
        if path.name == "page_1.png":
            raise OSError("test full disk")
        original(path, data)
    monkeypatch.setattr(SubmissionStore, "_write", staticmethod(fail))
    request = payload()
    assert client.post("/submissions", json=request).status_code == 503
    assert client.get("/submissions").json() == []
    assert not list(router.store().root.glob(".pending-*"))
    monkeypatch.setattr(SubmissionStore, "_write", staticmethod(original))
    assert client.post("/submissions", json=request).status_code == 201


def test_detects_changed_artifact_and_refuses_to_serve_or_acknowledge_it(client):
    request = payload()
    receipt = client.post("/submissions", json=request).json()
    folder = router.store().root / receipt["submission_id"]
    (folder / "page_1.png").write_bytes(b"test tampering")
    detail = client.get(f'/submissions/{receipt["submission_id"]}').json()
    assert detail["integrity"][1]["matches"] is False
    assert client.get(f'/submissions/{receipt["submission_id"]}/pages/0').status_code == 409
    assert client.post("/submissions", json=request).status_code == 409


def test_server_controls_paths_and_unknown_submission_pages_are_404(client):
    assert client.get("/submissions/not-a-server-id").status_code == 404
    receipt = client.post("/submissions", json=payload()).json()
    assert client.get(f'/submissions/{receipt["submission_id"]}/pages/9').status_code == 404
    assert client.get(f'/submissions/{receipt["submission_id"]}/pages/-1').status_code == 404


def test_submission_models_forbid_evaluation_and_client_paths():
    request = payload()
    request["filename"] = "unsafe"
    with pytest.raises(ValidationError):
        SubmissionRequest.model_validate(request)
    assert SubmissionRecord.model_config["extra"] == "forbid"
    assert not {"score", "verdict", "rubric", "lean"} & SubmissionRecord.model_fields.keys()


def test_submission_flow_never_calls_audit(client, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No mathematical audit is authorized in this flow")
    import confia_lean_auditor.main as main
    monkeypatch.setattr(main, "run_lean_file", forbidden)
    async def transport_only(scope, receive, send):
        if scope["type"] == "http":
            assert scope["path"] != "/audit"
        await app(scope, receive, send)
    client = TestClient(transport_only)
    # Static dependency boundary plus the complete transport/read path.
    from pathlib import Path
    sources = "\n".join(path.read_text() for path in Path(router.__file__).parent.glob("*.py"))
    assert "run_lean" not in sources and '"/audit"' not in sources
    receipt = client.post("/submissions", json=payload()).json()
    assert client.get("/submissions").status_code == 200
    assert client.get(f'/submissions/{receipt["submission_id"]}').status_code == 200
    assert client.get(f'/submissions/{receipt["submission_id"]}/pages/0').status_code == 200
