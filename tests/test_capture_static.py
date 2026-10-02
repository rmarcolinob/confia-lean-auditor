from __future__ import annotations

from pathlib import Path
from html.parser import HTMLParser
import re
import json

from fastapi.testclient import TestClient

from confia_lean_auditor.main import STATIC_DIR, app


CLIENT = TestClient(app)
CAPTURE_DIR = Path(STATIC_DIR) / "capture"


def test_shared_curated_registry_covers_exactly_the_ten_catalog_sources():
    response = CLIENT.get("/static/problem-presentations/registry.json")
    assert response.status_code == 200
    entries = response.json()
    catalog = CLIENT.get("/problems").json()
    assert len(entries) == 10
    assert len({entry["problem_id"] for entry in entries}) == 10
    assert {entry["problem_id"] for entry in entries} == {problem["problem_id"] for problem in catalog}
    statements = {problem["problem_id"]: problem["statement"] for problem in catalog}
    repo_root = Path(__file__).resolve().parents[1]
    for entry in entries:
        asset = json.loads((repo_root / "problems" / entry["problem_id"] / "problem.json").read_text(encoding="utf-8"))
        assert entry["source_statement"] == statements[entry["problem_id"]] == asset["statement"]
        assert set(entry) == {"problem_id", "source_statement", "display_version", "segments"}
        assert entry["display_version"] == 1
        assert entry["segments"]
        for segment in entry["segments"]:
            assert set(segment) == {"type", "content"}
            assert segment["type"] in {"text", "math"}
            assert isinstance(segment["content"], str)
            if segment["type"] == "math":
                assert not re.search(r"\$|\\\(|\\\)|\\\[|\\\]", segment["content"])
                assert segment["content"].strip()


def test_capture_route_serves_the_experimental_notebook():
    response = CLIENT.get("/capture")

    assert response.status_code == 200
    assert "ConfIA — Caderno de resolução" in response.text
    assert "Ambiente experimental de captura. Não realiza correção automática." in response.text
    assert "Preparar versão para envio" in response.text
    assert "Exportar traços" in response.text
    assert "Exportar PNG da página" in response.text
    assert "Mouse (teste)" in response.text
    assert "Até três páginas" in response.text


def test_capture_static_assets_are_served():
    for asset in ("tablet.css", "ink-model.js", "ink-canvas.js", "draft-store.js", "problem-math.js", "tablet.js"):
        response = CLIENT.get(f"/static/capture/{asset}")
        assert response.status_code == 200, asset
        assert response.content, asset


def test_capture_viewport_allows_voluntary_zoom_and_shrinkable_controls():
    html = CLIENT.get("/capture").text
    css = (CAPTURE_DIR / "tablet.css").read_text(encoding="utf-8")
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    assert not re.search(r"user-scalable\s*=\s*(?:no|0)|maximum-scale\s*=", html)
    assert not re.search(r"(?:body|html)\s*\{[^}]*overflow(?:-x)?\s*:\s*(?:hidden|clip)", css)
    assert "button, select { font: inherit; font-size: 1rem; }" in css
    assert "grid-template-columns: minmax(0, 1fr)" in css
    assert "min-width: 0" in css


def test_capture_loads_pinned_local_katex_assets_and_fonts_in_order():
    html = CLIENT.get("/capture").text
    prefix = "/static/capture/vendor/katex-0.18.9/"
    for asset in ("katex.min.js", "katex.min.css", "contrib/auto-render.min.js", "LICENSE"):
        response = CLIENT.get(prefix + asset)
        assert response.status_code == 200, asset
        assert response.content
    assert html.index(prefix + "katex.min.js") < html.index(prefix + "contrib/auto-render.min.js")
    assert html.index("problem-math.js") < html.index('src="/static/capture/tablet.js?v=p2-ui-01"')
    css = CLIENT.get(prefix + "katex.min.css").text
    fonts = re.findall(r"url\((fonts/[^)]+)\)", css)
    assert fonts
    for font in fonts:
        assert CLIENT.get(prefix + font).status_code == 200, font


def test_capture_loads_current_presentation_assets_despite_a_cached_previous_ui():
    html = CLIENT.get("/capture").text
    for asset in ("tablet.css", "problem-math.js", "tablet.js"):
        url = f"/static/capture/{asset}?v=p2-ui-01"
        assert url in html
        assert CLIENT.get(url).status_code == 200


def test_capture_exposes_persistence_and_recovery_outside_technical_details():
    class CaptureControlsParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_details = False
            self.controls = {}

        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if tag == "details":
                self.in_details = True
            if "id" in attributes:
                self.controls[attributes["id"]] = (attributes, self.in_details)

        def handle_endtag(self, tag):
            if tag == "details":
                self.in_details = False

    response = CLIENT.get("/capture")
    parser = CaptureControlsParser()
    parser.feed(response.text)
    indicator, inside_details = parser.controls["draft-persistence"]

    assert not inside_details
    assert indicator["role"] == "status"
    assert indicator["aria-live"] == "polite"
    assert not parser.controls["open-document"][1]
    assert not parser.controls["saved-document-select"][1]
    assert "Recuperar rascunho" in response.text
    assert 'href="#draft-recovery"' in response.text
    assert parser.controls["document-id"][1]
    assert parser.controls["export-preview"][1]


def test_capture_layout_prioritizes_canvas_and_collapses_secondary_information():
    html = (CAPTURE_DIR / "tablet.html").read_text(encoding="utf-8")
    css = (CAPTURE_DIR / "tablet.css").read_text(encoding="utf-8")
    javascript = (CAPTURE_DIR / "tablet.js").read_text(encoding="utf-8")

    assert 'id="problem-dock"' in html
    assert 'id="toggle-problem"' in html
    assert 'aria-controls="problem-statement-wrap"' in html
    assert '<details id="technical-details"' in html
    assert html.index('id="ink-canvas"') < html.index('id="technical-details"')
    assert "side-column" not in html
    assert "position: sticky" in css
    assert "width: min(100%, 1180px)" in css
    assert "function setProblemExpanded" in javascript


def test_capture_surface_uses_catalog_but_not_audit_or_recognition_services():
    javascript = "\n".join(path.read_text(encoding="utf-8") for path in CAPTURE_DIR.glob("*.js"))

    assert 'fetch("/problems"' in javascript
    assert 'fetch("/audit"' not in javascript
    assert "Mathpix" not in javascript
    assert "openai" not in javascript.lower()
    assert "run_lean" not in javascript


def test_capture_contract_does_not_expose_evaluation_or_server_receipt_fields():
    source = (CAPTURE_DIR / "ink-model.js").read_text(encoding="utf-8")

    for forbidden in ("receipt_id", "audit_ready", "teacher_id", "student_id", "score", "verdict"):
        assert forbidden not in source


def test_existing_root_and_audit_route_remain_registered():
    paths = {route.path for route in app.routes}

    assert "/" in paths
    assert "/capture" in paths
    assert "/audit" in paths
