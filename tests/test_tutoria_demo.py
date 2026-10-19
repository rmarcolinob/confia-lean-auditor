"""TutorIA presentation contracts; routes and isolation are exercised by JS tests."""
import re

from test_ui_p0_accessibility import STATIC, Controls


def test_tutoria_assets_are_local_and_demo_is_loaded_before_the_experience():
    source = (STATIC / 'index.html').read_text()
    assets = ['tutoria.css', 'demo/tutoria-demo-data.js', 'tutoria.js']
    for asset in assets:
        assert (STATIC / asset).is_file()
        assert f'/static/{asset}?v=' in source
    assert source.index('/static/demo/tutoria-demo-data.js') < source.index('/static/tutoria.js') < source.index('/static/shell.js')
    controls = Controls(source).controls
    assert 'hidden' in controls['tutoria-root']
    assert controls['tutoria-navigation']['aria-label'] == 'Navegação do TutorIA'


def test_tutoria_reuses_approved_color_tokens_and_reflows_without_notebook_changes():
    css = (STATIC / 'tutoria.css').read_text()
    assert not re.search(r'#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|oklch\(', css)
    assert not re.search(r'--[\w-]+\s*:', css)  # No parallel token palette.
    assert 'var(--color-primary)' in css and 'var(--color-primary-strong)' in css
    assert re.search(r'\.tutoria-module-grid\s*\{[^}]*repeat\(6,', css)
    assert re.search(r'@media \(max-width: 1100px\).*?\.tutoria-module-grid\s*\{[^}]*repeat\(2,', css, re.S)
    assert re.search(r'@media \(max-width: 1100px\).*?\.tutoria-module\s*\{[^}]*grid-column: auto', css, re.S)
    assert re.search(r'@media \(max-width: 620px\).*?\.tutoria-module-grid[^}]*grid-template-columns: minmax\(0, 1fr\)', css, re.S)
    assert 'body[data-resolution-active="true"] #tutoria-root { display: none; }' in css


def test_tutoria_demo_does_not_introduce_a_persistence_or_audit_client():
    presentation = (STATIC / 'tutoria.js').read_text()
    fixtures = (STATIC / 'demo/tutoria-demo-data.js').read_text()
    for source in (presentation, fixtures):
        assert not re.search(r'\bfetch\s*\(|localStorage|sessionStorage|indexedDB|XMLHttpRequest', source)
        assert not re.search(r'["\x27]/(?:audit|submissions|management|assessments)', source)
    assert 'progress_demo' in fixtures
    assert 'feedbackOrigin: "DEMO"' in presentation
    assert 'origin: "REAL"' in presentation
