"""Profile data helpers: options, validation, and temporary storage.

The profile lives only in st.session_state (browser-session memory).
It is lost when the user closes or refreshes the tab. Nothing is saved
to disk or to a database.

Note: the old fixed 4-tool skill list (Excel/SQL/Python/Power BI) that
used to live here has been replaced by the career-specific skill map in
data/career_paths.py, captured as st.session_state["skill_profile"] on
the Career Quest (Step 1) page. Nothing downstream ever read the old
per-profile "skills" dict, so removing it here doesn't affect Step 2-6.
"""
import re

import streamlit as st

STUDY_YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year", "Graduate"]

PROFILE_KEY = "profile"

# A simple check: something@something.something (no spaces).
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_profile(first_name: str, university: str, email: str) -> list[str]:
    """Return a list of friendly error messages (empty list = all good)."""
    errors = []
    if not first_name.strip():
        errors.append("Please enter your first name.")
    if not university.strip():
        errors.append("Please enter your university.")
    # Email is optional, but if it is filled in it should look like an email.
    if email.strip() and not EMAIL_PATTERN.match(email.strip()):
        errors.append(
            "That email address doesn't look right. "
            "Please check it, or leave it blank."
        )
    return errors


def save_profile(profile: dict) -> None:
    """Keep the profile in session_state (temporary memory only)."""
    st.session_state[PROFILE_KEY] = profile


def get_profile() -> dict:
    """Return the saved profile, or an empty dict if none exists yet."""
    return st.session_state.get(PROFILE_KEY, {})
