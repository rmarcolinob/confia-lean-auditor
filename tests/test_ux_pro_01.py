"""UX-PRO-01 presentation contracts; interaction tests live in tests/js."""
import re
from test_ui_p0_accessibility import STATIC, Controls


def test_approved_palette_is_preserved():
    css = (STATIC / 'design-system.css').read_text()
    expected = {
        'primary': '#1b66d2', 'primary-strong': '#123b73', 'background': '#f4f7fb',
        'surface': '#ffffff', 'surface-subtle': '#eaf2ff', 'text': '#17233c',
        'text-muted': '#52647e', 'border': '#d5dfed', 'focus': '#123b73',
        'success': '#126c39', 'warning': '#795000', 'danger': '#8f2626', 'info': '#174c91',
        'success-subtle': '#e9f8ef', 'warning-subtle': '#fff7e7', 'danger-subtle': '#fff0f0',
    }
    for token, color in expected.items():
        assert f'--color-{token}: {color};' in css


def test_workspace_and_exam_actions_keep_shared_button_and_live_region_semantics():
    controls = Controls((STATIC / 'index.html').read_text()).controls
    for name in ('workspace-send-solution', 'workspace-tutor-feedback', 'workspace-preview-writing',
                 'workspace-undo', 'workspace-redo', 'workspace-add-page', 'resolve-question',
                 'audit-button', 'teacher-create-exam'):
        assert set(controls[name]['class'].split()) & {'primary-action', 'secondary-action', 'button-primary', 'button-secondary'}
    for name in ('student-exams-message', 'student-exam-progress', 'teacher-exams-message', 'teacher-context-message'):
        assert controls[name]['aria-live'] == 'polite'
    assert controls['student-exam-title']['tabindex'] == '-1'


def test_document_and_responsive_table_keep_readable_scrollable_layout():
    teacher = (STATIC / 'submissions/teacher.css').read_text()
    styles = (STATIC / 'styles.css').read_text()
    assert re.search(r'\.transcription-document\s*\{[^}]*background: var\(--color-surface\)', teacher)
    assert re.search(r'@media \(max-width: 1100px\).*?\.transcription-workspace\s*\{[^}]*grid-template-columns: minmax\(0, 1fr\)', teacher, re.S)
    assert re.search(r'\.submission-context\s*\{[^}]*position: sticky;', teacher)
    assert re.search(r'\.exam-deliveries-scroll\s*\{[^}]*overflow: auto', styles)
    assert re.search(r'#teacher-exam-progress thead th\s*\{[^}]*position: sticky', styles)
