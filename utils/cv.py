"""CV Readiness analysis: rule-based section/keyword detection.

No AI APIs are used anywhere in this file — every check here is plain
text matching, so the scoring is transparent and easy to explain to a
student. The uploaded PDF itself is never saved to disk; only the
small analysis result below is kept, and only in st.session_state
(temporary browser-session memory).
"""
import re

# Session-state key for the analysis result (not the file itself).
CV_ANALYSIS_KEY = "cv_analysis"

# Extra safety net in front of Streamlit's own upload-size limit
# (see .streamlit/config.toml -> maxUploadSize).
MAX_FILE_SIZE_MB = 5

# Section name -> phrases that suggest that section is present.
SECTION_KEYWORDS = {
    "Education": ["education", "academic background", "university", "degree"],
    "Skills": ["skills", "technical skills", "competencies", "tools"],
    "Experience": ["experience", "work experience", "employment", "internship"],
    "Projects": ["projects", "project experience", "personal projects"],
    "Certifications": ["certification", "certifications", "certificate", "licenses"],
    "Achievements": ["achievements", "awards", "honors", "honours", "accomplishments"],
}

# Action verbs that suggest active, results-oriented wording.
ACTION_VERBS = [
    "managed", "developed", "analyzed", "analysed", "created", "led",
    "designed", "implemented", "improved", "built", "organized",
    "organised", "coordinated", "conducted", "researched", "presented",
    "automated", "optimized", "optimised", "collaborated", "delivered",
    "planned", "trained", "mentored",
]

# Numbers, percentages, currency, counts - signs of measurable results.
QUANT_PATTERN = re.compile(
    r"\d+%|\$\s?\d+|\b\d+[,.]?\d*\s?(hours|hrs|days|weeks|months|years|"
    r"students|users|clients|people|projects|members|times|x)\b|\b\d+\b",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
LINKEDIN_PATTERN = re.compile(r"linkedin\.com/\S+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"github\.com/\S+", re.IGNORECASE)


def extract_text_from_pdf(uploaded_file) -> str:
    """Return the text found in an uploaded PDF (empty string if none).

    Raises ValueError with a message that is safe to show the user
    directly if the file can't be read at all.
    """
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(uploaded_file)
    except (PdfReadError, Exception) as exc:  # pypdf raises a few error types
        raise ValueError(
            "That PDF could not be read. It may be corrupted or damaged."
        ) from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")  # some PDFs use a blank owner password
        except Exception as exc:
            raise ValueError(
                "This PDF is password-protected and can't be read."
            ) from exc

    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:
            continue  # skip a single broken page instead of failing the file

    return "\n".join(pages_text).strip()


def detect_sections(text: str) -> dict:
    """Return {section_name: True/False} for each section we look for."""
    text_lower = text.lower()
    return {
        section: any(phrase in text_lower for phrase in phrases)
        for section, phrases in SECTION_KEYWORDS.items()
    }


def detect_contact_info(text: str) -> dict:
    """Return which contact details were found in the text."""
    return {
        "email": bool(EMAIL_PATTERN.search(text)),
        "phone": bool(PHONE_PATTERN.search(text)),
        "linkedin": bool(LINKEDIN_PATTERN.search(text)),
        "github": bool(GITHUB_PATTERN.search(text)),
    }


def detect_action_verbs(text: str) -> list:
    """Return the list of known action verbs found in the text."""
    text_lower = text.lower()
    return sorted(v for v in ACTION_VERBS if re.search(rf"\b{v}\b", text_lower))


def count_quantifiers(text: str) -> int:
    """Count numbers/percentages/etc. that suggest measurable results."""
    return len(QUANT_PATTERN.findall(text))


def _points(count: int, cap: int, max_points: int) -> int:
    """Scale a count up to `cap` into a 0..max_points score."""
    return round(min(count, cap) / cap * max_points)


def score_cv(text: str) -> dict:
    """Run every check and build the full CV Readiness result.

    Returns a dict with:
      total_score   - 0-100
      breakdown     - list of (category, points, max_points)
      strengths     - list of short positive messages
      improvements  - list of short suggestions
    """
    sections = detect_sections(text)
    contact = detect_contact_info(text)
    verbs = detect_action_verbs(text)
    quant_count = count_quantifiers(text)
    word_count = len(text.split())

    breakdown = []
    strengths = []
    improvements = []

    # Contact information (10 pts) - email, phone, LinkedIn/GitHub
    contact_hits = sum(contact.values())
    breakdown.append(("Contact information", _points(contact_hits, 3, 10), 10))
    if contact["email"]:
        strengths.append("An email address was found.")
    else:
        improvements.append("Add an email address so recruiters can reach you.")
    if contact["phone"]:
        strengths.append("A phone number was found.")
    else:
        improvements.append("Add a phone number.")
    if contact["linkedin"] or contact["github"]:
        strengths.append("A LinkedIn or GitHub link was found.")
    else:
        improvements.append("Consider adding a LinkedIn or GitHub link.")

    # Education (10 pts)
    edu_points = 10 if sections["Education"] else 0
    breakdown.append(("Education", edu_points, 10))
    if sections["Education"]:
        strengths.append("An Education section was detected.")
    else:
        improvements.append("Add an Education section with your university and degree.")

    # Skills (15 pts)
    skills_points = 15 if sections["Skills"] else 0
    breakdown.append(("Skills", skills_points, 15))
    if sections["Skills"]:
        strengths.append("A Skills section was detected.")
    else:
        improvements.append(
            "Add a Skills section listing tools like Excel, SQL, Python or Power BI."
        )

    # Experience / Projects (20 pts) - projects count just as much as jobs
    has_exp_or_proj = sections["Experience"] or sections["Projects"]
    breakdown.append(("Experience / Projects", 20 if has_exp_or_proj else 0, 20))
    if has_exp_or_proj:
        strengths.append(
            "Experience or project work was detected. Internships, personal "
            "projects, coursework and volunteering all count here."
        )
    else:
        improvements.append(
            "Add an Experience or Projects section - class projects, "
            "internships, or volunteer work are all good evidence."
        )

    # Action-oriented wording (15 pts)
    verb_points = _points(len(verbs), 6, 15)
    breakdown.append(("Action-oriented wording", verb_points, 15))
    if verbs:
        example = ", ".join(verbs[:5])
        strengths.append(f"Found {len(verbs)} action verb(s), e.g. {example}.")
    else:
        improvements.append(
            "Start bullet points with action verbs like 'developed', 'led', or 'analyzed'."
        )

    # Quantifiable achievements (15 pts)
    quant_points = _points(quant_count, 5, 15)
    breakdown.append(("Quantifiable achievements", quant_points, 15))
    if quant_count > 0:
        strengths.append(f"Found {quant_count} number(s) or measurable result(s).")
    else:
        improvements.append(
            "Add numbers where you can, e.g. 'analyzed 500+ survey responses' "
            "or 'improved accuracy by 15%'."
        )

    # Relevant extra sections (10 pts) - Certifications / Achievements
    extra_sections = sum(sections[s] for s in ("Certifications", "Achievements"))
    breakdown.append(("Relevant sections", _points(extra_sections, 2, 10), 10))
    if extra_sections:
        strengths.append("Additional sections like Certifications or Achievements were found.")
    else:
        improvements.append("Consider adding Certifications or Achievements if you have any.")

    # Length & readability (5 pts)
    if 150 <= word_count <= 1000:
        length_points = 5
    elif word_count > 0:
        length_points = 2
    else:
        length_points = 0
    breakdown.append(("Length & readability", length_points, 5))
    if length_points == 5:
        strengths.append("The CV length looks reasonable.")
    elif word_count < 150:
        improvements.append("The CV looks quite short - consider adding more detail.")
    else:
        improvements.append("The CV looks long - consider trimming it to the most relevant points.")

    total_score = sum(points for _, points, _ in breakdown)

    return {
        "total_score": total_score,
        "breakdown": breakdown,
        "strengths": strengths,
        "improvements": improvements,
    }


# =============================================================================
# Presentation-layer regrouping for the "CV X-Ray" screen (Phase 2)
# =============================================================================
# This groups the SAME 8 raw categories above into 5 meaningful dimensions
# for display. It does not change scoring at all - total_score and the raw
# breakdown are untouched; this is purely how the numbers are presented.
DIMENSION_GROUPS = {
    "Structure": ["Contact information", "Education", "Relevant sections", "Length & readability"],
    "Evidence": ["Experience / Projects"],
    "Career Relevance": ["Skills"],
    "Clarity": ["Action-oriented wording"],
    "Accomplishment Strength": ["Quantifiable achievements"],
}


def dimension_breakdown(result: dict) -> list:
    """Regroup result['breakdown'] into the 5 CV X-Ray dimensions.

    Returns a list of (dimension_name, points, max_points, pct) in a
    fixed, readable order.
    """
    raw = {name: (points, max_points) for name, points, max_points in result["breakdown"]}
    dims = []
    for dim_name, raw_names in DIMENSION_GROUPS.items():
        points = sum(raw[n][0] for n in raw_names if n in raw)
        max_points = sum(raw[n][1] for n in raw_names if n in raw)
        pct = round(100 * points / max_points) if max_points else 0
        dims.append((dim_name, points, max_points, pct))
    return dims
