"""Skill Challenge page (Phase 2 redesign of the old "Skills Assessment").

Questions are still loaded from data/questions.json based on the career
track chosen on Career Goal, and scoring is still the same simple,
transparent percent-correct calculation per competency - no AI/API is
used, and nothing about the scoring engine below changed in Phase 2.

New in Phase 2: the last question is swapped for a short, real-world,
publicly-sourced data question from data/real_world_cases.json (see
that file for source/URL/date), and the flow is framed as a set of
missions (Observe / Investigate / Decide / Explain) rather than a plain
quiz list.

Session-state keys used here (unchanged from Phase 1):
  assessment_questions - the question list for this attempt
  assessment_answers   - {question_id: selected_option_text}
  assessment_index     - which question is currently shown
  assessment_results   - the final scored result, once complete
"""
import json
from pathlib import Path

import streamlit as st

from utils.navigation import go_to
from utils.quest import render as render_quest
from views.career_goal import CAREER_GOAL_KEY

QUESTIONS_FILE = Path(__file__).resolve().parent.parent / "data" / "questions.json"
REAL_WORLD_FILE = Path(__file__).resolve().parent.parent / "data" / "real_world_cases.json"

QUESTIONS_KEY = "assessment_questions"
ANSWERS_KEY = "assessment_answers"
INDEX_KEY = "assessment_index"
RESULTS_KEY = "assessment_results"

# A competency at or above this percentage is shown as a strength.
STRENGTH_THRESHOLD = 70

# Purely cosmetic "mission" framing cycled across the questions.
MISSION_CYCLE = [
    ("Observe", "Take in the situation before jumping to conclusions."),
    ("Investigate", "Dig into the details that actually matter."),
    ("Decide", "Choose the action best supported by the evidence."),
    ("Explain", "Connect your choice back to the reasoning."),
]

CSS = """
<style>
.block-container { max-width: 900px; padding-top: 2.2rem; }
.lh-brand { color: #C792FF; font-weight: 700; letter-spacing: 0.12em;
            font-size: 0.85rem; text-transform: uppercase; }
.lh-page-title { font-size: 1.9rem; font-weight: 800; color: #F7F3FF;
                 margin: 0.3rem 0 0.3rem 0; }
.lh-page-sub { color: rgba(239,234,252,0.74); margin-bottom: 1rem; }
.lh-goal-line { color: #C792FF; font-weight: 600; margin-bottom: 0.2rem; }
.lh-mission-tag { display: inline-block; background: rgba(199,146,255,0.18); color: #EAD9FF; border: 1px solid rgba(199,146,255,0.28);
                  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
                  text-transform: uppercase; padding: 3px 10px; border-radius: 999px;
                  margin: 0.4rem 0 0.3rem 0; }
.lh-mission-sub { color: #B9B0CA; font-size: 0.82rem; margin-bottom: 0.6rem; }
.lh-progress { color: rgba(239,234,252,0.74); font-size: 0.9rem; margin-bottom: 0.6rem; }
.lh-real-world-tag { display: inline-block; background: #E7F4EC; color: #1E8F5F;
                      font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em;
                      text-transform: uppercase; padding: 3px 10px; border-radius: 999px;
                      margin-bottom: 0.5rem; }
.lh-data-box { background: rgba(255,255,255,0.065); border-radius: 14px; padding: 16px 20px;
               border: 1px solid rgba(255,255,255,0.12); margin-bottom: 1rem; font-size: 0.9rem;
               color: #F1EAFE; line-height: 1.5; backdrop-filter: blur(10px); }
.lh-source { font-size: 0.78rem; color: #B9B0CA; margin-top: 8px; }
.lh-score-box { background: rgba(255,255,255,0.065); border-radius: 14px; padding: 20px;
                text-align: center; margin: 1rem 0; border: 1px solid rgba(255,255,255,0.12); }
.lh-score-num { font-size: 2.6rem; font-weight: 800; color: #C792FF; }
.lh-score-label { color: rgba(239,234,252,0.74); font-size: 0.9rem; margin-top: 4px; }
.lh-row { display: flex; justify-content: space-between; font-size: 0.9rem;
          padding: 5px 2px; border-bottom: 1px solid rgba(199,146,255,0.14); }
</style>
"""


def _load_question_bank() -> dict:
    """Read data/questions.json. Returns {} if missing/invalid so the
    page can show a friendly message instead of crashing."""
    try:
        with open(QUESTIONS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _load_real_world_bank() -> dict:
    try:
        with open(REAL_WORLD_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _real_world_question(track_id: str) -> dict | None:
    """Return one real-data question for this track, tagged with its
    source, or None if the data file is missing/malformed."""
    bank = _load_real_world_bank()
    case = bank.get(track_id) or bank.get("general")
    if not case or not case.get("questions"):
        return None
    q = dict(case["questions"][0])
    q["is_real_world"] = True
    q["case_title"] = case.get("case_title", "")
    q["scenario"] = case.get("scenario", "")
    q["data_pack"] = case.get("data_pack", [])
    q["source_name"] = case.get("source_name", "")
    q["source_url"] = case.get("source_url", "")
    q["source_date"] = case.get("source_date", "")
    q["simulation_note"] = case.get("simulation_note", "")
    return q


def _questions_for_track(track_id: str) -> list:
    """Return up to 8 questions for a track: 7 from the existing
    question bank (falling back to 'general' if the track is missing)
    plus 1 real-world data question as the final mission."""
    bank = _load_question_bank()
    questions = bank.get(track_id) or bank.get("general") or []
    valid = [
        q for q in questions
        if isinstance(q, dict)
        and q.get("question")
        and q.get("competency")
        and q.get("correct_answer") in q.get("options", [])
    ]
    valid = valid[:7]

    real_world = _real_world_question(track_id)
    if real_world:
        valid.append(real_world)
    else:
        # Fall back gracefully if the real-world data file is ever
        # missing/malformed, instead of shrinking the challenge.
        bank_fallback = bank.get(track_id) or bank.get("general") or []
        if len(bank_fallback) > 7:
            valid.append(bank_fallback[7])

    return valid[:8]


def _score_assessment(questions: list, answers: dict) -> dict:
    """Build a simple, transparent score: percent correct overall and
    per competency, plus which competencies count as strengths."""
    competency_totals = {}  # competency -> [correct, total]
    correct_count = 0

    for question in questions:
        competency = question["competency"]
        totals = competency_totals.setdefault(competency, [0, 0])
        totals[1] += 1
        if answers.get(question["id"]) == question["correct_answer"]:
            totals[0] += 1
            correct_count += 1

    competency_scores = {
        competency: round(100 * correct / total) if total else 0
        for competency, (correct, total) in competency_totals.items()
    }
    total_questions = len(questions)
    overall_score = round(100 * correct_count / total_questions) if total_questions else 0

    strengths = [c for c, pct in competency_scores.items() if pct >= STRENGTH_THRESHOLD]
    development_areas = [c for c, pct in competency_scores.items() if pct < STRENGTH_THRESHOLD]

    return {
        "overall_score": overall_score,
        "competency_scores": competency_scores,
        "strengths": strengths,
        "development_areas": development_areas,
        "total_questions": total_questions,
        "correct_count": correct_count,
    }


def _goal_line(goal: dict) -> str:
    text = goal.get("track_label", "")
    if goal.get("specific_goal"):
        text += f" — {goal['specific_goal']}"
    return text


def _real_world_box_html(question: dict) -> str:
    points = "".join(f"<li>{p}</li>" for p in question.get("data_pack", []))
    source = question.get("source_name", "")
    source_url = question.get("source_url", "")
    source_date = question.get("source_date", "")
    link = f'<a href="{source_url}" target="_blank">{source}</a>' if source_url else source
    return (
        f'<div class="lh-real-world-tag">📡 Real-world data</div>'
        f'<div class="lh-data-box">'
        f'<b>{question.get("case_title", "")}</b><br>'
        f'{question.get("scenario", "")}<br><br>'
        f'<ul>{points}</ul>'
        f'<div class="lh-source">Source: {link}'
        f'{" — " + source_date if source_date else ""}. '
        f'{question.get("simulation_note", "")}</div>'
        f"</div>"
    )


def _render_question(goal: dict, questions: list, index: int, answers: dict) -> None:
    current = questions[index]

    st.markdown(f'<div class="lh-goal-line">Career goal: {_goal_line(goal)}</div>',
                unsafe_allow_html=True)
    mission_name, mission_sub = MISSION_CYCLE[index % len(MISSION_CYCLE)]
    st.markdown(f'<div class="lh-mission-tag">Mission {index + 1:02d} — {mission_name}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="lh-mission-sub">{mission_sub}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="lh-progress">Task {index + 1} of {len(questions)}</div>',
                unsafe_allow_html=True)

    if current.get("is_real_world"):
        st.markdown(_real_world_box_html(current), unsafe_allow_html=True)

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
        key=f"assessment_choice_{current['id']}",
    )

    is_last = index == len(questions) - 1
    button_label = "Finish Skill Challenge" if is_last else "Next Mission →"

    if st.button(button_label, type="primary"):
        if choice is None:
            st.error("Please select an answer before continuing.")
        else:
            answers[current["id"]] = choice
            st.session_state[ANSWERS_KEY] = answers
            if is_last:
                st.session_state[RESULTS_KEY] = _score_assessment(questions, answers)
            else:
                st.session_state[INDEX_KEY] = index + 1
            st.rerun()


def _render_results(goal: dict, results: dict) -> None:
    st.markdown(f'<div class="lh-goal-line">Career goal: {_goal_line(goal)}</div>',
                unsafe_allow_html=True)
    st.markdown("### 🧠 Skill Challenge Complete")

    st.markdown(
        f'<div class="lh-score-box">'
        f'<div class="lh-score-num">{results["overall_score"]}%</div>'
        f'<div class="lh-score-label">Career Quest Performance in this simulation '
        f'({results["correct_count"]} / {results["total_questions"]} correct) '
        f"&mdash; not a hiring probability.</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Competency breakdown**")
    rows = "".join(
        f'<div class="lh-row"><span>{comp}</span><span>{pct}%</span></div>'
        for comp, pct in results["competency_scores"].items()
    )
    st.markdown(rows, unsafe_allow_html=True)

    st.markdown("### Strengths")
    if results["strengths"]:
        for comp in results["strengths"]:
            st.markdown(f"- Strong current demonstrated performance in **{comp}**.")
    else:
        st.write("No competency reached the strength threshold in this attempt yet.")

    st.markdown("### Development Areas")
    if results["development_areas"]:
        for comp in results["development_areas"]:
            st.markdown(f"- Consider practicing **{comp}** further.")
    else:
        st.write("Every competency met the strength threshold in this simulation.")

    st.caption(
        "This reflects your current demonstrated performance in this assessment "
        "only, not a prediction of hiring success."
    )

    st.button(
        "Continue to Case Room →",
        type="primary",
        on_click=go_to,
        args=("case_challenge",),
    )
    st.button("← Back to start", on_click=go_to, args=("landing",))


def render() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="lh-brand">LeadHer Career Quest</div>', unsafe_allow_html=True)
    render_quest("assessment")
    st.markdown('<div class="lh-page-title">🧠 Skill Challenge</div>', unsafe_allow_html=True)

    goal = st.session_state.get(CAREER_GOAL_KEY)
    if not goal:
        st.markdown(
            '<div class="lh-page-sub">Please choose a career goal before starting '
            "the Skill Challenge.</div>",
            unsafe_allow_html=True,
        )
        st.button(
            "Choose my career goal",
            type="primary",
            on_click=go_to,
            args=("career_goal",),
        )
        st.button("← Back to start", on_click=go_to, args=("landing",))
        return

    if RESULTS_KEY in st.session_state:
        _render_results(goal, st.session_state[RESULTS_KEY])
        return

    if QUESTIONS_KEY not in st.session_state:
        questions = _questions_for_track(goal["track_id"])
        if not questions:
            st.error(
                "The Skill Challenge for this career path couldn't be loaded "
                "right now. Please try again, or choose a different career path."
            )
            st.button(
                "Choose a different career goal",
                on_click=go_to,
                args=("career_goal",),
            )
            st.button("← Back to start", on_click=go_to, args=("landing",))
            return
        st.session_state[QUESTIONS_KEY] = questions
        st.session_state[ANSWERS_KEY] = {}
        st.session_state[INDEX_KEY] = 0

    questions = st.session_state[QUESTIONS_KEY]
    answers = st.session_state[ANSWERS_KEY]
    index = st.session_state.get(INDEX_KEY, 0)

    # Safety net: if the index ever drifts out of range, finish gracefully
    # instead of raising an IndexError.
    if index >= len(questions):
        st.session_state[RESULTS_KEY] = _score_assessment(questions, answers)
        st.rerun()
        return

    _render_question(goal, questions, index, answers)
