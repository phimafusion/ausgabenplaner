from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_index_html_viewport_and_mobile_nav():
    """Verify that index.html contains modern viewport settings and mobile navigation elements."""
    html_path = STATIC_DIR / "index.html"
    assert html_path.exists(), "index.html must exist"
    content = html_path.read_text(encoding="utf-8")

    # Responsive viewport meta tag
    assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in content

    # Mobile menu hamburger button
    assert 'id="btn-mobile-menu"' in content
    assert 'class="btn-mobile-nav"' in content
    assert 'class="hamburger-bar"' in content

    # Navbar actions container
    assert 'id="navbar-actions"' in content


def test_styles_css_responsive_rules():
    """Verify that styles.css defines touch-friendly baselines and mobile media queries."""
    css_path = STATIC_DIR / "styles.css"
    assert css_path.exists(), "styles.css must exist"
    content = css_path.read_text(encoding="utf-8")

    # Touch action / tap highlight baseline
    assert "touch-action: manipulation;" in content
    assert "-webkit-tap-highlight-color: transparent;" in content

    # Hamburger nav styling
    assert ".btn-mobile-nav" in content
    assert ".hamburger-bar" in content

    # Media queries for tablet and smartphone
    assert "@media (max-width: 860px)" in content
    assert "@media (max-width: 640px)" in content

    # Mobile table card transform rules
    assert "data-table" in content
    assert "content: attr(data-label);" in content

    # Sticky historical comparison column for mobile scrolling
    assert "position: sticky;" in content
    assert "matrix-table" in content

    # Cost column nowrap enforcement
    assert "white-space: nowrap !important;" in content
    assert ".data-table th:nth-child(2)" in content


def test_app_js_mobile_interaction_and_data_labels():
    """Verify that app.js wires up the mobile menu toggle and sets data-label attributes."""
    js_path = STATIC_DIR / "app.js"
    assert js_path.exists(), "app.js must exist"
    content = js_path.read_text(encoding="utf-8")

    # Mobile elements wired
    assert "btnMobileMenu" in content
    assert "navbarActions" in content
    assert "is-open" in content
    assert "is-active" in content

    # Data label attributes for mobile card rendering
    assert 'data-label="Position"' in content
    assert 'data-label="Kosten"' in content
    assert 'data-label="Person"' in content
    assert 'data-label="Betrag"' in content


def test_static_files_served():
    """Verify that FastAPI serves static files properly."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Ausgabenplaner" in resp.text

    resp_css = client.get("/static/styles.css")
    assert resp_css.status_code == 200
    assert resp_css.headers["content-type"].startswith("text/css")

    resp_js = client.get("/static/app.js")
    assert resp_js.status_code == 200
    assert "javascript" in resp_js.headers["content-type"]


def test_table_lock_toggle_ui():
    """Verify that table lock toggle buttons and action column headers exist."""
    html_path = STATIC_DIR / "index.html"
    content = html_path.read_text(encoding="utf-8")

    assert 'id="btn-toggle-unlock-positions"' in content
    assert 'id="btn-toggle-unlock-contributions"' in content
    assert 'class="text-right th-actions hidden"' in content

    js_path = STATIC_DIR / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    assert "btnToggleUnlockPositions" in js_content
    assert "updateLockControls" in js_content


def test_position_interval_calculation_ui():
    """Verify that modal-position contains payment interval select, amount input and live calculation preview."""
    html_path = STATIC_DIR / "index.html"
    content = html_path.read_text(encoding="utf-8")

    assert 'id="pos-interval"' in content
    assert 'value="monthly"' in content
    assert 'value="quarterly"' in content
    assert 'value="yearly"' in content
    assert 'id="pos-raw-amount"' in content
    assert 'id="pos-calculated-monthly-val"' in content

    js_path = STATIC_DIR / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    assert "posInterval" in js_content
    assert "updatePositionCalculationPreview" in js_content


