"""UI-01 presentation contracts. No /audit request or Lean execution."""
from html.parser import HTMLParser
from pathlib import Path
import re

from fastapi.testclient import TestClient
from confia_lean_auditor.main import app, STATIC_DIR

CLIENT = TestClient(app)
STATIC = Path(STATIC_DIR)


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.ids = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, f"duplicate ID: {attrs['id']}"
            self.ids[attrs['id']] = (tag, attrs)


def test_shell_landmarks_and_profile_navigation_are_conventional():
    html = CLIENT.get('/').text
    page = Page(html)
    assert all(any(tag == expected for tag, _ in page.elements) for expected in ('header', 'aside', 'main', 'footer'))
    assert sum(tag == 'h1' for tag, _ in page.elements) == 1
    assert 'MVP ITA 2025' not in html
    assert 'Perfil de demonstração' in html
    profiles = [attrs for _, attrs in page.elements if 'data-tab-target' in attrs]
    assert len(profiles) == 3
    assert [p['aria-pressed'] for p in profiles] == ['true', 'false', 'false']
    for profile in profiles:
        assert profile['aria-controls'] == profile['data-tab-target']
        assert profile['aria-controls'] in page.ids
    assert not any(attrs.get('role') in ('tab', 'tablist', 'tabpanel') or 'aria-selected' in attrs for _, attrs in page.elements)
    assert page.ids['active-profile'][1]['aria-live'] == 'polite'
    assert page.ids['profile-navigation'][0] == 'nav'


def test_every_menu_destination_is_available_and_capture_is_reused():
    page = Page(CLIENT.get('/').text)
    links = [attrs['href'] for tag, attrs in page.elements if tag == 'a' and 'href' in attrs]
    expected = {'#student/home', '#student/tutoria', '#student/exams', '#student/submissions', '/capture',
                '#teacher/home', '#teacher/students', '#teacher/exams', '#teacher/submissions',
                '#teacher/transcriptions', '#teacher/analysis',
                '#management/home', '#management/overview'}
    assert expected <= set(links)
    assert not {'#student/resolve', '#student/feedback'} & {
        attrs['href'] for tag, attrs in page.elements
        if tag == 'a' and 'href' in attrs and 'data-shell-link' in attrs
    }
    for forbidden in ('#classes', '#progress', '#achievements', '#assignments', '#grades'):
        assert forbidden not in links
    assert CLIENT.get('/capture').status_code == 200
    assert not any(tag == 'canvas' for tag, _ in page.elements)
    frames = [attrs for tag, attrs in page.elements if tag == 'iframe']
    assert len(frames) == 1 and frames[0]['id'] == 'resolution-notebook'
    assert frames[0]['title']
    for asset in ('design-system.css', 'shell.js', 'capture/identity.css'):
        assert CLIENT.get(f'/static/{asset}?v=ui-01').status_code == 200


def test_management_panel_uses_institutional_aggregate_contract():
    html = CLIENT.get('/').text
    page = Page(html)
    for section in ('management-area', 'management-home', 'management-overview',
                    'management-cards', 'management-breadcrumb', 'management-table'):
        assert section in page.ids
    assert page.ids['management-message'][1]['role'] == 'status'
    management_html = html.split('<section id="management-area"', 1)[1].split('</main>', 1)[0]
    assert 'Dados agregados das escolas e turmas' in management_html
    assert 'Dados ilustrativos' not in management_html
    assert '<article class="macro-card">' not in management_html
    source = (STATIC / 'management.js').read_text()
    assert 'read("/management/network/overview")' in source
    assert 'read("/management/schools")' in source
    assert 'renderCards(overview.metrics)' in source
    assert 'dados agregados persistidos' in source
    assert 'não é nota oficial' in source


def test_skip_links_target_focusable_main_and_institutions_match():
    for route, main_id in (('/', 'app-root'), ('/capture', 'capture-main')):
        page = Page(CLIENT.get(route).text)
        skip = next(attrs for tag, attrs in page.elements if tag == 'a' and attrs.get('class') == 'skip-link')
        assert skip['href'] == f'#{main_id}'
        tag, attrs = page.ids[main_id]
        assert tag == 'main' and attrs['tabindex'] == '-1'
        html = CLIENT.get(route).text
        for name in ('Governo do Piauí', 'FAPEPI', 'SIA'):
            assert name in html


def test_tokens_components_and_non_color_states_are_shared():
    css = (STATIC / 'design-system.css').read_text()
    tokens = ['primary', 'primary-strong', 'background', 'surface', 'surface-subtle', 'text', 'text-muted',
              'border', 'focus', 'success', 'warning', 'danger', 'info']
    assert all(f'--color-{name}:' in css for name in tokens)
    assert all(f'--spacing-{n}:' in css for n in range(1, 9))
    assert all(f'--{name}:' in css for name in ('radius-control', 'radius-card', 'radius-pill', 'shadow-card',
               'shadow-overlay', 'control-height', 'z-header', 'z-sticky', 'z-overlay'))
    assert all(f'.{name}' in css for name in ('button-primary', 'button-secondary', 'button-danger', 'input',
               'textarea', 'select', 'card', 'section', 'badge', 'alert', 'status', 'empty-state', 'disclosure'))
    assert '[hidden] { display: none !important; }' in css
    assert 'status-pill[data-kind="busy"]::before' in css
    assert 'status-pill[data-kind="error"]::before' in css
    assert 'status-pill[data-kind="success"]::before' in css
    assert '@import' not in css and 'https://' not in css


def test_responsive_structure_shrinks_instead_of_clipping_overflow():
    css = (STATIC / 'styles.css').read_text()
    teacher_css = (STATIC / 'submissions/teacher.css').read_text()
    assert 'grid-template-columns: 226px minmax(0, 1fr)' in css
    assert '@media (max-width: 900px)' in css and '.shell-sidebar { position: static; }' in css
    assert '.profile-navigation > div { display: flex; flex-wrap: wrap;' in css
    assert '.shell { width: 100%; min-width: 0;' in css
    assert '#teacher-text-prototype { grid-template-columns: minmax(0, .85fr) minmax(0, 1.35fr)' in teacher_css
    for path in ('design-system.css', 'styles.css', 'capture/identity.css'):
        assert not re.search(r'(?:body|html)\s*\{[^}]*overflow(?:-x)?\s*:\s*(?:hidden|clip)', (STATIC / path).read_text())


def test_notebook_logical_geometry_and_input_surface_remain_owned_by_capture():
    html = CLIENT.get('/capture').text
    page = Page(html)
    assert page.ids['ink-canvas'][1]['width'] == '1200'
    assert page.ids['ink-canvas'][1]['height'] == '1600'
    assert page.ids['export-preview'][1]['width'] == '1200'
    assert page.ids['export-preview'][1]['height'] == '1600'
    css = (STATIC / 'capture/tablet.css').read_text()
    assert 'width: min(100%, 1180px)' in css
    canvas = re.search(r'#ink-canvas\s*\{(.*?)\}', css, re.S).group(1)
    assert 'width: 100%' in canvas and 'height: auto' in canvas
    assert 'aspect-ratio: 3 / 4' in canvas and 'touch-action: none' in canvas
    identity = (STATIC / 'capture/identity.css').read_text()
    assert not re.search(r'(?:canvas|canvas-frame|problem-dock)\s*\{', identity)
    assert 'shell-sidebar' not in html
    assert 'href="/#student/resolve"' in html


def test_central_product_vocabulary_is_preserved_without_contract_renames():
    source = '\n'.join((STATIC / path).read_text() for path in ('app.js', 'submissions/teacher.js', 'capture/tablet.js'))
    for phrase in ('Análise ConfIA', 'Solução enviada', 'Transcrição', 'Transcrição conferida', 'Recebida pelo ConfIA',
                   'Verificação formal com Lean', 'Critérios de avaliação', 'Número do envio'):
        assert phrase in source
    assert 'reconhecimento do manuscrito' in source
    assert 'versão preparada' in source.lower()
    assert 'rubric_assessment' in source  # Backend field stays unchanged.
