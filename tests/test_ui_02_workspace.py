"""UI-02 contracts: student entry points share the validated capture surface."""
from pathlib import Path
import re
from fastapi.testclient import TestClient
from confia_lean_auditor.main import app, STATIC_DIR
from test_ui_01_shell import Page

STATIC = Path(STATIC_DIR)
CLIENT = TestClient(app)


def test_one_notebook_implementation_is_embedded_with_compatible_capture_route():
    page = Page(CLIENT.get('/').text)
    assert sum(tag == 'iframe' for tag, _ in page.elements) == 1
    assert not any(tag == 'canvas' for tag, _ in page.elements)
    assert list(STATIC.rglob('ink-model.js')) == [STATIC / 'capture/ink-model.js']
    assert list(STATIC.rglob('ink-canvas.js')) == [STATIC / 'capture/ink-canvas.js']
    assert CLIENT.get('/capture?embedded=1&problem_id=ITA2025Q1&mode=practice').status_code == 200
    capture = CLIENT.get('/capture').text
    for name in ('ink-model.js', 'ink-canvas.js', 'draft-store.js', 'submission-client.js'):
        assert f'/static/capture/{name}' in capture
    source = (STATIC / 'resolution-workspace.js').read_text()
    assert '/capture?embedded=1&problem_id=' in source
    assert 'ConfiaInkModel' not in source and 'getContext("2d")' not in source


def test_modes_responses_and_current_session_views_have_native_accessible_controls():
    html = CLIENT.get('/').text
    page = Page(html)
    for name in ('practice-mode', 'submission-mode', 'notebook-response', 'typed-response'):
        tag, attrs = page.ids[name]
        assert tag == 'button' and attrs['type'] == 'button'
        assert attrs['aria-pressed'] in ('true', 'false')
    assert page.ids['workspace-status'][1]['role'] == 'status'
    assert page.ids['workspace-status'][1]['aria-live'] == 'polite'
    assert page.ids['resolution-notebook'][1]['title']
    assert 'Como você quer trabalhar esta questão?' in html
    assert 'Representação digitada para análise' in html
    assert 'a versão digitada para analisar esta solução manuscrita' in html
    assert 'Ainda não há histórico persistente' in html
    assert 'somente recibos confirmados nesta sessão' in html
    assert 'data-student-mode=' not in html
    for forbidden in ('fake_test', 'recognition-providers', 'localStorage', 'meus envios'):
        assert forbidden not in (STATIC / 'resolution-workspace.js').read_text()


def test_sending_and_analysis_remain_separate_and_canvas_geometry_is_preserved():
    capture = (STATIC / 'capture/tablet.js').read_text()
    workspace = (STATIC / 'resolution-workspace.js').read_text()
    app = (STATIC / 'app.js').read_text()
    sender = (STATIC / 'capture/submission-client.js').read_text()
    assert '/audit' not in capture and '/audit' not in sender
    assert 'fetch("/audit"' in app
    assert '!window.ConfIAWorkspace.canAnalyze()' in app
    assert 'resolutionMode !== "submission"' in capture
    assert 'transport("/submissions"' in sender and 'method: "POST"' in sender
    assert 'receipt.snapshot_id === snapshot.local_snapshot_id' in sender
    assert 'snapshot_id === context.local_snapshot_id' in workspace
    assert 'source: "tablet"' not in workspace  # No invented server receipt.
    page = Page(CLIENT.get('/capture').text)
    assert page.ids['ink-canvas'][1]['width'] == '1200'
    assert page.ids['ink-canvas'][1]['height'] == '1600'
    css = (STATIC / 'styles.css').read_text()
    assert 'body[data-resolution-active="true"] .app-layout { grid-template-columns: minmax(0, 1fr)' in css
    assert 'body[data-resolution-active="true"] .shell-sidebar { position: static' in css


def test_analysis_is_a_native_closed_disclosure_after_the_notebook():
    html = CLIENT.get('/').text
    page = Page(html)
    tag, attrs = page.ids['practice-response']
    assert tag == 'details' and 'open' not in attrs
    assert page.ids['prepare-analysis'][0] == 'summary'
    assert html.index('id="resolution-notebook"') < html.index('id="prepare-analysis"') < html.index('id="solution-input"')
    assert 'Preparar análise' in html
    assert 'A análise atual usa sua versão digitada.' in html
    for control in ('handwriting-analysis-note', 'example-select', 'load-example', 'audit-button'):
        assert control in page.ids


def test_parent_statement_is_compact_and_sticky_through_notebook_and_submission():
    html = CLIENT.get('/').text
    page = Page(html)
    assert page.ids['notebook-problem-context'][0] == 'section'
    assert 'hidden' in page.ids['notebook-problem-context'][1]
    toggle = page.ids['toggle-notebook-problem'][1]
    assert toggle['type'] == 'button'
    assert toggle['aria-expanded'] == 'true'
    assert toggle['aria-controls'] == 'notebook-problem-body'
    assert page.ids['notebook-math-message'][1]['role'] == 'status'
    assert 'notebook-problem-title' not in page.ids
    assert re.search(r'<p class="eyebrow">Questão <span id="notebook-problem-code"></span></p>', html)
    assert html.index('id="resolution-title"') < html.index('id="notebook-problem-context"') < html.index('id="resolution-notebook"') < html.index('id="prepare-analysis"')
    assert html.index('id="resolution-notebook"') < html.index('class="notebook-end"') < html.index('id="workspace-draft-persistence"') < html.index('id="workspace-submission-actions"') < html.index('id="workspace-recognition-actions"')
    css = (STATIC / 'styles.css').read_text()
    sticky = re.search(r'body\[data-resolution-active="true"\] #notebook-problem-context\s*\{([^}]*)\}', css)
    assert sticky and 'position: sticky;' in sticky.group(1) and 'top: 0;' in sticky.group(1)
    assert 'body[data-handwriting-focus="true"] #notebook-problem-context' not in css
    assert '#notebook-problem-body { max-height:' in css
    assert 'position: sticky' not in (STATIC / 'capture/tablet.css').read_text().split('/* Embedded mode')[1]
    workspace = (STATIC / 'resolution-workspace.js').read_text()
    assert 'get("notebook-problem-statement").textContent = problem?.statement || ""' in workspace
    assert 'notebook-problem-title' not in workspace
    assert 'frame.style.height = `${context.content_height}px`' in workspace


def test_embedded_practice_has_no_second_visible_statement_and_still_has_persistence_status():
    css = (STATIC / 'capture/tablet.css').read_text()
    for selector in ('#problem-dock', '.setup-card', '.draft-persistence-bar', '#technical-details', '.export-card'):
        assert f'body[data-embedded="true"] {selector}' in css
    assert '.export-card { display: none; }' in css
    html = CLIENT.get('/capture').text
    page = Page(html)
    assert 'hidden' not in page.ids['problem-dock'][1]
    assert 'hidden' not in page.ids['problem-statement-wrap'][1]
    assert page.ids['toggle-problem'][1]['aria-expanded'] == 'true'
    assert page.ids['draft-persistence'][1]['role'] == 'status'
