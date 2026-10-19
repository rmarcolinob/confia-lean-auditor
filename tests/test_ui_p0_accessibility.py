"""Static guards for UI-P0 semantics; browser validation checks the computed styles."""
from html.parser import HTMLParser
from pathlib import Path
import re

STATIC = Path(__file__).resolve().parents[1] / "app/confia_lean_auditor/static"


class Controls(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.controls = {}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.controls[attributes["id"]] = attributes


def test_global_hidden_overrides_grid_and_disabled_is_not_wait():
    css = (STATIC / "styles.css").read_text()
    assert re.search(r"\[hidden\]\s*\{\s*display:\s*none\s*!important;", css)
    assert "cursor: wait" not in css
    assert 'button[aria-busy="true"]' in css
    assert "cursor: progress" in css


def test_visible_focus_covers_all_interactive_controls():
    css = (STATIC / "styles.css").read_text()
    assert ":is(button, a, input, select, textarea, summary):focus-visible" in css
    assert "outline: 3px solid var(--confia-navy)" in css
    assert "outline-offset: 3px" in css


def test_placeholder_contrast_exceeds_4_5_on_white():
    css = (STATIC / "styles.css").read_text()
    color = re.search(r"input::placeholder,\s*textarea::placeholder\s*\{\s*color: (#[0-9a-f]{6});", css).group(1)
    assert "opacity: 1" in css
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    luminance = sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))
    assert 1.05 / (luminance + 0.05) >= 4.5


def test_status_live_regions_and_validation_errors_are_associated():
    controls = Controls((STATIC / "index.html").read_text()).controls
    for name in ("service-status", "student-validation-message", "teacher-analysis-status", "manuscript-message"):
        assert controls[name]["role"] == "status"
        assert controls[name]["aria-live"] == "polite"
    for name in ("solution-input", "student-name-input", "problem-select"):
        assert controls[name]["aria-describedby"] == "student-validation-message"
    assert controls["result-panel"]["aria-label"] == "Feedback pedagógico"
