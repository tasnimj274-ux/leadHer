"""Business Case Challenge: loading and rule-based scoring.

No AI/API is used anywhere here - scoring is plain percent-correct
per competency, same approach as the Skills Assessment. Case data,
answers and results are kept only in st.session_state (see
views/case_challenge.py), never written to disk or a database.
"""
import json
from pathlib import Path

CASES_FILE = Path(__file__).resolve().parent.parent / "data" / "cases.json"

CASE_DATA_KEY = "case_data"
CASE_ANSWERS_KEY = "case_answers"
CASE_INDEX_KEY = "case_index"
CASE_RESULTS_KEY = "case_results"

# A competency at or above this percentage is shown as a strength.
STRENGTH_THRESHOLD = 70


def _load_case_bank() -> dict:
    """Read data/cases.json. Returns {} if missing/invalid so the page
    can show a friendly message instead of crashing."""
    try:
        with open(CASES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _is_valid_case(case: dict) -> bool:
    """Basic structural check so a malformed case.json entry can't
    crash the page - just gets treated as missing."""
    if not isinstance(case, dict):
        return False
    if not (case.get("title") and case.get("context") and case.get("problem")):
        return False
    questions = case.get("questions")
    if not isinstance(questions, list) or not (3 <= len(questions) <= 4):
        return False
    for question in questions:
        if not isinstance(question, dict):
            return False
        if not question.get("question") or not question.get("competency"):
            return False
        options = question.get("options")
        if not isinstance(options, list) or question.get("correct_answer") not in options:
            return False
    return True


def get_case_for_track(track_id: str) -> dict | None:
    """Return the case for a track, falling back to 'general' if the
    track is missing or its case is malformed. Returns None only if
    neither the track nor 'general' is usable."""
    bank = _load_case_bank()
    case = bank.get(track_id)
    if _is_valid_case(case):
        return case
    fallback = bank.get("general")
    if _is_valid_case(fallback):
        return fallback
    return None


def score_case(case: dict, answers: dict) -> dict:
    """Score a completed case: overall performance and a per-competency,
    per-question breakdown with explanations for feedback.

    Returns a dict with:
      overall_score       - 0-100
      competency_scores   - {competency: percent}
      strengths            - competencies >= STRENGTH_THRESHOLD
      development_areas    - competencies below STRENGTH_THRESHOLD
      question_results     - per-question detail for feedback text
    """
    questions = case["questions"]
    competency_totals = {}  # competency -> [correct, total]
    correct_count = 0
    question_results = []

    for question in questions:
        competency = question["competency"]
        totals = competency_totals.setdefault(competency, [0, 0])
        totals[1] += 1

        selected = answers.get(question["id"])
        is_correct = selected == question["correct_answer"]
        if is_correct:
            totals[0] += 1
            correct_count += 1

        question_results.append(
            {
                "question": question["question"],
                "competency": competency,
                "selected_answer": selected,
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
                "explanation": question["explanation"],
            }
        )

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
        "question_results": question_results,
    }


# =============================================================================
# Presentation-layer mapping to 5 canonical dimensions (Phase 2, Case Room)
# =============================================================================
# data/cases.json uses its own per-track competency names (e.g. "Data
# Interpretation", "HR Judgment"). This maps each track's 4 competencies
# onto the 5 canonical dimensions requested for the Case Room results
# screen, WITHOUT changing scoring: score_case() above and cases.json are
# both untouched. A track's case only has 4 competencies, so exactly one
# of the 5 canonical dimensions is left unassessed per case - shown as
# "Not assessed in this case" rather than guessed at.
CANONICAL_DIMENSIONS = [
    "Problem Understanding", "Evidence Use", "Decision Making",
    "Business Reasoning", "Career-Specific Skill",
]

_TRACK_DIMENSION_MAP = {
    "data_analytics": {
        "Problem Understanding": "Problem Understanding",
        "Data Interpretation": "Evidence Use",
        "Metric Selection": "Career-Specific Skill",
        "Business Reasoning": "Business Reasoning",
    },
    "business_analysis": {
        "Problem Understanding": "Problem Understanding",
        "Process Analysis": "Evidence Use",
        "Stakeholder Communication": "Career-Specific Skill",
        "Prioritization": "Decision Making",
    },
    "marketing": {
        "Problem Understanding": "Problem Understanding",
        "Customer Insight": "Evidence Use",
        "Segmentation": "Career-Specific Skill",
        "Decision Making": "Decision Making",
    },
    "finance": {
        "Problem Understanding": "Problem Understanding",
        "Numerical Reasoning": "Evidence Use",
        "Risk Awareness": "Career-Specific Skill",
        "Financial Reasoning": "Business Reasoning",
    },
    "hr": {
        "Problem Understanding": "Problem Understanding",
        "Communication": "Evidence Use",
        "HR Judgment": "Career-Specific Skill",
        "Decision Making": "Decision Making",
    },
    "technology": {
        "Debugging / Problem Solving": "Problem Understanding",
        "Logical Reasoning": "Evidence Use",
        "Technical Prioritization": "Career-Specific Skill",
        "Decision Making": "Decision Making",
    },
    "supply_chain": {
        "Problem Understanding": "Problem Understanding",
        "Operations Reasoning": "Evidence Use",
        "Inventory Thinking": "Career-Specific Skill",
        "Prioritization": "Decision Making",
    },
    "general": {
        "Problem Understanding": "Problem Understanding",
        "Communication": "Evidence Use",
        "Numerical / Business Reasoning": "Business Reasoning",
        "Decision Making": "Decision Making",
    },
}


def to_canonical_dimensions(competency_scores: dict, track_id: str) -> dict:
    """Map {track-specific competency: pct} onto the 5 canonical Case
    Room dimensions. A dimension with no mapped competency for this
    track comes back as None (render as "Not assessed in this case")."""
    mapping = _TRACK_DIMENSION_MAP.get(track_id, {})
    out = {dim: None for dim in CANONICAL_DIMENSIONS}
    for competency, pct in competency_scores.items():
        canonical = mapping.get(competency)
        if canonical:
            out[canonical] = pct
    return out
