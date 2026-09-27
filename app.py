"""LeadHer Career Quest - main entry point.

Run with:  streamlit run app.py
"""
import streamlit as st

from utils.navigation import current_page, init_state
from utils.theme import inject_game_background
from views import assessment, career_goal, case_challenge, cv_readiness, interview, landing, report

# set_page_config must be the first Streamlit call.
st.set_page_config(
    page_title="LeadHer Career Quest",
    page_icon="🎯",
    layout="centered",
)

init_state()
inject_game_background()

# Map each page name to the function that draws it. Every stage is a real,
# built page as of Phase 2 (see utils/navigation.PAGE_NAMES for the order).
PAGES = {
    "landing": landing.render,
    "career_goal": career_goal.render,
    "cv_readiness": cv_readiness.render,
    "assessment": assessment.render,
    "case_challenge": case_challenge.render,
    "interview": interview.render,
    "report": report.render,
}

# Look up the current page and run it (fall back to landing if unknown).
PAGES.get(current_page(), landing.render)()
