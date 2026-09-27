"""Simple page navigation using Streamlit session state.

The current page name is stored in st.session_state["page"].
app.py reads it and shows the matching page.
"""
import streamlit as st

DEFAULT_PAGE = "landing"

# Every page in the app, in journey order.
# Note: the old standalone "profile" page has been folded into
# "career_goal", which is now Step 1 (career goal + skill map + a short
# personal-info form) - see views/career_goal.py.
PAGE_NAMES = [
    "landing",
    "career_goal",
    "cv_readiness",
    "assessment",
    "case_challenge",
    "interview",
    "report",
]

# Pages that are already built with their own real page.
# (Phase 2: "report" - the Career Readiness Map - is now built too, so
# every page in PAGE_NAMES has a real implementation.)
BUILT_PAGES = list(PAGE_NAMES)

# Kept for backward compatibility with anything that still imports this;
# it's always empty now that every page is built.
PLACEHOLDER_PAGES = [name for name in PAGE_NAMES if name not in BUILT_PAGES]


def init_state() -> None:
    """Create the 'page' key the first time the app runs."""
    if "page" not in st.session_state:
        st.session_state["page"] = DEFAULT_PAGE


def go_to(page_name: str) -> None:
    """Switch to another page. Used as a button callback."""
    if page_name not in PAGE_NAMES:
        raise ValueError(f"Unknown page: {page_name!r}")
    st.session_state["page"] = page_name


def current_page() -> str:
    """Return the name of the page that should be shown."""
    return st.session_state.get("page", DEFAULT_PAGE)
