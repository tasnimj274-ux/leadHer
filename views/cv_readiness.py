"""CV X-Ray Mission page (Phase 2 redesign of the old "CV Readiness").

Still reads the uploaded PDF in memory only (never written to disk) and
scores it with the same rule-based utils.cv.score_cv() as before -
nothing about the scoring engine changed. What's new in Phase 2 is the
staged "scanning" reveal, the 5-dimension breakdown (via
utils.cv.dimension_breakdown, a pure presentation-layer regrouping of
the same 8 raw categories), and the "unlocked strengths / improvement
quests" framing.
"""
import time

import streamlit as st

from utils.cv import CV_ANALYSIS_KEY, MAX_FILE_SIZE_MB, dimension_breakdown, extract_text_from_pdf, score_cv
from utils.navigation import go_to
from utils.quest import render as render_quest

CSS = """
<style>
.block-container { max-width: 900px; padding-top: 2.2rem; }
.lh-brand { color: #C792FF; font-weight: 700; letter-spacing: 0.12em;
            font-size: 0.85rem; text-transform: uppercase; }
.lh-page-title { font-size: 1.9rem; font-weight: 800; color: #F7F3FF;
                 margin: 0.3rem 0 0.3rem 0; }
.lh-page-sub { color: rgba(239,234,252,0.74); margin-bottom: 1rem; }
.lh-score-box { background: linear-gradient(135deg, #C792FF 0%, #9B6DE0 100%);
                border-radius: 16px; padding: 22px; text-align: center;
                margin: 1rem 0; color: #fff; }
.lh-score-tag { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em;
                text-transform: uppercase; opacity: 0.85; }
.lh-score-num { font-size: 2.6rem; font-weight: 800; }
.lh-score-label { font-size: 0.9rem; opacity: 0.95; margin-top: 4px; }
.lh-row { display: flex; justify-content: space-between; font-size: 0.9rem;
          padding: 5px 2px; border-bottom: 1px solid rgba(199,146,255,0.14); }
.lh-unlock-box { background: rgba(255,255,255,0.065); border-radius: 12px; padding: 14px 18px;
                 margin: 0.6rem 0; border: 1px solid rgba(255,255,255,0.12); }
.lh-disclaimer { background: rgba(255,193,99,0.10); border-left: 4px solid #F0B429;
                 padding: 10px 14px; border-radius: 8px; font-size: 0.85rem;
                 color: #FFE8B5; margin: 1rem 0; }
</style>
"""


def _score_breakdown_html(breakdown: list) -> str:
    rows = [
        f'<div class="lh-row"><span>{name}</span><span>{points} / {max_points}</span></div>'
        for name, points, max_points in breakdown
    ]
    return "".join(rows)


def _dimension_breakdown_html(result: dict) -> str:
    rows = [
        f'<div class="lh-row"><span>{name}</span><span>{pct}%</span></div>'
        for name, points, max_points, pct in dimension_breakdown(result)
    ]
    return "".join(rows)


def _run_scan_animation() -> None:
    """A short, honest staged reveal - each line only appears once that
    check has actually been evaluated. Not decorative; the order matches
    the real evaluation order inside score_cv()."""
    steps = [
        "Reading document...",
        "Checking contact details...",
        "Checking Education & Skills sections...",
        "Checking Experience / Projects...",
        "Scanning wording and measurable results...",
    ]
    placeholder = st.empty()
    for i, step in enumerate(steps, start=1):
        placeholder.markdown(f"**SCANNING...** ({i}/{len(steps)}) {step}")
        time.sleep(0.25)
    placeholder.empty()


def _analyze_uploaded_file(uploaded_file) -> None:
    """Read, check, and score the uploaded PDF. Stops early with a
    friendly st.error() message for any of the problem cases."""
    if uploaded_file.size == 0:
        st.error("That file appears to be empty. Please upload a valid PDF.")
        return

    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(f"That file is larger than {MAX_FILE_SIZE_MB} MB. Please upload a smaller PDF.")
        return

    with st.spinner("Reading your CV..."):
        try:
            text = extract_text_from_pdf(uploaded_file)
        except ValueError as exc:
            st.error(str(exc))
            return

        if not text:
            st.error(
                "No readable text was found in this PDF. It may be a scanned "
                "image - try exporting or saving your CV as a text-based PDF."
            )
            return

    _run_scan_animation()
    st.session_state[CV_ANALYSIS_KEY] = score_cv(text)


def _render_results(result: dict) -> None:
    st.markdown("### 🏁 Mission Complete")
    st.markdown(
        f'<div class="lh-score-box">'
        f'<div class="lh-score-tag">CV Readiness Score</div>'
        f'<div class="lh-score-num">{result["total_score"]} / 100</div>'
        f'<div class="lh-score-label">Your performance in this CV-readiness '
        f"simulation only, not a hiring prediction.</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Readiness dimensions**")
    st.markdown(_dimension_breakdown_html(result), unsafe_allow_html=True)

    with st.expander("See the detailed score breakdown"):
        st.markdown(_score_breakdown_html(result["breakdown"]), unsafe_allow_html=True)

    st.markdown("### 🔓 YOU UNLOCKED")
    if result["strengths"]:
        for item in result["strengths"][:4]:
            st.markdown(f'<div class="lh-unlock-box">✓ <b>Strength:</b> {item}</div>',
                        unsafe_allow_html=True)
    else:
        st.write("No clear strengths were detected yet - see the improvement quests below.")

    if result["improvements"]:
        for item in result["improvements"][:4]:
            st.markdown(f'<div class="lh-unlock-box">🔓 <b>Improvement Quest:</b> {item}</div>',
                        unsafe_allow_html=True)
    else:
        st.write("Nice work - no major improvement quests were detected by this simulation.")

    st.caption(
        "This CV Readiness Score reflects this rule-based simulation only - it "
        "does not predict whether you'll be hired."
    )

    st.button(
        "Continue to Skill Challenge →",
        type="primary",
        on_click=go_to,
        args=("assessment",),
    )


def render() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="lh-brand">LeadHer Career Quest</div>', unsafe_allow_html=True)
    render_quest("cv_readiness")
    st.markdown('<div class="lh-page-title">📄 CV X-Ray Mission</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lh-page-sub">Upload your CV as a PDF. This rule-based check '
        "looks for common sections, contact details, action verbs and measurable "
        "results - simple things that many recruiters scan for first.</div>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader("Upload your CV (PDF only)", type=["pdf"])

    if st.button("🔍 Scan My CV", type="primary"):
        if uploaded_file is None:
            st.error("Please upload a PDF file first.")
        else:
            _analyze_uploaded_file(uploaded_file)

    result = st.session_state.get(CV_ANALYSIS_KEY)
    if result:
        _render_results(result)

    st.markdown(
        '<div class="lh-disclaimer">This is a rule-based educational check, not a '
        "real recruiter review, and it does not predict whether you'll get a job. "
        "Your uploaded file is processed temporarily in memory and is never saved "
        "to disk.</div>",
        unsafe_allow_html=True,
    )
    st.button("← Back to start", on_click=go_to, args=("landing",))
