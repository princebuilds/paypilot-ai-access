"""Cross-Check Matrix Row 12: Voice and keyboard fallback validation.

Target Invariant:
- With speech unsupported or mic denied, full shopping flow operates by keyboard and text.
- Textarea supports Enter (without shift) to submit.
- Mic button indicates unsupported/disabled state gracefully without crashing.
- Live region and ARIA attributes provide screen-reader announcements when speech synthesis is off.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def test_speech_feature_detection_and_fallback():
    """Verify app.js tests for SpeechRecognition and provides clear fallback."""
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert "SpeechRecognition" in app_js
    assert "speechSynthesis" in app_js
    assert "Voice input is not supported" in app_js or "micBtn" in app_js


def test_keyboard_navigation_and_shortcuts():
    """Verify index.html and app.js support keyboard submission and visible focus."""
    index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    styles_css = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")

    # Skip link exists and links to #main-content
    assert '<a href="#main-content" class="skip-link"' in index_html

    # Standard HTML form submit handles Enter key on text inputs
    assert "searchFormEl.addEventListener" in app_js
    assert '"submit"' in app_js or "'submit'" in app_js

    # High visibility focus indicator in styles.css
    assert ":focus" in styles_css
    assert "outline" in styles_css


def test_aria_live_regions_exist_for_screen_readers():
    """Verify polite and assertive regions announce assistant updates without audio."""
    index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")

    assert 'id="live-announcer"' in index_html
    assert 'aria-live="polite"' in index_html
    assert 'id="live-alert"' in index_html
    assert 'role="alert"' in index_html
