"""Global Quest UI: the 7-stage progress system shown on every page.

XP/Level here are PURELY engagement/progression indicators - how far
through the quest someone has gone. They are never derived from, and
never displayed as, an assessment/case/interview/CV score. Those real
scores live entirely in utils/cv.py, utils/case.py, utils/interview.py
and views/assessment.py, untouched by this module.

Completion state is read directly from the same session-state keys the
rest of the app already uses (cv_analysis, assessment_results,
case_results, interview_results, career_goal) - nothing new is written
here, so nothing about the existing session-state architecture changes.
"""
import streamlit as st

from utils.cv import CV_ANALYSIS_KEY

STAGES = [
    {"key": "career_goal", "icon": "🎯", "label": "Career Goal", "xp": 100},
    {"key": "skill_map", "icon": "🧩", "label": "Skill Calibration", "xp": 0},  # same page as career_goal
    {"key": "cv_readiness", "icon": "📄", "label": "CV X-Ray", "xp": 150},
    {"key": "assessment", "icon": "🧠", "label": "Skill Challenge", "xp": 150},
    {"key": "case_challenge", "icon": "💼", "label": "Case Room", "xp": 150},
    {"key": "interview", "icon": "🎤", "label": "Interview Room", "xp": 200},
    {"key": "report", "icon": "🏆", "label": "Readiness Map", "xp": 50},
]
MAX_XP = sum(s["xp"] for s in STAGES)  # 800

LEVELS = [
    (0, "Quest Starter"),
    (100, "Career Explorer"),
    (250, "Skill Builder"),
    (400, "Case Strategist"),
    (600, "Interview Ready"),
    (800, "Quest Champion"),
]

CSS = """
<style>
.lh-quest-wrap { margin: 0.2rem 0 1.4rem 0; padding: 12px 14px 14px; border-radius: 18px; background: rgba(17, 16, 40, 0.72); border: 1px solid rgba(255,255,255,0.10); box-shadow: 0 14px 35px rgba(0,0,0,0.22); backdrop-filter: blur(16px); }
.lh-level-row { display: flex; justify-content: space-between; align-items: baseline;
                font-size: 0.78rem; color: rgba(244, 241, 255, 0.72); margin-bottom: 4px; }
.lh-level-name { font-weight: 800; color: #D6B9FF; letter-spacing: 0.04em; text-shadow: 0 0 18px rgba(170,110,255,0.35); text-transform: uppercase; }
.lh-xp-track { background: rgba(255,255,255,0.08); border-radius: 999px; height: 8px; overflow: hidden; margin-bottom: 12px; }
.lh-xp-fill { background: linear-gradient(90deg, #A55CFF, #FF74B6, #5DAFFF); box-shadow: 0 0 18px rgba(196,112,255,0.5); height: 100%; border-radius: 999px; }
.lh-quest { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.lh-quest-step { display: flex; align-items: center; gap: 6px; }
.lh-quest-dot { width: 26px; height: 26px; border-radius: 50%; font-size: 0.85rem;
                display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.lh-quest-dot.done { background: linear-gradient(135deg,#8B5CF6,#FF70B7); color: #fff; box-shadow: 0 0 20px rgba(173,92,255,0.35); }
.lh-quest-dot.active { background: rgba(255,255,255,0.08); color: #F3D8FF; border: 2px solid #C28CFF; box-shadow: 0 0 20px rgba(194,140,255,0.35); animation: cq-pulse 2.2s ease-in-out infinite; }
.lh-quest-dot.locked { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.40); }
.lh-quest-label { font-size: 0.68rem; color: rgba(244,241,255,0.62); white-space: nowrap; }
.lh-quest-label.active { color: #FFFFFF; font-weight: 800; }
.lh-quest-label.locked { color: #B7ADC9; }
.lh-quest-sep { width: 12px; height: 2px; background: linear-gradient(90deg, rgba(167,110,255,0.65), rgba(255,255,255,0.12)); margin: 0 1px; }
@keyframes cq-pulse { 0%,100% { transform: scale(1); box-shadow: 0 0 20px rgba(194,140,255,0.25); } 50% { transform: scale(1.08); box-shadow: 0 0 28px rgba(194,140,255,0.52); } }\n</style>\n"""


def _level_name(xp: int) -> str:
    name = LEVELS[0][1]
    for threshold, label in LEVELS:
        if xp >= threshold:
            name = label
    return name


def _level_number(xp: int) -> int:
    return sum(1 for threshold, _ in LEVELS if xp >= threshold)


def compute_progress() -> dict:
    """Read real completion signals from session_state and turn them
    into engagement XP + per-stage status. Never invents anything."""
    ss = st.session_state
    completed = {
        "career_goal": bool(ss.get("career_goal")),
        "skill_map": bool(ss.get("skill_profile")),
        "cv_readiness": bool(ss.get(CV_ANALYSIS_KEY)),
        "assessment": bool(ss.get("assessment_results")),
        "case_challenge": bool(ss.get("case_results")),
        "interview": bool(ss.get("interview_results")),
        "report": bool(ss.get("_report_viewed")),
    }
    xp = sum(s["xp"] for s in STAGES if completed[s["key"]])
    return {"completed": completed, "xp": xp}


def stage_status(stage_key: str, completed: dict) -> str:
    if completed.get(stage_key):
        return "completed"
    order = [s["key"] for s in STAGES]
    idx = order.index(stage_key)
    prereqs_done = all(completed[k] for k in order[:idx])
    return "active" if prereqs_done else "locked"


def render(current_stage_key: str) -> None:
    """Draw the level/XP bar plus the 7-stage lock/active/completed quest
    trail. `current_stage_key` is one of the STAGES keys."""
    st.markdown(CSS, unsafe_allow_html=True)
    progress = compute_progress()
    xp = progress["xp"]
    completed = dict(progress["completed"])
    # The page currently being viewed always reads as at least "active",
    # even if a not-yet-satisfied prerequisite would otherwise lock it
    # (e.g. someone returns to Career Goal after finishing everything).
    fill_pct = round(100 * xp / MAX_XP) if MAX_XP else 0

    st.markdown(
        f'<div class="lh-quest-wrap">'
        f'<div class="lh-level-row">'
        f'<span class="lh-level-name">Level {_level_number(xp):02d} — {_level_name(xp)}</span>'
        f'<span>XP {xp} / {MAX_XP}</span>'
        f'</div>'
        f'<div class="lh-xp-track"><div class="lh-xp-fill" style="width:{fill_pct}%"></div></div>',
        unsafe_allow_html=True,
    )

    parts = ['<div class="lh-quest">']
    for i, stage in enumerate(STAGES):
        status = stage_status(stage["key"], completed)
        if stage["key"] == current_stage_key and status == "locked":
            status = "active"  # you're here, so it can't be locked for you
        if status == "completed":
            dot_class, content = "done", "✓"
        elif status == "active":
            dot_class, content = "active", stage["icon"]
        else:
            dot_class, content = "locked", "🔒"
        label_class = "active" if stage["key"] == current_stage_key else ("locked" if status == "locked" else "")
        parts.append(
            f'<div class="lh-quest-step">'
            f'<div class="lh-quest-dot {dot_class}">{content}</div>'
            f'<div class="lh-quest-label {label_class}">{stage["label"]}</div>'
            f"</div>"
        )
        if i != len(STAGES) - 1:
            parts.append('<div class="lh-quest-sep"></div>')
    parts.append("</div></div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
