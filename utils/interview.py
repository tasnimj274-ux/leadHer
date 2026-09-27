"""Mock Interview: loading questions/role context, deterministic follow-up
questions, and transparent rule-based scoring.

No AI/API is used anywhere here. Scoring works the same way as the Skills
Assessment and Business Case: plain, explainable rules (keyword and
pattern matching), not an attempt at real language understanding. It
measures performance in this interview simulation only, and is not a
prediction of hiring success.

Session-state keys used by views/interview.py:
  interview_questions - the 5-question sequence for this attempt
  interview_answers   - {question_id: {"text", "mode", "word_count", ...}}
  interview_followups - {question_id: {"question": str, "answer": str} or None}
  interview_results   - the final scored result, once complete
"""
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUESTIONS_FILE = DATA_DIR / "interview_questions.json"
CASES_FILE = DATA_DIR / "interview_cases.json"
ROLE_PROFILES_FILE = DATA_DIR / "role_profiles.json"

QUESTIONS_KEY = "interview_questions"
ANSWERS_KEY = "interview_answers"
FOLLOWUPS_KEY = "interview_followups"
RESULTS_KEY = "interview_results"
INDEX_KEY = "interview_index"
STAGE_KEY = "interview_stage"   # "answer" or "followup" within the current question

STAGE_LABELS = ["Introduction", "Experience", "Role Knowledge", "Real-World Problem", "Pressure / Situational"]

# Points per question for each scoring dimension (5 questions x these = the
# totals in the spec: Relevance 25, Evidence 20, Structure 20, Role 20, Professional 15).
DIMENSION_MAX_PER_QUESTION = {
    "relevance": 5,
    "evidence": 4,
    "structure": 4,
    "role_alignment": 4,
    "professional": 3,
}
DIMENSION_LABELS = {
    "relevance": "Answer Relevance",
    "evidence": "Evidence / Examples",
    "structure": "Structure / Clarity",
    "role_alignment": "Role Alignment",
    "professional": "Professional Response",
}
DIMENSION_TOTAL_MAX = {k: v * 5 for k, v in DIMENSION_MAX_PER_QUESTION.items()}   # x5 questions

MIN_WORDS_FOR_FULL_CREDIT = 25   # a solid, developed answer
VERY_SHORT_WORDS = 8             # answers shorter than this are treated as minimal


def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def get_role_profile(track_id: str) -> dict:
    profiles = _load_json(ROLE_PROFILES_FILE)
    return profiles.get(track_id) or profiles.get("general") or {}


def get_case(track_id: str) -> dict:
    cases = _load_json(CASES_FILE)
    return cases.get(track_id) or cases.get("general") or {}


def _question_bank(track_id: str) -> dict:
    bank = _load_json(QUESTIONS_FILE)
    return bank.get(track_id) or bank.get("general") or {}


def _case_data_html_points(case: dict) -> list:
    return case.get("data_points", [])


def build_questions(track_id: str) -> list:
    """Return the fixed 5-question interview sequence for a track."""
    bank = _question_bank(track_id)
    case = get_case(track_id)
    role = get_role_profile(track_id)

    role_keywords = [w.lower() for w in role.get("core_competencies", [])]

    def _q(qid, stage_index, entry, extra_keywords=None):
        keywords = list(entry.get("keywords", [])) + (extra_keywords or [])
        return {
            "id": qid,
            "stage": STAGE_LABELS[stage_index],
            "question": entry["question"],
            "keywords": [k.lower() for k in keywords],
            "role_keywords": role_keywords,
            "allow_followup": qid in ("q1_intro", "q2_experience"),
            "is_case": False,
        }

    questions = []
    if bank.get("q1_intro"):
        questions.append(_q("q1_intro", 0, bank["q1_intro"]))
    if bank.get("q2_experience"):
        questions.append(_q("q2_experience", 1, bank["q2_experience"]))
    if bank.get("q3_role"):
        questions.append(_q("q3_role", 2, bank["q3_role"]))

    # Q4: the real-world data / mini case question.
    case_keywords = [
        "investigate", "compare", "trend", "because", "recommend", "check",
        "assume", "context", "data", "pattern", "explain", "reason",
    ]
    questions.append({
        "id": "q4_case",
        "stage": STAGE_LABELS[3],
        "question": case.get("prompt", "Look at the data below. What do you notice, and what would you recommend?"),
        "keywords": case_keywords,
        "role_keywords": role_keywords,
        "allow_followup": False,
        "is_case": True,
        "case_title": case.get("title", ""),
        "case_context": case.get("context", ""),
        "case_data_label": case.get("data_label", ""),
        "case_data_points": _case_data_html_points(case),
        "case_source_name": case.get("source_name", ""),
        "case_source_url": case.get("source_url", ""),
        "case_source_date": case.get("source_date", ""),
    })

    if bank.get("q5_situational"):
        questions.append(_q("q5_situational", 4, bank["q5_situational"]))

    return questions


# =============================================================================
# Deterministic follow-up questions (no AI - simple signal matching)
# =============================================================================

_PROJECT_WORDS = re.compile(r"\b(project|assignment|case|campaign|dataset|report|app|dashboard)\b", re.I)
_TEAM_WORDS = re.compile(r"\b(team|group|colleague|classmate|members|together|we)\b", re.I)
_EVIDENCE_HINTS = re.compile(
    r"\b(led|built|created|analyzed|managed|organized|designed|developed|\d+"
    r"|percent|%|result|outcome|because)\b", re.I,
)


def get_followup(question: dict, answer_text: str) -> str:
    """Return a follow-up question string, or '' if none applies.

    Simple deterministic rules - no AI is used to "understand" the answer,
    only to look for a few plain signals in the text.
    """
    if not question.get("allow_followup"):
        return ""
    text = (answer_text or "").strip()
    word_count = len(text.split())

    if word_count < 6:
        return "Could you walk me through that in a little more detail?"
    if not _EVIDENCE_HINTS.search(text):
        return "Can you give me one concrete example, with what you actually did?"
    if _PROJECT_WORDS.search(text):
        return "Tell me specifically what YOUR contribution was, versus the rest of the team."
    if _TEAM_WORDS.search(text):
        return "What did you do when the team disagreed about something?"
    if word_count < 15:
        return "Could you walk me through that in a little more detail?"
    return ""


# =============================================================================
# Rule-based content scoring
# =============================================================================

_UNPROFESSIONAL_RE = re.compile(
    r"\b(idk|dunno|whatever|shut up|stupid|dumb|lol|lmao|wtf)\b", re.I
)
_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%?")


def _combined_text(answer_text: str, followup_answer: str) -> str:
    parts = [t.strip() for t in (answer_text, followup_answer) if t and t.strip()]
    return " ".join(parts)


def _keyword_hits(text_lower: str, keywords: list) -> int:
    hits = 0
    for kw in keywords:
        if not kw:
            continue
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text_lower):
            hits += 1
    return hits


def _score_relevance(text: str, text_lower: str, keywords: list) -> tuple:
    word_count = len(text.split())
    if word_count == 0:
        return 0, "No answer was given."
    hits = _keyword_hits(text_lower, keywords)
    if word_count < VERY_SHORT_WORDS:
        points = min(1, hits)
        note = "The answer was very short, so it's hard to tell if it addressed the question."
    elif hits >= 4:
        points = 5
        note = "Clearly addressed the question with relevant, on-topic content."
    elif hits >= 2:
        points = 4
        note = "Mostly on-topic, touching several relevant points."
    elif hits >= 1:
        points = 3
        note = "Somewhat on-topic, but could connect more directly to the question."
    else:
        points = 2 if word_count >= MIN_WORDS_FOR_FULL_CREDIT else 1
        note = "The connection to the specific question wasn't very clear."
    return points, note


def _score_evidence(text: str, text_lower: str) -> tuple:
    indicators = 0
    if _NUMBER_RE.search(text):
        indicators += 1
    if re.search(r"\b(for example|specifically|in one case|one time|when i)\b", text_lower):
        indicators += 1
    if re.search(r"\b(i led|i built|i created|i analyzed|i managed|i organized|i designed|i developed|i coordinated)\b", text_lower):
        indicators += 1
    if re.search(r"\b(result|outcome|so that|as a result|which meant|and this)\b", text_lower):
        indicators += 1
    points = min(4, indicators)
    if points >= 3:
        note = "Backed up the answer with a specific example and a result."
    elif points >= 1:
        note = "Gave some evidence, but a specific example with a clear result would help."
    else:
        note = "No concrete example or evidence was given - this is the biggest opportunity here."
    return points, note


def _score_structure(text: str) -> tuple:
    word_count = len(text.split())
    sentences = [s for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    if word_count == 0:
        return 0, "No answer was given."
    if word_count < VERY_SHORT_WORDS:
        return 1, "The answer was too short to show much structure."
    points = 0
    if len(sentences) >= 2:
        points += 2
    elif len(sentences) == 1 and word_count >= 15:
        points += 1
    if MIN_WORDS_FOR_FULL_CREDIT <= word_count <= 180:
        points += 2
    elif word_count > 8:
        points += 1
    points = min(4, points)
    if points >= 3:
        note = "Well organized, with a clear beginning, middle and end."
    elif points >= 2:
        note = "Reasonably organized; breaking it into a few clear steps would help."
    else:
        note = "Consider structuring the answer as: the situation, what you did, and the result."
    return points, note


def _score_role_alignment(text_lower: str, keywords: list, role_keywords: list) -> tuple:
    hits = _keyword_hits(text_lower, keywords) + _keyword_hits(text_lower, role_keywords)
    points = min(4, hits)
    if points >= 3:
        note = "Language and examples fit well with what this role actually involves."
    elif points >= 1:
        note = "Some relevant language, but could connect more directly to this role's day-to-day work."
    else:
        note = "Try to use language and examples closer to this specific role's core skills."
    return points, note


def _score_professional(text: str, text_lower: str) -> tuple:
    word_count = len(text.split())
    if word_count == 0:
        return 0, "No answer was given."
    if _UNPROFESSIONAL_RE.search(text_lower):
        return 0, "A few words or phrases came across as informal for an interview setting."
    if word_count < 4:
        return 1, "The response was too brief to come across as a complete, professional answer."
    points = 3 if word_count >= 8 else 2
    note = "Came across as clear and professional." if points == 3 else "Reasonably professional, though quite brief."
    return points, note


def _score_question(question: dict, answer_text: str, followup_answer: str) -> dict:
    text = _combined_text(answer_text, followup_answer)
    text_lower = text.lower()

    rel_pts, rel_note = _score_relevance(text, text_lower, question["keywords"])
    ev_pts, ev_note = _score_evidence(text, text_lower)
    st_pts, st_note = _score_structure(text)
    role_pts, role_note = _score_role_alignment(text_lower, question["keywords"], question["role_keywords"])
    pro_pts, pro_note = _score_professional(text, text_lower)

    return {
        "question_id": question["id"],
        "stage": question["stage"],
        "question": question["question"],
        "word_count": len(text.split()),
        "dimensions": {
            "relevance": {"points": rel_pts, "max": DIMENSION_MAX_PER_QUESTION["relevance"], "note": rel_note},
            "evidence": {"points": ev_pts, "max": DIMENSION_MAX_PER_QUESTION["evidence"], "note": ev_note},
            "structure": {"points": st_pts, "max": DIMENSION_MAX_PER_QUESTION["structure"], "note": st_note},
            "role_alignment": {"points": role_pts, "max": DIMENSION_MAX_PER_QUESTION["role_alignment"], "note": role_note},
            "professional": {"points": pro_pts, "max": DIMENSION_MAX_PER_QUESTION["professional"], "note": pro_note},
        },
        "total": rel_pts + ev_pts + st_pts + role_pts + pro_pts,
    }


def score_interview(questions: list, answers: dict, followups: dict) -> dict:
    """Score all 5 answers. Returns overall total, per-dimension totals,
    per-question detail, and plain-language strengths/development areas.
    """
    per_question = []
    for q in questions:
        ans = answers.get(q["id"], {})
        followup = followups.get(q["id"]) or {}
        result = _score_question(q, ans.get("text", ""), followup.get("answer", ""))
        per_question.append(result)

    dimension_totals = {dim: 0 for dim in DIMENSION_MAX_PER_QUESTION}
    for result in per_question:
        for dim, detail in result["dimensions"].items():
            dimension_totals[dim] += detail["points"]

    overall = sum(dimension_totals.values())

    # Strengths / development areas by dimension, expressed as a percentage
    # of that dimension's total possible points.
    dim_pct = {
        dim: round(100 * dimension_totals[dim] / DIMENSION_TOTAL_MAX[dim]) if DIMENSION_TOTAL_MAX[dim] else 0
        for dim in dimension_totals
    }
    strengths = [DIMENSION_LABELS[d] for d, pct in dim_pct.items() if pct >= 75]
    development = sorted(
        (d for d, pct in dim_pct.items() if pct < 75), key=lambda d: dim_pct[d]
    )
    development_labels = [DIMENSION_LABELS[d] for d in development]

    if not strengths:
        strengths = [DIMENSION_LABELS[max(dim_pct, key=dim_pct.get)]]

    return {
        "overall": overall,
        "dimension_totals": dimension_totals,
        "dimension_max": DIMENSION_TOTAL_MAX,
        "dimension_pct": dim_pct,
        "strengths": strengths,
        "development_areas": development_labels,
        "per_question": per_question,
    }


def practice_suggestions(results: dict) -> list:
    """3-5 concrete next steps, driven by which dimensions scored lowest."""
    tips_by_dim = {
        "relevance": "Before answering, restate the question in your own words to make sure your answer stays on-topic.",
        "evidence": "Prepare 2-3 specific stories in advance (a project, a challenge, a leadership moment) with a clear result for each.",
        "structure": "Practice the Situation -> Action -> Result shape: briefly set the scene, explain what you did, then the outcome.",
        "role_alignment": "Read a few real job postings for this career track and note the exact words they use - reuse that language naturally.",
        "professional": "Record yourself answering out loud once, and review it for clarity, completeness and tone.",
    }
    ordered = sorted(results["dimension_pct"], key=lambda d: results["dimension_pct"][d])
    tips = [tips_by_dim[d] for d in ordered[:4]]
    tips.append("Do a full practice run of this Mock Interview again after you've worked on the above.")
    return tips[:5]
