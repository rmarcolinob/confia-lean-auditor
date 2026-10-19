"""The post-receipt endpoint publishes a review revision, never a preview or acceptance."""
import json

from fastapi.testclient import TestClient
import httpx

from confia_lean_auditor.main import app
from confia_lean_auditor.recognition.mathpix import MathpixRecognitionProvider
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.submissions import router
from confia_lean_auditor.submissions.schemas import TranscriptionSegment
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.submission_audits.source import convert_segments
from test_submissions import payload


def test_teacher_single_source_revisions_preserve_recognition_and_historical_receipts(tmp_path, monkeypatch):
    """The unified editor creates versions through the existing immutable API."""
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "test-id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "test-key")
    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: MathpixRecognitionProvider(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json={"text": "2 + 2 = 5", "latex_styled": "2+2=5"})
    )))
    monkeypatch.setattr(router, "configured_registry", lambda: registry)
    client = TestClient(app)
    sid = client.post("/submissions", json=payload()).json()["submission_id"]
    run = client.post(f"/submissions/{sid}/recognitions", json={
        "provider": "mathpix", "idempotency_key": "teacher:source-editor",
    }).json()
    tid = run["transcription_id"]
    first = client.get(f"/transcriptions/{tid}").json()["revisions"][0]
    folder = tmp_path / "submissions" / sid

    for number in (1, 2, 3):
        before_acceptance = {path: path.read_bytes() for path in folder.rglob("*") if path.is_file()}
        accepted = client.post(f"/transcriptions/{tid}/accept", json={
            "revision_number": number, "reviewer_reference": "professor-teste-01",
            "acceptance_note": "Conferida visualmente com o manuscrito original.",
        })
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["acceptance"]["revision_number"] == number
        assert accepted.json()["acceptance"]["mathematical_validity_assessed"] is False
        assert all(path.read_bytes() == content for path, content in before_acceptance.items())
        if number == 3:
            break
        historical_files = {path: path.read_bytes() for path in folder.rglob("*") if path.is_file()}
        source = f"Leitura {number + 1}: \\(2+2=5\\).\n\nConclusão do aluno."
        edited = client.post(f"/transcriptions/{tid}/revisions", json={
            "based_on_revision_number": number, "reviewer_reference": "professor-teste-01",
            "reviewer_identity_verified": False, "change_type": "reading_correction",
            "segments": [{"segment_id": f"manual:page:{number + 1}", "page_index": 0, "order": 0,
                          "kind": "mixed", "text": source, "latex": None}],
            "status": "NEEDS_REVIEW",
        })
        assert edited.status_code == 201, edited.text
        current = edited.json()
        assert current["revision_number"] == number + 1
        assert current["status"] == "NEEDS_REVIEW"
        assert current["provenance"] == first["provenance"]
        assert current["recognizer_run_id"] == first["recognizer_run_id"]
        # The existing Auditor bridge receives exactly the edited source, once.
        solution, warnings = convert_segments([TranscriptionSegment.model_validate(item) for item in current["segments"]])
        assert solution == source and warnings == []
        assert all(path.read_bytes() == content for path, content in historical_files.items())
        history = client.get(f"/transcriptions/{tid}").json()
        assert history["revisions"][-1]["status"] == "NEEDS_REVIEW"
        assert len(history["acceptances"]) == number

    history = client.get(f"/transcriptions/{tid}").json()
    assert [item["revision_number"] for item in history["acceptances"]] == [1, 2, 3]
    assert history["revisions"][0]["segments"] == first["segments"]
    assert all(item["status"] == "ACCEPTED" for item in history["revisions"])
    assert SubmissionStore(router.store().root).transcription_history(tid).model_dump(mode="json") == history
    assert client.get(f"/submissions/{sid}/audits").json() == []


def test_official_mathpix_after_submission_is_visible_to_teacher_and_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "test-id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "test-key")
    calls = []

    def transport(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"text": "2 + 2 = 5", "latex_styled": "2 + 2 = 5"})

    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: MathpixRecognitionProvider(transport=httpx.MockTransport(transport)))
    monkeypatch.setattr(router, "configured_registry", lambda: registry)
    client = TestClient(app)
    submitted = payload()
    # Transient recognition does not create the official source.
    preview = client.post("/submissions/recognition-preview", json={
        "snapshot_json": submitted["snapshot_json"], "client_preview_id": "preview:official-test",
    })
    assert preview.status_code == 200
    assert not (tmp_path / "submissions").exists()
    receipt = client.post("/submissions", json=submitted)
    assert receipt.status_code == 201, receipt.text
    sid = receipt.json()["submission_id"]
    folder = tmp_path / "submissions" / sid
    originals = {name: (folder / name).read_bytes() for name in ("snapshot.json", "page_1.png", "submission.json", "receipt.json")}
    assert client.get(f"/submissions/{sid}/transcriptions").json() == []

    key = {"provider": "mathpix", "idempotency_key": "mathpix:0"}
    first = client.post(f"/submissions/{sid}/recognitions", json=key)
    assert first.status_code == 201, first.text
    summary = first.json()
    assert summary["status"] == "NEEDS_REVIEW" and summary["revision_number"] == 1
    run = client.get(f"/submissions/{sid}/recognitions/{summary['recognizer_run_id']}").json()
    assert run["result"]["segments"][0]["latex"] == "2 + 2 = 5"
    assert run["result"]["input_hash"] != preview.json()["snapshot_sha256"]  # Different contracts.
    teacher_list = client.get(f"/submissions/{sid}/transcriptions").json()
    assert len(teacher_list) == 1
    assert teacher_list[0]["latest_revision"]["status"] == "NEEDS_REVIEW"
    assert teacher_list[0]["latest_revision"]["segments"][0]["latex"] == "2 + 2 = 5"
    history = client.get(f"/transcriptions/{summary['transcription_id']}").json()
    assert len(history["revisions"]) == 1 and history["acceptances"] == []
    assert client.get(f"/submissions/{sid}/audits").json() == []

    # Reload/replay of the same prepared snapshot and execution key creates nothing new.
    assert client.post("/submissions", json=submitted).status_code == 200
    replay = client.post(f"/submissions/{sid}/recognitions", json=key)
    assert replay.status_code == 200 and replay.json() == summary
    assert len(client.get(f"/submissions/{sid}/recognitions").json()) == 1
    assert len(client.get(f"/submissions/{sid}/transcriptions").json()) == 1
    assert len(calls) == 2  # One transient request and one official request.
    assert all((folder / name).read_bytes() == data for name, data in originals.items())


def test_failed_official_run_keeps_submission_and_explicit_retry_creates_review(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "test-id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "test-key")
    failing = {"value": True}

    def transport(_request):
        return httpx.Response(503) if failing["value"] else httpx.Response(200, json={"latex_styled": "x=1"})

    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: MathpixRecognitionProvider(transport=httpx.MockTransport(transport)))
    monkeypatch.setattr(router, "configured_registry", lambda: registry)
    client = TestClient(app)
    receipt = client.post("/submissions", json=payload()).json()
    sid = receipt["submission_id"]
    first = client.post(f"/submissions/{sid}/recognitions", json={"provider": "mathpix", "idempotency_key": "mathpix:0"})
    assert first.status_code == 201 and first.json()["status"] == "FAILED"
    assert client.get(f"/submissions/{sid}").status_code == 200
    assert client.get(f"/submissions/{sid}/transcriptions").json() == []
    assert client.get(f"/submissions/{sid}/audits").json() == []
    failing["value"] = False
    assert client.post(f"/submissions/{sid}/recognitions", json={"provider": "mathpix", "idempotency_key": "mathpix:0"}).json() == first.json()
    retry = client.post(f"/submissions/{sid}/recognitions", json={"provider": "mathpix", "idempotency_key": "mathpix:1"})
    assert retry.status_code == 201 and retry.json()["status"] == "NEEDS_REVIEW"
    assert len(client.get(f"/submissions/{sid}/transcriptions").json()) == 1
    assert client.get(f"/submissions/{sid}/audits").json() == []
