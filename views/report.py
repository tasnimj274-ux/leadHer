"""Career Readiness Map (Step 7) - Phase 2.

Pulls together whatever the student has actually completed so far -
career_goal, skill_profile, cv_analysis, assessment_results,
case_results, interview_results, and the voice fluency result - and
never invents a number for a stage that wasn't completed; those show
"Not completed" (or "Insufficient data" for fluency) instead.

Naming note (per product guidance): the overall figures here are
called "Career Quest Performance" / "Career Readiness Snapshot" -
never "Employability Score" or "Hiring Probability".
"""
import streamlit as st

from utils.cv import CV_ANALYSIS_KEY, dimension_breakdown
from utils.navigation import go_to
from utils.quest import render as render_quest
from utils.voice import FLUENCY_RESULT_KEY
from views.career_goal import CAREER_GOAL_KEY, SKILL_PROFILE_KEY

try:
    import plotly.graph_objects as go
except ImportError:  # pragma: no cover - plotly is a listed dependency
    go = None

CSS = """
<style>
.block-container { max-width: 900px; padding-top: 2.2rem; }
.lh-brand { color: #C792FF; font-weight: 700; letter-spacing: 0.12em;
            font-size: 0.85rem; text-transform: uppercase; }
.lh-hero { background: linear-gradient(135deg, #C792FF 0%, #9B6DE0 100%);
           border-radius: 18px; padding: 26px; text-align: center; color: #fff;
           margin: 0.6rem 0 1.2rem 0; }
.lh-hero-title { font-size: 2rem; font-weight: 800; }
.lh-hero-sub { font-size: 1rem; opacity: 0.92; margin-top: 4px; }
.lh-goal-line { color: #C792FF; font-weight: 600; margin: 0.6rem 0 0.2rem 0; }
.lh-section-label { font-size: 0.78rem; font-weight: 700; color: #C792FF;
                     text-transform: uppercase; letter-spacing: 0.06em; margin: 1.1rem 0 0.4rem 0; }
.lh-progress-row { display: flex; justify-content: space-between; font-size: 0.92rem;
                    padding: 7px 2px; border-bottom: 1px solid rgba(199,146,255,0.14); }
.lh-status-done { color: #66E3AE; font-weight: 700; }
.lh-status-missing { color: #B7ADC9; font-weight: 600; }
.lh-unlock-box { background: rgba(57, 211, 145, 0.10); border-radius: 12px; padding: 12px 16px; border: 1px solid rgba(57,211,145,0.18);
                 margin: 0.4rem 0; border: 1px solid rgba(57,211,145,0.18); }
.lh-quest-box { background: rgba(255,255,255,0.065); border-radius: 12px; padding: 12px 16px;
                margin: 0.4rem 0; border: 1px solid rgba(255,255,255,0.12); }
.lh-day-row { display: flex; gap: 10px; padding: 8px 2px; border-bottom: 1px solid rgba(199,146,255,0.14); }
.lh-day-num { font-weight: 800; color: #C792FF; min-width: 52px; }
.lh-disclaimer { background: rgba(255,193,99,0.10); border-left: 4px solid #F0B429;
                 padding: 10px 14px; border-radius: 8px; font-size: 0.85rem;
                 color: #FFE8B5; margin: 1rem 0; }
</style>
"""


def _goal_line(goal: dict) -> str:
    text = goal.get("track_label", "")
    if goal.get("specific_goal"):
        text += f" — {goal['specific_goal']}"
    return text


def _quest_progress_rows() -> list:
    """[(label, done_bool, detail_str)] - read straight from session
    state, nothing invented."""
    ss = st.session_state
    cv = ss.get(CV_ANALYSIS_KEY)
    assessment = ss.get("assessment_results")
    case = ss.get("case_results")
    interview = ss.get("interview_results")
    fluency = ss.get(FLUENCY_RESULT_KEY)

    rows = [
        ("📄 CV X-Ray", bool(cv), f'{cv["total_score"]} / 100' if cv else "Not completed"),
        ("🧠 Skill Challenge", bool(assessment),
         f'{assessment["overall_score"]}%' if assessment else "Not completed"),
        ("💼 Case Room", bool(case),
         f'{case["overall_score"]} / 100' if case else "Not completed"),
        ("🎤 Interview Room", bool(interview),
         f'{interview["overall"]} / 100' if interview else "Not completed"),
    ]
    if fluency is None:
        rows.append(("🗣️ English Speaking Simulation", False, "Not completed"))
    elif fluency.get("insufficient"):
        rows.append(("🗣️ English Speaking Simulation", False, "Insufficient data"))
    else:
        rows.append(("🗣️ English Speaking Simulation", True, f'{fluency["overall"]} / 100'))
    return rows


def _skill_map_radar(skill_profile: dict) -> None:
    """A Plotly radar of the student's own Step-1 skill self-ratings
    (1-5 -> 0-100%). This is self-reported calibration, shown as its
    own honestly-labeled chart - it is not mixed with the different,
    incompatible competency sets used by Assessment/Case/Interview."""
    if not skill_profile:
        st.info("No skill map was recorded yet - revisit Career Goal to build one.")
        return
    if go is None:
        # Fallback if plotly somehow isn't available - a simple table.
        for skill, level in skill_profile.items():
            st.markdown(f'<div class="lh-progress-row"><span>{skill}</span>'
                        f'<span>{level} / 5</span></div>', unsafe_allow_html=True)
        return

    labels = list(skill_profile.keys())
    values = [v * 20 for v in skill_profile.values()]  # 1-5 -> 20-100
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        line_color="#C792FF",
        fillcolor="rgba(109, 63, 200, 0.25)",
        name="Self-rated skill level",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        margin=dict(l=30, r=30, t=20, b=20),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Self-rated skill calibration from Career Goal (Step 1) - not a scored assessment.")


def _collect_strengths_and_gaps() -> tuple:
    """Pull the ALREADY-COMPUTED strengths/development_areas lists out
    of each stage's real results - never recomputed or invented here."""
    ss = st.session_state
    strengths, gaps = [], []

    assessment = ss.get("assessment_results")
    if assessment:
        strengths += [f"{c} (Skill Challenge)" for c in assessment.get("strengths", [])]
        gaps += [f"{c} (Skill Challenge)" for c in assessment.get("development_areas", [])]

    case = ss.get("case_results")
    if case:
        strengths += [f"{c} (Case Room)" for c in case.get("strengths", [])]
        gaps += [f"{c} (Case Room)" for c in case.get("development_areas", [])]

    interview = ss.get("interview_results")
    if interview:
        from utils.interview import DIMENSION_LABELS
        strengths += [f"{DIMENSION_LABELS.get(d, d)} (Interview)" for d in interview.get("strengths", [])]
        gaps += [f"{DIMENSION_LABELS.get(d, d)} (Interview)"
                 for d in interview.get("development_areas", [])]

    cv = ss.get(CV_ANALYSIS_KEY)
    if cv:
        for name, points, max_points, pct in dimension_breakdown(cv):
            if pct >= 70:
                strengths.append(f"{name} (CV)")
            else:
                gaps.append(f"{name} (CV)")

    return strengths, gaps


def _seven_day_plan(gaps: list) -> list:
    """A deterministic, rule-based 7-day plan built from actual weak
    areas found across the quest so far - no scores are invented."""
    if not gaps:
        return [
            "Every stage you've completed met the strength threshold. Use this "
            "week to keep your CV and portfolio up to date, and try a fresh "
            "career track to broaden your Career Readiness Map."
        ] * 1
    unique_gaps = list(dict.fromkeys(gaps))  # de-duplicate, keep order
    plan = []
    for day in range(7):
        focus = unique_gaps[day % len(unique_gaps)]
        plan.append(
            f"Spend 20-30 minutes on **{focus}** - review one short resource on it, "
            "then do one small practice task and note what felt hardest."
        )
    return plan


def render() -> None:
    st.session_state["_report_viewed"] = True

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="lh-brand">LeadHer Career Quest</div>', unsafe_allow_html=True)
    render_quest("report")

    goal = st.session_state.get(CAREER_GOAL_KEY)
    if not goal:
        st.write("Please complete Career Goal first to see your Career Readiness Map.")
        st.button("Choose my career goal", type="primary", on_click=go_to, args=("career_goal",))
        st.button("← Back to start", on_click=go_to, args=("landing",))
        return

    st.markdown(
        '<div class="lh-hero">'
        '<div class="lh-hero-title">🏆 QUEST COMPLETE</div>'
        '<div class="lh-hero-sub">Your Career Readiness Map</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="lh-goal-line">Career goal: {_goal_line(goal)}</div>',
                unsafe_allow_html=True)

    st.markdown('<div class="lh-section-label">Quest Progress</div>', unsafe_allow_html=True)
    for label, done, detail in _quest_progress_rows():
        status_html = (f'<span class="lh-status-done">✓ {detail}</span>' if done
                        else f'<span class="lh-status-missing">{detail}</span>')
        st.markdown(f'<div class="lh-progress-row"><span>{label}</span>{status_html}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="lh-section-label">Your Skill Map</div>', unsafe_allow_html=True)
    _skill_map_radar(st.session_state.get(SKILL_PROFILE_KEY))

    strengths, gaps = _collect_strengths_and_gaps()

    st.markdown('<div class="lh-section-label">YOU\'VE UNLOCKED</div>', unsafe_allow_html=True)
    if strengths:
        for s in strengths[:8]:
            st.markdown(f'<div class="lh-unlock-box">🟢 {s}</div>', unsafe_allow_html=True)
    else:
        st.info("Complete CV X-Ray, Skill Challenge, Case Room or Interview Room to unlock strengths here.")

    st.markdown('<div class="lh-section-label">NEXT QUESTS</div>', unsafe_allow_html=True)
    if gaps:
        for g in gaps[:8]:
            st.markdown(f'<div class="lh-quest-box">🔓 {g}</div>', unsafe_allow_html=True)
    else:
        st.write("No development gaps identified yet from what you've completed so far.")

    st.markdown('<div class="lh-section-label">Your 7-Day Development Plan</div>', unsafe_allow_html=True)
    for i, tip in enumerate(_seven_day_plan(gaps), start=1):
        st.markdown(
            f'<div class="lh-day-row"><span class="lh-day-num">Day {i}</span><span>{tip}</span></div>',
            unsafe_allow_html=True,
        )

    st.caption(
        "This Career Readiness Snapshot reflects your performance in these "
        "practice simulations only. It is not an employability score, a "
        "hiring score, or a prediction of hiring probability."
    )
    st.button("← Back to start", on_click=go_to, args=("landing",))
