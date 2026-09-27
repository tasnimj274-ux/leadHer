"""Mock Interview page.

Privacy note: recorded audio is transcribed in memory only and is never
written to disk. Only the resulting transcript text and a few numeric
speaking metrics are kept in st.session_state for this browser session.
"""
import streamlit as st

from utils.interview import (
    ANSWERS_KEY,
    FOLLOWUPS_KEY,
    INDEX_KEY,
    QUESTIONS_KEY,
    RESULTS_KEY,
    STAGE_KEY,
    build_questions,
    get_followup,
    practice_suggestions,
    score_interview,
)
from utils.quest import render as render_quest
from utils.navigation import go_to
from utils.voice import (
    FLUENCY_RESULT_KEY,
    VOICE_UNAVAILABLE_MESSAGE,
    VoiceError,
    analyze_fluency,
    ensure_model_loaded,
    transcribe_audio,
)
from views.career_goal import CAREER_GOAL_KEY

CSS = """
<style>
.block-container { max-width: 900px; padding-top: 2.5rem; }
.lh-brand { color: #C792FF; font-weight: 700; letter-spacing: 0.12em;
            font-size: 0.85rem; text-transform: uppercase; }
.lh-page-title { font-size: 1.9rem; font-weight: 800; color: #F7F3FF;
                 margin: 0.3rem 0 0.3rem 0; }
.lh-goal-line { color: #C792FF; font-weight: 600; margin-bottom: 0.2rem; }
.lh-progress { color: rgba(239,234,252,0.74); font-size: 0.9rem; margin-bottom: 0.6rem; }
.lh-stage { display: inline-block; background: rgba(199,146,255,0.14); color: #C792FF;
            font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;
            text-transform: uppercase; padding: 3px 10px; border-radius: 999px;
            margin-bottom: 0.6rem; }
.lh-interviewer-box { background: rgba(255,255,255,0.065); border-radius: 14px; padding: 18px 20px;
               border: 1px solid rgba(255,255,255,0.12); margin-bottom: 1rem; }
.lh-interviewer-label { font-size: 0.75rem; font-weight: 700; color: #C792FF;
                         text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.lh-interviewer-q { font-size: 1.1rem; color: #F7F3FF; font-style: italic; line-height: 1.5; }
.lh-case-box { background: rgba(255,255,255,0.065); border-radius: 14px; padding: 16px 20px;
               border: 1px solid rgba(255,255,255,0.12); margin-bottom: 1rem; font-size: 0.9rem;
               color: #F1EAFE; line-height: 1.5; backdrop-filter: blur(10px); }
.lh-case-box b { color: #FFFFFF; }
.lh-source { font-size: 0.78rem; color: #B9B0CA; margin-top: 8px; }
.lh-privacy { background: rgba(255,193,99,0.10); border-left: 4px solid #F0B429;
              padding: 10px 14px; border-radius: 8px; font-size: 0.85rem;
              color: #FFE8B5; margin: 1rem 0; }
.lh-score-box { background: rgba(255,255,255,0.065); border-radius: 14px; padding: 20px;
                text-align: center; margin: 1rem 0; border: 1px solid rgba(255,255,255,0.12); }
.lh-score-num { font-size: 2.6rem; font-weight: 800; color: #C792FF; }
.lh-score-label { color: rgba(239,234,252,0.74); font-size: 0.9rem; margin-top: 4px; }
.lh-row { display: flex; justify-content: space-between; font-size: 0.9rem;
          padding: 5px 2px; border-bottom: 1px solid rgba(199,146,255,0.14); }
.lh-fluency-box { background: rgba(57, 211, 145, 0.10); border-radius: 14px; padding: 20px; border: 1px solid rgba(57,211,145,0.18);
                   margin: 1rem 0; border: 1px solid rgba(57,211,145,0.18); }
.lh-fluency-num { font-size: 2.2rem; font-weight: 800; color: #66E3AE; }
.lh-metric-row { display: flex; justify-content: space-between; font-size: 0.88rem;
                  padding: 5px 2px; border-bottom: 1px solid rgba(57,211,145,0.18); }
.lh-recorded { color: #66E3AE; font-weight: 600; font-size: 0.85rem; }
</style>
"""

STAGE_ORDER = ["Introduction", "Experience", "Role Knowledge", "Real-World Problem", "Pressure / Situational"]


def _goal_line(goal: dict) -> str:
    text = goal.get("track_label", "")
    if goal.get("specific_goal"):
        text += f" — {goal['specific_goal']}"
    return text


def _init_state(track_id: str) -> None:
    if QUESTIONS_KEY not in st.session_state:
        st.session_state[QUESTIONS_KEY] = build_questions(track_id)
        st.session_state[ANSWERS_KEY] = {}
        st.session_state[FOLLOWUPS_KEY] = {}
        st.session_state[INDEX_KEY] = 0
        st.session_state[STAGE_KEY] = "answer"


def _case_box_html(question: dict) -> str:
    points = "".join(f"<li>{p}</li>" for p in question.get("case_data_points", []))
    source = question.get("case_source_name", "")
    source_url = question.get("case_source_url", "")
    source_date = question.get("case_source_date", "")
    source_line = ""
    if source:
        link = f'<a href="{source_url}" target="_blank">{source}</a>' if source_url else source
        source_line = f'<div class="lh-source">Source: {link}{" — " + source_date if source_date else ""}</div>'
    return (
        f'<div class="lh-case-box">'
        f'<b>{question.get("case_title", "")}</b><br>'
        f'{question.get("case_context", "")}<br><br>'
        f'<b>{question.get("case_data_label", "")}</b>'
        f'<ul>{points}</ul>'
        f'{source_line}'
        f"</div>"
    )


VOICE_READY_KEY = "_voice_model_ready"
VOICE_UNAVAILABLE_KEY = "_voice_model_unavailable"


def _answer_widgets(key_prefix: str):
    """Renders the Type/Record choice and returns (mode, text_value, audio_value)."""
    mode = st.radio(
        "How would you like to answer?",
        ["Type", "Record"],
        horizontal=True,
        key=f"{key_prefix}_mode",
    )
    text_value, audio_value = None, None
    if mode == "Type":
        text_value = st.text_area(
            "Your answer",
            key=f"{key_prefix}_text",
            height=140,
            placeholder="Type your answer here...",
        )
    else:
        # The speech model is only ever loaded here - the first time the
        # candidate actually picks "Record" - never at app startup. Once
        # loaded, it's cached (utils.voice._load_model uses
        # st.cache_resource), so this block is a no-op instant check on
        # every later question and rerun.
        if st.session_state.get(VOICE_UNAVAILABLE_KEY):
            st.warning(VOICE_UNAVAILABLE_MESSAGE)
            if st.button("Retry voice setup", key=f"{key_prefix}_retry_voice"):
                st.session_state.pop(VOICE_UNAVAILABLE_KEY, None)
                st.rerun()
            return mode, text_value, audio_value

        if not st.session_state.get(VOICE_READY_KEY):
            with st.spinner("Preparing voice transcription for your first answer..."):
                try:
                    ensure_model_loaded()
                except VoiceError:
                    st.session_state[VOICE_UNAVAILABLE_KEY] = True
                    st.rerun()
                    return mode, text_value, audio_value
                st.session_state[VOICE_READY_KEY] = True

        try:
            audio_value = st.audio_input("Record your answer", key=f"{key_prefix}_audio", sample_rate=16000)
        except TypeError:
            audio_value = st.audio_input("Record your answer", key=f"{key_prefix}_audio")
        if audio_value is not None:
            st.markdown('<div class="lh-recorded">🎙️ Recording captured</div>', unsafe_allow_html=True)
            st.audio(audio_value)
        st.caption(
            "Audio is processed to create a text transcript for this simulation and is "
            "not permanently stored. Keep answers to about 60-90 seconds."
        )
    return mode, text_value, audio_value


def _resolve_answer(mode: str, text_value, audio_value):
    """Returns (answer_dict, error_message). answer_dict is None on error."""
    if mode == "Type":
        text = (text_value or "").strip()
        if not text:
            return None, "Please type an answer before continuing."
        return {"text": text, "mode": "text", "word_count": len(text.split())}, None

    if audio_value is None:
        return None, "Please record an answer before continuing, or switch to Type."

    stage_labels = {
        "preparing": "Preparing audio...",
        "transcribing": "Transcribing your answer... (first time may take a bit longer)",
        "analysing": "Analysing response...",
    }
    with st.status(stage_labels["preparing"], expanded=False) as status:
        def _update_stage(stage: str) -> None:
            label = stage_labels.get(stage)
            if label:
                status.update(label=label)

        try:
            transcript = transcribe_audio(audio_value.getvalue(), stage_callback=_update_stage)
        except VoiceError as exc:
            status.update(label="Transcription failed", state="error")
            return None, str(exc)
        status.update(label="Complete", state="complete")
    return {
        "text": transcript.text,
        "mode": "voice",
        "word_count": transcript.word_count,
        "words": transcript.words,
        "duration_seconds": transcript.duration_seconds,
    }, None


def _render_question_step(goal: dict, questions: list, index: int) -> None:
    question = questions[index]
    stage_num = STAGE_ORDER.index(question["stage"]) + 1
    is_followup = st.session_state[STAGE_KEY] == "followup"

    st.markdown(f'<div class="lh-goal-line">Target role: {_goal_line(goal)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="lh-stage">Stage {stage_num:02d} / 05 &middot; {question["stage"]}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="lh-progress">Question {index + 1} of {len(questions)}</div>',
                unsafe_allow_html=True)

    if question.get("is_case"):
        st.markdown(_case_box_html(question), unsafe_allow_html=True)

    if not is_followup:
        st.markdown(
            f'<div class="lh-interviewer-box">'
            f'<div class="lh-interviewer-label">Interviewer</div>'
            f'<div class="lh-interviewer-q">"{question["question"]}"</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
        key_prefix = f"interview_{question['id']}"
    else:
        followup_text = st.session_state[FOLLOWUPS_KEY][question["id"]]["question"]
        st.markdown(
            f'<div class="lh-interviewer-box">'
            f'<div class="lh-interviewer-label">Interviewer (follow-up)</div>'
            f'<div class="lh-interviewer-q">"{followup_text}"</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
        key_prefix = f"interview_{question['id']}_followup"

    mode, text_value, audio_value = _answer_widgets(key_prefix)

    is_last = index == len(questions) - 1
    button_label = "Finish Interview" if (is_last and (is_followup or not question.get("allow_followup"))) else "Submit Answer"

    if st.button(button_label, type="primary"):
        answer, error = _resolve_answer(mode, text_value, audio_value)
        if error:
            st.error(error)
            return

        if not is_followup:
            answers = st.session_state[ANSWERS_KEY]
            answers[question["id"]] = answer
            st.session_state[ANSWERS_KEY] = answers

            followup_text = get_followup(question, answer["text"])
            if followup_text:
                st.session_state[FOLLOWUPS_KEY][question["id"]] = {"question": followup_text, "answer": ""}
                st.session_state[STAGE_KEY] = "followup"
                st.rerun()
                return
            else:
                st.session_state[FOLLOWUPS_KEY][question["id"]] = None
        else:
            st.session_state[FOLLOWUPS_KEY][question["id"]] = {
                "question": st.session_state[FOLLOWUPS_KEY][question["id"]]["question"],
                "answer": answer["text"],
                "mode": answer["mode"],
                "word_count": answer.get("word_count"),
                "words": answer.get("words"),
                "duration_seconds": answer.get("duration_seconds"),
            }

        st.session_state[STAGE_KEY] = "answer"
        if is_last:
            st.session_state[INDEX_KEY] = len(questions)
        else:
            st.session_state[INDEX_KEY] = index + 1
        st.rerun()

    st.caption("Do your best - this is a private practice simulation, not a real interview.")


def _collect_voice_answers(answers: dict, followups: dict) -> list:
    voice_answers = []
    for entry in list(answers.values()) + [f for f in followups.values() if f]:
        if entry and entry.get("mode") == "voice" and entry.get("text"):
            voice_answers.append({
                "text": entry["text"],
                "word_count": entry.get("word_count") or len(entry["text"].split()),
                "words": entry.get("words") or [],
                "duration_seconds": entry.get("duration_seconds") or 0.0,
            })
    return voice_answers


def _render_results(goal: dict, results: dict, fluency: dict) -> None:
    st.markdown(f'<div class="lh-goal-line">Target role: {_goal_line(goal)}</div>', unsafe_allow_html=True)
    st.markdown("### 🎤 Interview Room Complete")

    st.markdown(
        f'<div class="lh-score-box">'
        f'<div class="lh-score-num">{results["overall"]} / 100</div>'
        f'<div class="lh-score-label">Interview Performance &mdash; your performance in this '
        f"interview simulation only, not a hiring probability.</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Breakdown**")
    from utils.interview import DIMENSION_LABELS
    rows = "".join(
        f'<div class="lh-row"><span>{DIMENSION_LABELS[d]}</span>'
        f'<span>{results["dimension_totals"][d]} / {results["dimension_max"][d]}</span></div>'
        for d in DIMENSION_LABELS
    )
    st.markdown(rows, unsafe_allow_html=True)

    st.markdown("### Your Strengths")
    for s in results["strengths"]:
        st.markdown(f"- Solid performance in **{s}**.")

    st.markdown("### Your Development Areas")
    if results["development_areas"]:
        for d in results["development_areas"]:
            st.markdown(f"- Consider practicing **{d}** further.")
    else:
        st.write("Every dimension met the strength threshold in this simulation.")

    if not fluency.get("insufficient"):
        st.markdown(
            f'<div class="lh-fluency-box">'
            f'<div class="lh-interviewer-label">English Speaking Fluency &mdash; Simulation</div>'
            f'<div class="lh-fluency-num">{fluency["overall"]} / 100</div>',
            unsafe_allow_html=True,
        )
        for m in fluency["metrics"]:
            st.markdown(
                f'<div class="lh-metric-row"><span>{m["name"]}</span>'
                f'<span>{m["label"]} ({m["detail"]})</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption(
            "This is a practice-oriented English speaking simulation, not a standardized "
            "language test (not IELTS/CEFR), and it does not score accent or pronunciation."
        )
        if fluency.get("tips"):
            st.markdown(f"**Feedback:** {fluency['tips'][0]}")
    elif any(a.get("mode") == "voice" for a in st.session_state.get(ANSWERS_KEY, {}).values()):
        st.info(fluency.get("message", "Not enough voice data for a reliable simulation score."))

    st.markdown("### What to Practise Next")
    for tip in practice_suggestions(results):
        st.markdown(f"- {tip}")

    st.caption(
        "This reflects your performance in this interview simulation only - it does not "
        "predict your chance of getting hired."
    )

    st.button(
        "Continue to Career Readiness Map →",
        type="primary",
        on_click=go_to,
        args=("report",),
    )
    st.button("← Back to start", on_click=go_to, args=("landing",))


def render() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="lh-brand">LeadHer Career Quest</div>', unsafe_allow_html=True)
    render_quest("interview")
    st.markdown('<div class="lh-page-title">🎤 Interview Room</div>', unsafe_allow_html=True)

    goal = st.session_state.get(CAREER_GOAL_KEY)
    if not goal:
        st.write("Please choose a career goal before starting the Mock Interview.")
        st.button("Choose my career goal", type="primary", on_click=go_to, args=("career_goal",))
        st.button("← Back to start", on_click=go_to, args=("landing",))
        return

    _init_state(goal["track_id"])

    if RESULTS_KEY in st.session_state:
        _render_results(goal, st.session_state[RESULTS_KEY], st.session_state.get(FLUENCY_RESULT_KEY, {}))
        return

    questions = st.session_state[QUESTIONS_KEY]
    index = st.session_state.get(INDEX_KEY, 0)

    if index >= len(questions):
        results = score_interview(questions, st.session_state[ANSWERS_KEY], st.session_state[FOLLOWUPS_KEY])
        voice_answers = _collect_voice_answers(st.session_state[ANSWERS_KEY], st.session_state[FOLLOWUPS_KEY])
        fluency = analyze_fluency(voice_answers)
        st.session_state[RESULTS_KEY] = results
        st.session_state[FLUENCY_RESULT_KEY] = fluency
        st.rerun()
        return

    st.markdown(
        '<div class="lh-privacy">Your answers stay in this browser session only. If you '
        "record audio, it is transcribed to text for scoring and is not permanently "
        "stored by this app.</div>",
        unsafe_allow_html=True,
    )
    _render_question_step(goal, questions, index)
