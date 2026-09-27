"""Global animated visual theme for LeadHer Career Quest.

Pure CSS only: no JavaScript or external assets. The optional web-font import has local fallbacks.
The background is decorative and uses pointer-events:none so it never
interferes with Streamlit controls.
"""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ---------- LeadHer game typography ---------- */
:root {
    --lh-font-body: 'Manrope', 'Segoe UI', Arial, sans-serif;
    --lh-font-display: 'Space Grotesk', 'Trebuchet MS', Arial, sans-serif;
}

html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"],
[data-testid="stMainBlockContainer"], .stMarkdown, .stTextInput, .stSelectbox,
.stSelectSlider, .stButton, .stForm, .stAlert, .stCaption, label, input, textarea, button {
    font-family: var(--lh-font-body) !important;
}

h1, h2, h3, h4, h5, h6,
.lh-brand, .lh-page-title, .lh-title, .lh-mission-tag, .lh-section-label,
.lh-level-name, .lh-score-num, .lh-unlock-title, .lh-case-title,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
    font-family: var(--lh-font-display) !important;
    letter-spacing: -0.02em;
}

.lh-page-title, .lh-title {
    font-weight: 700 !important;
}

.lh-brand, .lh-mission-tag, .lh-section-label, .lh-level-name {
    letter-spacing: 0.06em !important;
}

div[data-testid="stButton"] > button,
button[data-testid="stBaseButton-primary"] {
    font-family: var(--lh-font-display) !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}
/* ---------- High-contrast dark theme ---------- */
body, p, li, label,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] *,
[data-testid="stText"],
[data-testid="stText"] *,
[data-testid="stCaptionContainer"],
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stSelectSlider"] label,
[data-testid="stFileUploader"] label {
    color: #F7F3FF !important;
}

input, textarea, [role="combobox"], [data-baseweb="select"] * {
    color: #F7F3FF !important;
}

[data-baseweb="select"] > div,
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="menu"],
[data-baseweb="menu"] * {
    background-color: #17152F !important;
    color: #F7F3FF !important;
}

[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label,
[data-testid="stSelectbox"] label,
[data-testid="stSelectSlider"] label,
[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stFileUploader"] label {
    color: #F7F3FF !important;
}

[data-testid="stRadio"] [data-testid="stMarkdownContainer"] *,
[data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] * {
    color: #F7F3FF !important;
}

button, input, textarea {
    color-scheme: dark;
}

input::placeholder, textarea::placeholder {
    color: rgba(247,243,255,0.46) !important;
}

[data-testid="stSelectSlider"] [role="slider"] {
    background: #C792FF !important;
}

/* Keep informational text readable on the dark canvas. */
[data-testid="stAlert"], [data-testid="stAlert"] * {
    color: #F7F3FF !important;
}

/* ---------- Global canvas ---------- */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #090819 !important;
}

[data-testid="stAppViewContainer"] {
    position: relative;
    overflow-x: hidden;
}

.main, [data-testid="stMainBlockContainer"] {
    background: transparent !important;
}

.block-container {
    position: relative;
    z-index: 5;
}

/* ---------- Animated aurora background ---------- */
.cq-bg,
.cq-bg::before,
.cq-bg::after {
    position: fixed;
    inset: 0;
    pointer-events: none;
}

.cq-bg {
    z-index: 0;
    overflow: hidden;
    background:
        radial-gradient(circle at 12% 18%, rgba(168, 92, 255, 0.19), transparent 28%),
        radial-gradient(circle at 84% 22%, rgba(255, 107, 170, 0.14), transparent 26%),
        radial-gradient(circle at 70% 86%, rgba(77, 164, 255, 0.14), transparent 30%),
        linear-gradient(145deg, #090819 0%, #11102a 42%, #0c1226 100%);
}

.cq-bg::before {
    content: "";
    width: 72vw;
    height: 72vw;
    left: -18vw;
    top: -22vw;
    border-radius: 50%;
    background:
        radial-gradient(circle at 62% 52%,
            rgba(153, 90, 255, 0.24) 0%,
            rgba(153, 90, 255, 0.08) 28%,
            transparent 65%);
    filter: blur(18px);
    animation: cq-orbit-a 18s ease-in-out infinite alternate;
}

.cq-bg::after {
    content: "";
    width: 62vw;
    height: 62vw;
    right: -16vw;
    bottom: -24vw;
    border-radius: 50%;
    background:
        radial-gradient(circle at 42% 38%,
            rgba(79, 175, 255, 0.22) 0%,
            rgba(255, 112, 184, 0.08) 31%,
            transparent 68%);
    filter: blur(22px);
    animation: cq-orbit-b 22s ease-in-out infinite alternate;
}

.cq-bg-grid {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 1;
    opacity: 0.20;
    background-image:
        linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
    background-size: 44px 44px;
    mask-image: linear-gradient(to bottom, transparent, #000 14%, #000 84%, transparent);
    animation: cq-grid-drift 24s linear infinite;
}

.cq-stars {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 2;
    opacity: 0.75;
    background-image:
        radial-gradient(circle at 13% 24%, rgba(255,255,255,0.85) 0 1px, transparent 1.5px),
        radial-gradient(circle at 78% 15%, rgba(255,255,255,0.65) 0 1px, transparent 1.5px),
        radial-gradient(circle at 69% 73%, rgba(255,255,255,0.60) 0 1px, transparent 1.5px),
        radial-gradient(circle at 28% 84%, rgba(255,255,255,0.50) 0 1px, transparent 1.5px),
        radial-gradient(circle at 91% 56%, rgba(255,255,255,0.55) 0 1px, transparent 1.5px),
        radial-gradient(circle at 44% 11%, rgba(255,255,255,0.45) 0 1px, transparent 1.5px);
    animation: cq-twinkle 5s ease-in-out infinite alternate;
}

.cq-orb {
    position: fixed;
    pointer-events: none;
    z-index: 3;
    border-radius: 999px;
    filter: blur(0.2px);
    box-shadow: 0 0 40px rgba(180, 119, 255, 0.22);
}

.cq-orb.one {
    width: 14px; height: 14px; left: 9%; top: 26%;
    background: rgba(203, 155, 255, 0.78);
    animation: cq-float-1 12s ease-in-out infinite;
}

.cq-orb.two {
    width: 9px; height: 9px; right: 12%; top: 38%;
    background: rgba(111, 194, 255, 0.78);
    animation: cq-float-2 14s ease-in-out infinite;
}

.cq-orb.three {
    width: 11px; height: 11px; left: 18%; bottom: 18%;
    background: rgba(255, 144, 201, 0.76);
    animation: cq-float-3 16s ease-in-out infinite;
}

/* ---------- Glass surfaces ---------- */
[data-testid="stHeader"] {
    background: rgba(7, 7, 18, 0.35) !important;
    backdrop-filter: blur(12px);
}

[data-testid="stSidebar"] {
    background: rgba(10, 9, 25, 0.78) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}

div[data-testid="stForm"],
div[data-testid="stExpander"],
div[data-testid="stAlert"],
div[data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255,255,255,0.10);
    backdrop-filter: blur(12px);
}

/* ---------- Buttons: game-like glow ---------- */
div[data-testid="stButton"] > button,
button[data-testid="stBaseButton-primary"] {
    transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    box-shadow: 0 8px 26px rgba(109, 63, 200, 0.08);
}

div[data-testid="stButton"] > button:hover,
button[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(125, 86, 230, 0.18);
}

/* ---------- Small screen ---------- */
@media (max-width: 700px) {
    .cq-bg-grid { background-size: 30px 30px; }
    .cq-bg::before { width: 110vw; height: 110vw; }
    .cq-bg::after { width: 95vw; height: 95vw; }
}

/* ---------- Streamlit app chrome ---------- */
/* Hide Streamlit's viewer/developer chrome so LeadHer owns the viewport. */
[data-testid="stHeader"] {
    display: none !important;
}

[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"],
.stAppDeployButton,
#MainMenu,
footer {
    display: none !important;
}

/* ---------- Motion ---------- */
@keyframes cq-orbit-a {
    0% { transform: translate3d(0, 0, 0) scale(1); }
    100% { transform: translate3d(14vw, 10vh, 0) scale(1.18); }
}

@keyframes cq-orbit-b {
    0% { transform: translate3d(0, 0, 0) scale(1); }
    100% { transform: translate3d(-12vw, -9vh, 0) scale(1.15); }
}

@keyframes cq-grid-drift {
    0% { transform: translate3d(0, 0, 0); }
    100% { transform: translate3d(44px, 22px, 0); }
}

@keyframes cq-twinkle {
    0% { opacity: 0.35; }
    100% { opacity: 0.95; }
}

@keyframes cq-float-1 {
    0%, 100% { transform: translate3d(0,0,0); }
    50% { transform: translate3d(8vw,-10vh,0); }
}

@keyframes cq-float-2 {
    0%, 100% { transform: translate3d(0,0,0); }
    50% { transform: translate3d(-9vw,8vh,0); }
}

@keyframes cq-float-3 {
    0%, 100% { transform: translate3d(0,0,0); }
    50% { transform: translate3d(10vw,-6vh,0); }
}

@media (prefers-reduced-motion: reduce) {
    .cq-bg::before,
    .cq-bg::after,
    .cq-bg-grid,
    .cq-stars,
    .cq-orb {
        animation: none !important;
    }
}
</style>
"""

HTML = """
<div class="cq-bg"></div>
<div class="cq-bg-grid"></div>
<div class="cq-stars"></div>
<div class="cq-orb one"></div>
<div class="cq-orb two"></div>
<div class="cq-orb three"></div>
"""

def inject_game_background() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(HTML, unsafe_allow_html=True)
