"""Chat asset, design and isolation contracts; interaction coverage lives in JS."""
import re

from test_ui_p0_accessibility import STATIC, Controls


def test_chat_assets_and_floating_control_are_integrated_in_dependency_order():
    html = (STATIC / 'index.html').read_text()
    for name in ('tutoria-chat.css', 'demo/tutoria-chat-demo.js', 'tutoria-chat.js'):
        assert (STATIC / name).is_file()
        assert f'/static/{name}?v=' in html
    assert html.index('/static/demo/tutoria-chat-demo.js') < html.index('/static/tutoria-chat.js') < html.index('/static/tutoria.js')
    control = Controls(html).controls['tutoria-assistant-toggle']
    assert control['type'] == 'button' and control['aria-expanded'] == 'false'


def test_chat_uses_existing_palette_and_a_compact_conversation():
    css = (STATIC / 'tutoria-chat.css').read_text()
    assert not re.search(r'#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|oklch\(', css)
    assert not re.search(r'--[\w-]+\s*:', css)
    assert 'var(--color-primary-strong)' in css and 'var(--color-surface-subtle)' in css
    assert 'flex-direction: column' in css
    assert 'overflow-y: auto' in css and 'overscroll-behavior: contain' in css


def test_chat_is_local_and_session_only_without_transport_or_persistence():
    for name in ('tutoria-chat.js', 'tutoria-assistant.js', 'demo/tutoria-chat-demo.js'):
        source = (STATIC / name).read_text()
        assert not re.search(r'\bfetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon|localStorage|sessionStorage|indexedDB', source)
        assert not re.search(r'["\x27]/(?:audit|submissions|management|assessments)', source)

    assert 'origin: "DEMO"' in (STATIC / 'demo/tutoria-chat-demo.js').read_text()

def test_contextual_drawer_is_nonmodal_hidden_initially_and_loaded_before_shell():
    html = (STATIC / 'index.html').read_text()
    for name in ('tutoria-assistant.js', 'tutoria-assistant.css'):
        assert (STATIC / name).is_file()
        assert f'/static/{name}?v=tutoria-contextual-final-01' in html
    assert html.index('/static/tutoria.js') < html.index('/static/tutoria-assistant.js') < html.index('/static/shell.js')
    controls = Controls(html).controls
    assert controls['tutoria-assistant-drawer']['aria-modal'] == 'false'
    assert controls['tutoria-assistant-drawer']['aria-labelledby'] == 'tutoria-assistant-title'
    assert 'hidden' in controls['tutoria-assistant-drawer'] and 'hidden' in controls['tutoria-assistant-rail']
    assert controls['tutoria-assistant-toggle']['aria-controls'] == 'tutoria-assistant-drawer'


def test_drawer_reserves_space_for_notebook_and_reuses_existing_colors():
    css = (STATIC / 'tutoria-assistant.css').read_text()
    assert not re.search(r'#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|oklch\(', css)
    assert 'width: calc(100% - min(380px, 42vw))' in css
    assert 'width: min(380px, 42vw)' in css
    assert 'height: 52dvh' in css and 'height: 48dvh' in css
    assert 'overflow-y: auto' in css
    assert 'overflow-x: auto' in (STATIC / 'tutoria-chat.css').read_text()
