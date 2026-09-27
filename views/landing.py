"""Landing page: headline, 5-stage journey, start button, disclaimer."""
import streamlit as st

from utils.navigation import go_to

# The stages of the journey. Edit this list to change the cards.
STAGES = [
    ("1", "Career Quest", "Pick your path and map the skills that matter for it."),
    ("2", "CV Readiness", "Check how clear and complete your CV is."),
    ("3", "Skills Assessment", "Take a personalized skills assessment based on the career path you choose."),
    ("4", "Business Case", "Solve a small real-world data problem."),
    ("5", "Mock Interview", "Practise answering common interview questions."),
    ("6", "Readiness Report", "See your strengths and gaps, with next steps."),
]

CSS = """
<style>
.block-container { max-width: 900px; padding-top: 2.5rem; }
.lh-brand { color: #C792FF; font-weight: 700; letter-spacing: 0.12em;
            font-size: 0.85rem; text-transform: uppercase; }
.lh-title { font-size: 2.4rem; font-weight: 800; line-height: 1.15;
            margin: 0.4rem 0 0.6rem 0; color: #F7F3FF; }
.lh-tagline { font-size: 1.1rem; color: rgba(239,234,252,0.74); margin-bottom: 1.5rem; }
.lh-grid { display: flex; flex-wrap: wrap; gap: 12px; margin: 0.5rem 0 1.5rem 0; }
.lh-card { flex: 1 1 150px; background: rgba(255,255,255,0.065); border-radius: 14px;
           padding: 16px; border: 1px solid rgba(255,255,255,0.12); }
.lh-num { background: #C792FF; color: #fff; width: 28px; height: 28px;
          border-radius: 50%; display: flex; align-items: center;
          justify-content: center; font-weight: 700; margin-bottom: 8px; }
.lh-card-title { font-weight: 700; color: #F7F3FF; margin-bottom: 4px; }
.lh-card-text { font-size: 0.9rem; color: rgba(239,234,252,0.74); }
.lh-disclaimer { background: rgba(255,193,99,0.10); border-left: 4px solid #F0B429;
                 padding: 12px 16px; border-radius: 8px; font-size: 0.9rem;
                 color: #FFE8B5; margin-top: 1.5rem; }
</style>
"""


def _stage_cards_html() -> str:
    """Build the HTML for the 5 stage cards (no indentation on purpose,
    because indented lines would be treated as code by Markdown)."""
    cards = []
    for number, title, text in STAGES:
        cards.append(
            f'<div class="lh-card"><div class="lh-num">{number}</div>'
            f'<div class="lh-card-title">{title}</div>'
            f'<div class="lh-card-text">{text}</div></div>'
        )
    return '<div class="lh-grid">' + "".join(cards) + "</div>"


def render() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown('<div class="lh-brand">LeadHer Career Quest</div>', unsafe_allow_html=True)
    st.markdown('<div class="lh-title">Could You Pass Your Own Hiring Process?</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="lh-tagline">Discover your strengths. Identify your gaps. '
        "Build your readiness.</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Your 6-stage journey")
    st.markdown(_stage_cards_html(), unsafe_allow_html=True)

    # on_click runs go_to("career_goal") before the page reruns,
    # so the app shows the next page right away.
    st.button(
        "Start My Career Quest",
        type="primary",
        on_click=go_to,
        args=("career_goal",),
    )

    st.markdown(
        '<div class="lh-disclaimer"><b>Learning simulation only.</b> '
        "LeadHer Career Quest is an educational practice tool, not a real "
        "recruitment test. Your results reflect your performance in this "
        "simulation only and say nothing about real hiring decisions.</div>",
        unsafe_allow_html=True,
    )
