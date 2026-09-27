"""Case Room page (Phase 2 redesign of the old "Business Case Challenge").

Still loads one career-specific business case from data/cases.json
(based on the track chosen on Career Goal), walks the student through
its decision questions one at a time, and scores the result with the
same plain rule-based percent-correct logic as before - no AI/API
involved, and utils/case.py's scoring itself is untouched.

New in Phase 2: the case is presented as a staged "Case Room"
experience (Client Brief -> Data Pack -> Stakeholder Message -> each
Decision Point -> final Recommendation screen), and the results screen
also shows a 5-dimension canonical breakdown (Problem Understanding /
Evidence Use / Decision Making / Business Reasoning / Career-Specific
Skill) alongside the original per-competency breakdown.

Session-state keys used here (unchanged from Phase 1):
  case_data    - the case dict for this attempt
  case_answers - {question_id: selected_option_text}
  case_index   - which question is currently shown
  case_results - the final scored result, once complete
"""
import streamlit as st

from utils.case import (
    CANONICAL_DIMENSIONS,
    CASE_ANSWERS_KEY,
    CASE_DATA_KEY,
    CASE_INDEX_KEY,
    CASE_RESULTS_KEY,
    get_case_for_track,
    score_case,
    to_canonical_dimensions,
)
from utils.quest import render as render_quest
from utils.navigation import go_to
from views.career_goal import CAREER_GOAL_KEY

CSS = """
<style>
.block-container { max-width: 900px; padding-top: 2.2rem; }
.lh-brand { color: #C792FF; font-weight: 700; letter-spacing: 0.12em;
            font-size: 0.85rem; text-transform: uppercase; }
.lh-page-title { font-size: 1.9rem; font-weight: 800; color: #F7F3FF;
                 margin: 0.3rem 0 0.3rem 0; }
.lh-goal-line { color: #C792FF; font-weight: 600; margin-bottom: 0.2rem; }
.lh-case-title { font-size: 1.3rem; font-weight: 700; color: #F7F3FF;
                 margin: 0.4rem 0 0.4rem 0; }
.lh-case-meta { color: #B9B0CA; font-size: 0.82rem; margin-bottom: 0.6rem; }
.lh-section-label { font-size: 0.72rem; font-weight: 700; color: #C792FF;
                     text-transform: uppercase; letter-spacing: 0.06em; margin: 10px 0 4px 0; }
.lh-case-box { background: rgba(255,255,255,0.065); border-radius: 14px; padding: 18px 20px;
               border: 1px solid rgba(255,255,255,0.12); margin-bottom: 1rem; font-size: 0.92rem;
               color: #F1EAFE; line-height: 1.5; }
.lh-case-box b { color: #F7F3FF; }
.lh-progress { color: rgba(239,234,252,0.74); font-size: 0.9rem; margin-bottom: 0.6rem; }
.lh-decision-tag { display: inline-block; background: rgba(199,146,255,0.18); color: #EAD9FF; border: 1px solid rgba(199,146,255,0.28);
                    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
                    text-transform: uppercase; padding: 3px 10px; border-radius: 999px;
                    margin-bottom: 0.5rem; }
.lh-score-box { background: rgba(255,255,255,0.065); border-radius: 14px; padding: 20px;
                text-align: center; margin: 1rem 0; border: 1px solid rgba(255,255,255,0.12); }
.lh-score-num { font-size: 2.6rem; font-weight: 800; color: #C792FF; }
.lh-score-label { color: rgba(239,234,252,0.74); font-size: 0.9rem; margin-top: 4px; }
.lh-row { display: flex; justify-content: space-between; font-size: 0.9rem;
          padding: 5px 2px; border-bottom: 1px solid rgba(199,146,255,0.14); }
.lh-row.na { color: #B7ADC9; }
.lh-feedback { font-size: 0.88rem; color: #F1EAFE; margin: 4px 0 10px 0; }
</style>
"""


def _goal_line(goal: dict) -> str:
    text = goal.get("track_label", "")
    if goal.get("specific_goal"):
        text += f" — {goal['specific_goal']}"
    return text


def _case_briefing_html(case: dict) -> str:
    data_points = "".join(f"<li>{point}</li>" for point in case["data_points"])
    return (
        f'<div class="lh-section-label">📁 Client Brief</div>'
        f'<div class="lh-case-box">{case["context"]}</div>'
        f'<div class="lh-section-label">📊 Data Pack</div>'
        f'<div class="lh-case-box"><ul>{data_points}</ul></div>'
        f'<div class="lh-section-label">💬 Stakeholder Message</div>'
        f'<div class="lh-case-box"><b>"{case["problem"]}"</b></div>'
    )


def _render_question(goal: dict, case: dict, index: int, answers: dict) -> None:
    questions = case["questions"]
    current = questions[index]

    st.markdown(f'<div class="lh-goal-line">Career goal: {_goal_line(goal)}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="lh-case-title">💼 Case Room — {case["title"]}</div>',
                unsafe_allow_html=True)

    if index == 0:
        st.markdown(_case_briefing_html(case), unsafe_allow_html=True)
    else:
        with st.expander("📁 Client Brief / 📊 Data Pack / 💬 Stakeholder Message"):
            st.markdown(_case_briefing_html(case), unsafe_allow_html=True)

    st.markdown('<div class="lh-decision-tag">🎯 Decision Point</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="lh-progress">Decision {index + 1} of {len(questions)}</div>',
                unsafe_allow_html=True)
    st.subheader(current["question"])

    previous_answer = answers.get(current["id"])
    prev_index = (
        current["options"].index(previous_answer)
        if previous_answer in current["options"] else None
    )
    choice = st.radio(
        "Choose one answer:",
        current["options"],
        index=prev_index,
        key=f"case_choice_{current['id']}",
    )

    is_last = index == len(questions) - 1
    button_label = "See My Recommendation" if is_last else "Next Decision →"

    if st.button(button_label, type="primary"):
        if choice is None:
            st.error("Please select an answer before continuing.")
        else:
            answers[current["id"]] = choice
            st.session_state[CASE_ANSWERS_KEY] = answers
            if is_last:
                st.session_state[CASE_RESULTS_KEY] = score_case(case, answers)
            else:
                st.session_state[CASE_INDEX_KEY] = index + 1
            st.rerun()


def _render_results(goal: dict, case: dict, results: dict, track_id: str) -> None:
    st.markdown(f'<div class="lh-goal-line">Career goal: {_goal_line(goal)}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="lh-case-title">💼 Case Room — {case["title"]}</div>',
                unsafe_allow_html=True)
    st.markdown("### 📝 Recommendation — Case Complete")

    st.markdown(
        f'<div class="lh-score-box">'
        f'<div class="lh-score-num">{results["overall_score"]} / 100</div>'
        f'<div class="lh-score-label">Case Performance '
        f'({results["correct_count"]} / {results["total_questions"]} correct) '
        f"&mdash; your performance in this business simulation only.</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Breakdown**")
    canonical = to_canonical_dimensions(results["competency_scores"], track_id)
    for dim in CANONICAL_DIMENSIONS:
        pct = canonical[dim]
        if pct is None:
            st.markdown(
                f'<div class="lh-row na"><span>{dim}</span><span>Not assessed in this case</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="lh-row"><span>{dim}</span><span>{pct}%</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("### What you did well")
    if results["strengths"]:
        for comp in results["strengths"]:
            st.markdown(f"- Solid reasoning shown in **{comp}**.")
    else:
        st.write("No competency reached the strength threshold in this attempt yet.")

    st.markdown("### What to improve")
    if results["development_areas"]:
        for comp in results["development_areas"]:
            st.markdown(f"- Consider practicing **{comp}** further.")
    else:
        st.write("Every competency met the strength threshold in this simulation.")

    st.markdown("### Why each answer was strong or weak")
    for item in results["question_results"]:
        icon = "✅" if item["is_correct"] else "📈"
        st.markdown(f"{icon} **{item['competency']}** — {item['question']}")
        st.markdown(f'<div class="lh-feedback">{item["explanation"]}</div>',
                     unsafe_allow_html=True)

    st.caption(
        "This reflects your performance in this business simulation only - it is "
        "not a measure of hiring or employment probability."
    )

    st.button(
        "Continue to Interview Room →",
        type="primary",
        on_click=go_to,
        args=("interview",),
    )
    st.button("← Back to start", on_click=go_to, args=("landing",))


def render() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="lh-brand">LeadHer Career Quest</div>', unsafe_allow_html=True)
    render_quest("case_challenge")
    st.markdown('<div class="lh-page-title">💼 Case Room</div>', unsafe_allow_html=True)

    goal = st.session_state.get(CAREER_GOAL_KEY)
    if not goal:
        st.write("Please choose a career goal before starting the Case Room.")
        st.button(
            "Choose my career goal",
            type="primary",
            on_click=go_to,
            args=("career_goal",),
        )
        st.button("← Back to start", on_click=go_to, args=("landing",))
        return

    if CASE_RESULTS_KEY in st.session_state:
        case = st.session_state.get(CASE_DATA_KEY)
        if case:
            _render_results(goal, case, st.session_state[CASE_RESULTS_KEY], goal["track_id"])
            return
        # Results exist but the case itself is missing (shouldn't normally
        # happen) - clear the stale result and fall through to reload.
        st.session_state.pop(CASE_RESULTS_KEY, None)

    if CASE_DATA_KEY not in st.session_state:
        case = get_case_for_track(goal["track_id"])
        if not case:
            st.error(
                "The Case Room for this career path couldn't be loaded "
                "right now. Please try again, or choose a different career path."
            )
            st.button(
                "Choose a different career goal",
                on_click=go_to,
                args=("career_goal",),
            )
            st.button("← Back to start", on_click=go_to, args=("landing",))
            return
        st.session_state[CASE_DATA_KEY] = case
        st.session_state[CASE_ANSWERS_KEY] = {}
        st.session_state[CASE_INDEX_KEY] = 0

    case = st.session_state[CASE_DATA_KEY]
    answers = st.session_state[CASE_ANSWERS_KEY]
    index = st.session_state.get(CASE_INDEX_KEY, 0)
    questions = case["questions"]

    # Safety net: if the index ever drifts out of range, finish gracefully
    # instead of raising an IndexError.
    if index >= len(questions):
        st.session_state[CASE_RESULTS_KEY] = score_case(case, answers)
        st.rerun()
        return

    _render_question(goal, case, index, answers)
