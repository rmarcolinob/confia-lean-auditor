from pathlib import Path

from fastapi.testclient import TestClient
from confia_lean_auditor.main import app, STATIC_DIR

CLIENT = TestClient(app)


def test_capture_exposes_separate_submission_receipt_and_disabled_send():
    html = CLIENT.get("/capture").text
    assert 'id="send-solution" type="button" disabled' in html
    assert 'id="submission-message" role="status" aria-live="polite"' in html
    assert 'id="submission-receipt"' in html
    assert html.index('id="technical-details"') < html.index('id="send-solution"')
    assert html.index("submission-client.js") < html.index('src="/static/capture/tablet.js')
    assert 'href="/?area=teacher"' in html
    assert CLIENT.get("/static/capture/submission-client.js?v=p2-cap-02").status_code == 200


def test_teacher_inbox_is_integrated_and_separate_from_textual_correction():
    html = CLIENT.get("/").text
    assert html.index('id="teacher-area"') < html.index('id="manuscript-inbox"') < html.index('id="management-area"')
    assert 'id="teacher-text-prototype" hidden' in html
    assert 'id="refresh-manuscripts"' in html
    assert 'id="manuscript-list"' in html and 'id="manuscript-detail"' in html
    assert 'id="teacher-audit-button"' in html  # Existing separate prototype retained.
    for asset in ("teacher.css", "teacher.js"):
        assert CLIENT.get(f"/static/submissions/{asset}?v=p2-cap-03a").status_code == 200


def test_submission_frontends_use_text_nodes_original_pngs_and_no_direct_audit():
    sources = [(Path(STATIC_DIR) / "capture/submission-client.js").read_text(),
               (Path(STATIC_DIR) / "submissions/teacher.js").read_text()]
    for source in sources:
        assert "innerHTML" not in source
        for forbidden in ('fetch("/audit"', 'write("/audit"', "run_lean"):
            assert forbidden not in source
    assert "textContent" in sources[1]
    assert 'image.src = `/submissions/${id}/pages/${page.page_index}`' in sources[1]
    assert 'className = "transcription-workspace"' in sources[1]
    assert "2 + 2 = 5" in sources[1]
