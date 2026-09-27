"""Career-persona configuration for the Career Quest onboarding (Step 1).

This is intentionally a plain data module (not JSON) so it's easy to add
a new persona, skill, or description with a short pull request and no
UI changes.

IMPORTANT - how this connects to the rest of the app:
Skills Assessment, Business Case and Mock Interview each load their
content from data/questions.json, data/cases.json and
data/interview_*.json, keyed by one of 8 underlying "track_id" values:
data_analytics, business_analysis, marketing, finance, hr, technology,
supply_chain, general. Building real question banks / cases / interview
content for a brand-new track is a bigger content task than a UI
refresh, so this file introduces more specific, student-friendly
CAREER PERSONAS (e.g. "Product Manager", "Entrepreneur") for the
"What do you want to become?" screen, each of which maps to the closest
existing track_id for the assessment/case/interview stages. The persona
keeps its own label and its own skill map either way - only the
underlying question bank is shared.

To add a brand-new persona backed by an EXISTING track, just add an
entry to CAREER_PERSONAS below. To support a fully new track end to end,
you'd also need a matching entry in data/questions.json, data/cases.json,
data/interview_questions.json, data/interview_cases.json and
data/role_profiles.json (all keyed by the same track_id).
"""

# 5-level proficiency scale used for every skill in the skill map.
PROFICIENCY_LEVELS = [
    {"value": 1, "label": "Never used it", "blurb": "Brand new to this - and that's a fine place to start."},
    {"value": 2, "label": "Beginner", "blurb": "You've had some exposure, but you're still finding your footing."},
    {"value": 3, "label": "Comfortable", "blurb": "You can use this without much help in everyday situations."},
    {"value": 4, "label": "Strong", "blurb": "You're reliable with this and could help a teammate with it."},
    {"value": 5, "label": "Advanced", "blurb": "You could teach this or use it in a complex, high-stakes task."},
]
PROFICIENCY_LABELS = [level["label"] for level in PROFICIENCY_LEVELS]


def proficiency_blurb(value: int) -> str:
    """Short explanation text for a chosen 1-5 proficiency value."""
    for level in PROFICIENCY_LEVELS:
        if level["value"] == value:
            return level["blurb"]
    return ""


# Each persona is what the student actually picks on screen. "track_id"
# is the underlying content bank used for Assessment / Business Case /
# Mock Interview (see the module docstring above).
CAREER_PERSONAS = [
    {
        "id": "data_analyst",
        "track_id": "data_analytics",
        "label": "Data Analyst",
        "icon": "📊",
        "description": "Turn raw numbers into decisions leaders can act on.",
        "skills": [
            "SQL", "Excel / Spreadsheets", "Data Visualization", "Statistics",
            "Python", "BI Tools", "Business Communication", "Problem Solving",
        ],
    },
    {
        "id": "business_analyst",
        "track_id": "business_analysis",
        "label": "Business Analyst",
        "icon": "🧩",
        "description": "Bridge what the business needs and what gets built.",
        "skills": [
            "Requirements Analysis", "Business Process Mapping", "SQL / Data Analysis",
            "Excel", "Communication", "Stakeholder Management", "Problem Solving", "Presentation",
        ],
    },
    {
        "id": "product_manager",
        "track_id": "business_analysis",
        "label": "Product Manager",
        "icon": "🧭",
        "description": "Decide what gets built next, and why it matters.",
        "skills": [
            "Product Strategy", "User Research", "Product Analytics", "Communication",
            "Prioritization", "Problem Solving", "Stakeholder Management", "Product Thinking",
        ],
    },
    {
        "id": "marketing",
        "track_id": "marketing",
        "label": "Marketing Professional",
        "icon": "📣",
        "description": "Understand customers and communicate value clearly.",
        "skills": [
            "Market Research", "Digital Marketing", "Content Strategy", "Consumer Behaviour",
            "Analytics", "Communication", "Creativity", "Presentation",
        ],
    },
    {
        "id": "finance",
        "track_id": "finance",
        "label": "Finance Professional",
        "icon": "💰",
        "description": "Work with numbers, budgets and financial decisions.",
        "skills": [
            "Financial Analysis", "Excel", "Accounting Fundamentals", "Financial Modelling",
            "Data Analysis", "Communication", "Problem Solving", "Presentation",
        ],
    },
    {
        "id": "hr",
        "track_id": "hr",
        "label": "HR Professional",
        "icon": "🤝",
        "description": "Help people and workplace culture thrive together.",
        "skills": [
            "Recruitment", "Employee Relations", "HR Analytics", "Communication",
            "Interviewing", "Conflict Resolution", "Problem Solving", "Presentation",
        ],
    },
    {
        "id": "supply_chain",
        "track_id": "supply_chain",
        "label": "Supply Chain Professional",
        "icon": "📦",
        "description": "Plan how goods and services move, efficiently.",
        "skills": [
            "Supply Chain Fundamentals", "Inventory Management", "Excel", "Data Analysis",
            "Procurement", "Forecasting", "Problem Solving", "Communication",
        ],
    },
    {
        "id": "technology",
        "track_id": "technology",
        "label": "Technology / Software Professional",
        "icon": "💻",
        "description": "Build and reason carefully about software.",
        "skills": [
            "Programming", "Problem Solving", "Databases", "Software Development",
            "Version Control", "Communication", "Systems Thinking", "Debugging",
        ],
    },
    {
        "id": "entrepreneur",
        "track_id": "general",
        "label": "Entrepreneur",
        "icon": "🚀",
        "description": "Build something new and make it work in the real world.",
        "skills": [
            "Business Strategy", "Financial Literacy", "Sales & Persuasion", "Problem Solving",
            "Resilience", "Networking", "Resourcefulness", "Communication",
        ],
    },
    {
        "id": "exploring",
        "track_id": "general",
        "label": "Other / I'm still exploring",
        "icon": "🔎",
        "description": "Not locked in yet? Start with transferable skills instead.",
        "skills": [
            "Communication", "Problem Solving", "Adaptability", "Time Management",
            "Critical Thinking", "Collaboration", "Learning Agility", "Digital Literacy",
        ],
    },
]

PERSONA_BY_ID = {p["id"]: p for p in CAREER_PERSONAS}


def get_persona(persona_id: str) -> dict:
    return PERSONA_BY_ID.get(persona_id, CAREER_PERSONAS[-1])
