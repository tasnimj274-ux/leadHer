"""Step 1 - Career Quest onboarding: career goal + skill map + short profile.

This single page now covers what used to be two separate pages
(the old "profile" static form and the old "career_goal" picker):

  MISSION 01  What do you want to become?      -> career persona
  MISSION 02  Your current skill map            -> skill_profile
  (quick)     A few details about you           -> profile

Everything still lives only in st.session_state - nothing is written
to disk or a database.

Session-state contract kept for Step 2-6 (unchanged from before):
  st.session_state["career_goal"] = {
      "track_id": str,        # used by assessment/case_challenge/interview
      "track_label": str,     # shown as plain text on later pages
      "specific_goal": str,
      "persona_id": str,      # new - lets this page re-select the right card
  }

New in this rebuild:
  st.session_state["skill_profile"] = {"<skill name>": 1-5, ...}
  st.session_state["profile"]       = {"first_name", "university",
                                        "study_year", "email"} (via utils.profile)

Nothing downstream previously read the old profile "skills" dict, so
none of Step 2-6 needed to change.
"""
import streamlit as st

from data.career_paths import CAREER_PERSONAS, PROFICIENCY_LABELS, PROFICIENCY_LEVELS, get_persona
from utils.navigation import go_to
from utils.profile import STUDY_YEARS, get_profile, save_profile, validate_profile
from utils.quest import render as render_quest

CAREER_GOAL_KEY = "career_goal"
SKILL_PROFILE_KEY = "skill_profile"

# Which persona is currently highlighted while the student is still on
# this page (kept separate from the committed CAREER_GOAL_KEY so nothing
# downstream changes until "Continue" is actually pressed).
PERSONA_STATE_KEY = "career_persona_id"
# Skill ratings collected per persona while browsing, so switching
# between career cards doesn't throw away what was already answered.
RATINGS_CACHE_KEY = "_cq_skill_ratings_cache"

CSS = """
<style>
.block-container { max-width: 900px; padding-top: 2.2rem; }
.lh-brand { color: #DDBBFF; text-shadow: 0 0 18px rgba(200,150,255,0.25); font-weight: 700; letter-spacing: 0.12em;
            font-size: 0.85rem; text-transform: uppercase; }
.lh-mission-tag { display: inline-block; background: rgba(199,146,255,0.18); color: #EAD9FF; border: 1px solid rgba(199,146,255,0.28);
                  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
                  text-transform: uppercase; padding: 3px 10px; border-radius: 999px;
                  margin: 0.6rem 0 0.5rem 0; }
.lh-page-title { font-size: 1.9rem; font-weight: 800; color: #F7F3FF;
                 margin: 0.1rem 0 0.3rem 0; }
.lh-page-sub { color: rgba(239,234,252,0.72); margin-bottom: 1rem; }
.lh-persona-desc { font-size: 0.78rem; color: rgba(239,234,252,0.60); margin: -6px 0 14px 2px; }
.lh-unlock-banner { background: linear-gradient(135deg, rgba(112,63,200,0.88), rgba(255,103,177,0.45)); border: 1px solid rgba(255,255,255,0.14); box-shadow: 0 18px 45px rgba(0,0,0,0.24);
                     border-radius: 16px; padding: 18px 20px; margin: 0.4rem 0 1.2rem 0;
                     color: #fff; }
.lh-unlock-tag { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em;
                 text-transform: uppercase; opacity: 0.85; }
.lh-unlock-title { font-size: 1.5rem; font-weight: 800; margin: 2px 0 4px 0; }
.lh-unlock-text { font-size: 0.9rem; opacity: 0.95; }
.lh-legend { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 8px 14px;
             font-size: 0.78rem; color: rgba(239,234,252,0.74); margin-bottom: 0.8rem; }
.lh-divider { border-top: 1px solid rgba(255,255,255,0.10); margin: 1.4rem 0 1rem 0; }
.lh-section-label { font-size: 0.75rem; font-weight: 700; color: #C792FF;
                     text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.lh-privacy { background: rgba(255,255,255,0.06); border-left: 4px solid #B97CFF;
              padding: 10px 14px; border-radius: 8px; font-size: 0.85rem;
              color: rgba(242,236,255,0.78); margin: 1rem 0; }
.lh-hint { color: rgba(221,199,255,0.68); font-size: 0.85rem; margin: 0.2rem 0 1rem 0; }
div[data-testid="stButton"] > button { width: 100%; text-align: left; border-radius: 14px;
             padding: 14px 16px; border: 1px solid rgba(255,255,255,0.10); background: rgba(255,255,255,0.05); backdrop-filter: blur(12px);
             font-weight: 700; color: #F7F3FF; }
div[data-testid="stButton"] > button:hover { border-color: #C792FF; background: rgba(255,255,255,0.08);
             color: #C792FF; }
</style>
"""


def _index_of(options: list, value, default: int = 0) -> int:
    return options.index(value) if value in options else default


def _clear_old_progress() -> None:
    """Reset any in-progress or completed assessment/case when the
    underlying track changes, so results from a different track don't
    carry over."""
    for key in ("assessment_questions", "assessment_answers",
                "assessment_index", "assessment_results",
                "case_data", "case_answers", "case_index", "case_results"):
        st.session_state.pop(key, None)


def _choose_persona(persona_id: str) -> None:
    st.session_state[PERSONA_STATE_KEY] = persona_id


def _render_career_grid(selected_id: str | None) -> None:
    st.markdown('<div class="lh-mission-tag">Mission 01</div>', unsafe_allow_html=True)
    st.markdown('<div class="lh-page-title">🎯 What do you want to become?</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="lh-page-sub">Choose the path closest to your goal. '
        "We'll map out the skills that matter for it next.</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    for i, persona in enumerate(CAREER_PERSONAS):
        marker = "✅ " if persona["id"] == selected_id else f'{persona["icon"]}  '
        with cols[i % 2]:
            st.button(
                f'{marker}{persona["label"]}',
                key=f"persona_btn_{persona['id']}",
                on_click=_choose_persona,
                args=(persona["id"],),
            )
            st.markdown(
                f'<div class="lh-persona-desc">{persona["description"]}</div>',
                unsafe_allow_html=True,
            )

    if not selected_id:
        st.markdown('<div class="lh-hint">👆 Tap a path to unlock your skill map.</div>',
                    unsafe_allow_html=True)


def _render_unlocked_form(persona: dict) -> None:
    st.markdown(
        f'<div class="lh-unlock-banner">'
        f'<div class="lh-unlock-tag">🔓 Career path unlocked</div>'
        f'<div class="lh-unlock-title">{persona["icon"]} {persona["label"]}</div>'
        f'<div class="lh-unlock-text">Let\'s map the skills you\'ll need for your journey.</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.button("🔄 Choose a different path", on_click=_choose_persona, args=(None,))

    saved_goal = st.session_state.get(CAREER_GOAL_KEY, {})
    saved_profile = get_profile()
    ratings_cache = st.session_state.setdefault(RATINGS_CACHE_KEY, {})
    persona_ratings = ratings_cache.get(persona["id"], {})
    # If the currently-committed goal already points at this persona,
    # pre-fill from the real skill profile too (e.g. user came back later).
    if saved_goal.get("persona_id") == persona["id"]:
        persona_ratings = {**persona_ratings, **st.session_state.get(SKILL_PROFILE_KEY, {})}

    with st.form("career_quest_form"):
        st.markdown('<div class="lh-mission-tag">Mission 02</div>', unsafe_allow_html=True)
        st.markdown('<div class="lh-page-title">⚡ Your current skill map</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="lh-page-sub">Based on the career path you selected, here\'s a '
            "practical skill framework for this MVP. Tell us where you are now - there's "
            "no wrong answer, this just helps us find your development gaps.</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="lh-legend">'
            + " &nbsp;·&nbsp; ".join(f'{lvl["value"]} {lvl["label"]}' for lvl in PROFICIENCY_LEVELS)
            + "</div>",
            unsafe_allow_html=True,
        )

        skill_choices = {}
        for skill in persona["skills"]:
            default_value = persona_ratings.get(skill, 3)
            default_label = next(
                (lvl["label"] for lvl in PROFICIENCY_LEVELS if lvl["value"] == default_value),
                PROFICIENCY_LABELS[2],
            )
            skill_choices[skill] = st.select_slider(
                skill,
                options=PROFICIENCY_LABELS,
                value=default_label,
                key=f"skill_{persona['id']}_{skill}",
            )

        specific_goal = st.text_input(
            "Your specific goal (optional)",
            value=saved_goal.get("specific_goal", "") if saved_goal.get("persona_id") == persona["id"] else "",
            placeholder="e.g. Junior Data Analyst at a fintech startup",
            max_chars=80,
        )

        st.markdown('<div class="lh-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lh-section-label">👤 A few details about you</div>',
                    unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        first_name = col1.text_input("First name *", value=saved_profile.get("first_name", ""), max_chars=50)
        university = col2.text_input("University *", value=saved_profile.get("university", ""), max_chars=100)
        col3, col4 = st.columns(2)
        study_year = col3.selectbox(
            "Study year", STUDY_YEARS, index=_index_of(STUDY_YEARS, saved_profile.get("study_year"))
        )
        email = col4.text_input("Email (optional)", value=saved_profile.get("email", ""), max_chars=100)

        submitted = st.form_submit_button("Continue to CV Readiness →", type="primary")

    if submitted:
        errors = validate_profile(first_name, university, email)
        if errors:
            for message in errors:
                st.error(message)
            return

        new_track_id = persona["track_id"]
        if new_track_id != saved_goal.get("track_id"):
            _clear_old_progress()

        # Cache this persona's ratings (by numeric value) for later re-visits.
        numeric_ratings = {
            skill: next(lvl["value"] for lvl in PROFICIENCY_LEVELS if lvl["label"] == label)
            for skill, label in skill_choices.items()
        }
        ratings_cache[persona["id"]] = numeric_ratings
        st.session_state[RATINGS_CACHE_KEY] = ratings_cache

        st.session_state[CAREER_GOAL_KEY] = {
            "track_id": new_track_id,
            "track_label": persona["label"],
            "specific_goal": specific_goal.strip(),
            "persona_id": persona["id"],
        }
        st.session_state[SKILL_PROFILE_KEY] = numeric_ratings
        save_profile(
            {
                "first_name": first_name.strip(),
                "university": university.strip(),
                "study_year": study_year,
                "email": email.strip(),
            }
        )
        go_to("cv_readiness")
        st.rerun()


def render() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="lh-brand">LeadHer Career Quest</div>', unsafe_allow_html=True)

    if PERSONA_STATE_KEY not in st.session_state:
        # First visit this session: pre-select whatever was already
        # committed (e.g. the user came back to this page later).
        # After that, an explicit "choose a different path" reset (which
        # sets this to None) is respected on every later rerun.
        st.session_state[PERSONA_STATE_KEY] = st.session_state.get(CAREER_GOAL_KEY, {}).get("persona_id")
    selected_id = st.session_state.get(PERSONA_STATE_KEY)

    render_quest("skill_map" if selected_id else "career_goal")
    _render_career_grid(selected_id)

    if selected_id:
        persona = get_persona(selected_id)
        _render_unlocked_form(persona)

    st.markdown(
        '<div class="lh-privacy">Your career goal, skill map and details are used only '
        "for this career-readiness simulation, and are not stored beyond this browser "
        "session.</div>",
        unsafe_allow_html=True,
    )
    st.button("← Back to start", on_click=go_to, args=("landing",))
