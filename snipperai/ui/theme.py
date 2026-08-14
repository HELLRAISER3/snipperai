# snipperai/ui/theme.py
"""Dark 'liquid glass' theme tokens and QSS for SnipperAI.

Single source of truth for the app's monochrome design system: off-black
canvas, translucent glass surfaces, restrained typography, one radius
scale, one elevation model. Every window builds on `get_theme_qss(...)`
plus the shared widgets in `controls.py` rather than defining its own
inline stylesheets - that's what keeps every window looking like the
same app instead of five different experiments.
"""

FONT_STACK = (
    '"SF Pro Display", "SF Pro Text", "Segoe UI Variable Text", '
    '"Segoe UI", "Helvetica Neue", Inter, Arial, sans-serif'
)

# --- Tonal tokens ---------------------------------------------------------
# Off-black/off-white on purpose: pure #000/#FFF reads as harsh/high-vis,
# not premium. These are also imported directly by controls.py (e.g. for
# ToggleSwitch's hand-painted knob) and by windows that build inline HTML
# (agent chat) so there is exactly one place colors are ever defined.
CANVAS = "#161616"
SURFACE = "rgba(255, 255, 255, 0.045)"
SURFACE_BORDER = "rgba(255, 255, 255, 0.08)"
INPUT_SURFACE = "rgba(255, 255, 255, 0.07)"
TEXT_PRIMARY = "#F2F2F2"
TEXT_SECONDARY = "rgba(255, 255, 255, 0.55)"
TEXT_TERTIARY = "rgba(255, 255, 255, 0.35)"

# A touch of translucency for glass panels that should let a hint of the
# desktop show through (used by ocr/settings/agent). Kept as one shared
# value so all three stay visually consistent instead of drifting.
PANEL_TRANSLUCENT = "rgba(22, 22, 22, 0.92)"

BASE_QSS = f"""
* {{
    font-family: {FONT_STACK};
}}

QWidget#root {{
    background: transparent;
}}

/* --- Panel / chrome ---------------------------------------------------- */

QFrame#panel {{
    background-color: {CANVAS};
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
}}

QFrame#panel:hover {{
    border-color: rgba(255, 255, 255, 0.14);
}}

QFrame#title_bar {{
    background-color: rgba(255, 255, 255, 0.02);
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}}

QLabel#window_title {{
    color: {TEXT_TERTIARY};
    font-size: 12px;
    font-weight: 600;
}}

/* --- Section cards (replaces QGroupBox everywhere) ---------------------- */

QFrame#card {{
    background-color: {SURFACE};
    border: 1px solid {SURFACE_BORDER};
    border-radius: 12px;
}}

QLabel#card_title {{
    color: {TEXT_TERTIARY};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}

/* --- Shared text roles --------------------------------------------------
   These four were used by ocr_result_window.py but never actually defined
   anywhere in the previous theme.py - they were rendering with default
   Qt styling (effectively invisible/wrong on a dark panel). */

QLabel#title_label {{
    color: {TEXT_PRIMARY};
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.2px;
}}

QLabel#subtitle_label {{
    color: {TEXT_SECONDARY};
    font-size: 12.5px;
}}

QLabel#section_label {{
    color: {TEXT_TERTIARY};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#footer_label {{
    color: {TEXT_TERTIARY};
    font-size: 11px;
}}

QLabel#status_label {{
    background-color: rgba(255, 255, 255, 0.08);
    color: {TEXT_SECONDARY};
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.3px;
}}

QLabel#field_label {{
    color: {TEXT_SECONDARY};
    font-size: 12.5px;
    font-weight: 500;
}}

QLabel#toggle_label {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
    font-weight: 500;
}}

/* --- Inputs -------------------------------------------------------------- */

QLineEdit {{
    background-color: {INPUT_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9px;
    padding: 9px 12px;
    font-size: 13px;
    selection-background-color: rgba(255, 255, 255, 0.25);
    selection-color: {TEXT_PRIMARY};
}}

QLineEdit:focus {{
    border: 1px solid rgba(255, 255, 255, 0.35);
    background-color: rgba(255, 255, 255, 0.09);
}}

QLineEdit:disabled {{
    color: {TEXT_TERTIARY};
}}

QPlainTextEdit, QTextEdit {{
    background-color: {INPUT_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
    selection-background-color: rgba(255, 255, 255, 0.25);
    selection-color: {TEXT_PRIMARY};
    font-size: 13.5px;
}}

QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid rgba(255, 255, 255, 0.35);
}}

QScrollBar:vertical {{
    background: transparent;
    width: 9px;
    margin: 6px 2px 6px 0;
}}

QScrollBar::handle:vertical {{
    background-color: rgba(255, 255, 255, 0.18);
    min-height: 28px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: rgba(255, 255, 255, 0.30);
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* --- Buttons --------------------------------------------------------------
   One filled primary action per window, everything else ghost/outline.
   Hierarchy comes from fill vs. outline, never from color. */

QPushButton {{
    background-color: rgba(255, 255, 255, 0.06);
    color: {TEXT_PRIMARY};
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 12px;
    padding: 10px 14px;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: rgba(255, 255, 255, 0.12);
}}

QPushButton:pressed {{
    background-color: rgba(255, 255, 255, 0.16);
}}

QPushButton:disabled {{
    background-color: rgba(255, 255, 255, 0.03);
    color: {TEXT_TERTIARY};
    border-color: rgba(255, 255, 255, 0.06);
}}

QPushButton#ghost_button {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 15px;
    padding: 7px 16px;
    font-size: 12.5px;
    font-weight: 600;
}}

QPushButton#ghost_button:hover {{
    border-color: rgba(255, 255, 255, 0.28);
    color: {TEXT_PRIMARY};
}}

QPushButton#primary_button {{
    background-color: {TEXT_PRIMARY};
    color: {CANVAS};
    border: none;
    border-radius: 15px;
    padding: 8px 20px;
    min-width: 120px;
    font-size: 12.5px;
    font-weight: 700;
}}

QPushButton#primary_button:hover {{
    background-color: #FFFFFF;
}}

QPushButton#primary_button:pressed {{
    background-color: #D9D9D9;
}}

QPushButton#primary_button:disabled {{
    background-color: rgba(255, 255, 255, 0.14);
    color: {TEXT_TERTIARY};
}}
"""

# --- Component-specific overrides -----------------------------------------

SETTINGS_QSS = f"""
QFrame#panel {{
    background-color: {PANEL_TRANSLUCENT};
}}
"""

MENU_QSS = f"""
QFrame {{
    background-color: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}}

QPushButton {{
    background-color: rgba(255, 255, 255, 0.04);
    border-radius: 10px;
    color: {TEXT_PRIMARY};
}}
"""

OCR_QSS = f"""
QFrame#panel {{
    background-color: {PANEL_TRANSLUCENT};
}}

QPushButton#copy_button {{
    background-color: {TEXT_PRIMARY};
    color: {CANVAS};
    border: none;
    border-radius: 17px;
    padding: 9px 20px;
    min-width: 130px;
    font-size: 13px;
    font-weight: 700;
}}

QPushButton#copy_button:hover {{
    background-color: #FFFFFF;
}}

QPushButton#copy_button:pressed {{
    background-color: #D9D9D9;
}}

QPushButton#copy_button[state="success"] {{
    background-color: rgba(255, 255, 255, 0.14);
    color: {TEXT_PRIMARY};
    border: 1px solid rgba(255, 255, 255, 0.24);
}}
"""

AGENT_QSS = f"""
QFrame#panel {{
    background-color: {PANEL_TRANSLUCENT};
}}

QLabel#thumb_frame {{
    background-color: {SURFACE};
    border: 1px solid {SURFACE_BORDER};
    border-radius: 10px;
}}

QLabel#agent_info_label {{
    color: {TEXT_SECONDARY};
    font-size: 12.5px;
}}

QPushButton#send_button {{
    background-color: {TEXT_PRIMARY};
    color: {CANVAS};
    border: none;
    border-radius: 15px;
    padding: 9px 20px;
    min-width: 90px;
    font-size: 13px;
    font-weight: 700;
}}

QPushButton#send_button:hover {{
    background-color: #FFFFFF;
}}

QPushButton#send_button:pressed {{
    background-color: #D9D9D9;
}}

QPushButton#send_button:disabled {{
    background-color: rgba(255, 255, 255, 0.10);
    color: {TEXT_TERTIARY};
}}
"""

ONBOARDING_QSS = f"""
QLabel#onboarding_title {{
    color: {TEXT_PRIMARY};
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.2px;
}}

QLabel#onboarding_subtitle {{
    color: {TEXT_SECONDARY};
    font-size: 13px;
}}

QLabel#onboarding_body {{
    color: {TEXT_SECONDARY};
    font-size: 13px;
}}

QLabel#dot_active {{
    color: {TEXT_PRIMARY};
    font-size: 18px;
}}

QLabel#dot_inactive {{
    color: {TEXT_TERTIARY};
    font-size: 18px;
}}
"""


def get_theme_qss(component: str | None = None) -> str:
    """Base monochrome QSS plus any component-specific additions.

    Additions are appended (not replacing BASE_QSS), so later selectors
    win Qt's normal cascade - keep component overrides narrow and only
    for things that are genuinely specific to that window.
    """
    qss = BASE_QSS
    overrides = {
        "settings": SETTINGS_QSS,
        "menu": MENU_QSS,
        "ocr": OCR_QSS,
        "agent": AGENT_QSS,
        "onboarding": ONBOARDING_QSS,
    }
    qss += overrides.get(component, "")
    return qss