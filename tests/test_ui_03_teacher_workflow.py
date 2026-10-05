"""UI-03 presentation contracts; no mathematical audit or Lean execution."""
from html.parser import HTMLParser
from pathlib import Path
import re

from fastapi.testclient import TestClient
from confia_lean_auditor.main import app, STATIC_DIR

STATIC = Path(STATIC_DIR)


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids = {}
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if "id" in attrs:
            assert attrs["id"] not in self.ids
            self.ids[attrs["id"]] = (tag, attrs)


def test_teacher_entities_are_shared_and_text_demo_is_explicitly_separate():
    html = TestClient(app).get('/').text
    page = Page(html)
    for key in ('manuscript-queue', 'manuscript-list', 'manuscript-detail', 'transcription-filter'):
        assert key in page.ids
    for view in ('home', 'submissions', 'transcriptions', 'analysis'):
        assert any(attrs.get('href') == f'#teacher/{view}' for _, attrs in page.elements)
    shell = (STATIC / 'shell.js').read_text()
    assert 'else window.ConfIATeacher.showView(view)' in shell
    assert 'if (view === "text") window.ConfIATeacher.showText()' in shell
    assert 'Demonstração textual local' in html
    assert 'não corresponde aos manuscritos persistidos' in html


def test_no_official_decision_controls_or_local_decision_writes_remain():
    html = (STATIC / 'index.html').read_text()
    source = (STATIC / 'app.js').read_text()
    for forbidden in ('approve-correction', 'request-review', 'release-feedback', 'updateSelectedSubmissionStatus', 'teacherEvaluationLabel'):
        assert forbidden not in html + source
    assert 'Avaliação docente — integração em desenvolvimento' in html
    manuscript = (STATIC / 'submissions/teacher.js').read_text()
    for forbidden in ('localStorage', '/audit', 'TeacherDecision', 'StructuredSolution'):
        assert forbidden not in manuscript


def test_analysis_states_have_text_and_style_only_when_real_text_requests_apply():
    source = (STATIC / 'app.js').read_text()
    for label in ('Não executada', 'Processando', 'Concluída', 'Não foi possível concluir'):
        assert f'Análise ConfIA: {label}' in source
    assert 'teacherAnalysisStatus.dataset.analysisState = state' in source
    css = (STATIC / 'styles.css').read_text()
    for state in ('processing', 'completed', 'failed'):
        assert f'[data-analysis-state="{state}"]' in css
    manuscript = (STATIC / 'submissions/teacher.js').read_text()
    assert 'Esta solução ainda não foi encaminhada para análise matemática.' in manuscript


def test_comparison_shrinks_on_tablet_and_stacks_on_mobile():
    css = (STATIC / 'submissions/teacher.css').read_text()
    assert 'grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr)' in css
    mobile = css[css.index('@media (max-width: 760px)'):]
    assert '.transcription-workspace { grid-template-columns: minmax(0, 1fr); }' in mobile
    assert '.original-manuscript-panel { position: static; }' in mobile
    assert '@media (max-width: 440px)' in css
    assert 'white-space: pre-wrap; overflow-wrap: anywhere' in css
    assert not re.search(r'overflow(?:-x)?\s*:\s*(?:hidden|clip)', css)


def test_disclosures_and_live_regions_preserve_accessible_feedback():
    source = (STATIC / 'submissions/teacher.js').read_text()
    for label in ('Histórico da transcrição', 'Detalhes do reconhecimento', 'Integridade dos arquivos', 'Detalhes técnicos'):
        assert label in source
    assert 'button.setAttribute("aria-label", `Abrir solução' in source
    assert 'pageLabel.setAttribute("aria-live", "polite")' in source
    assert 'heading.focus()' in source
    assert 'step.dataset.complete' in source
    html = Page((STATIC / 'index.html').read_text())
    for key in ('manuscript-message', 'teacher-analysis-status'):
        attrs = html.ids[key][1]
        assert attrs['role'] == 'status' and attrs['aria-live'] == 'polite'
    assert html.ids['transcription-filter'][0] == 'select'
