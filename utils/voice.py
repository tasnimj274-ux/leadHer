"""Local voice transcription and a transparent, rule-based English speaking
fluency *simulation* for the Mock Interview.

Privacy: audio is transcribed in memory only. Nothing is written to disk,
and the raw audio bytes are discarded by the caller right after this
module returns a transcript. Only the transcript text and a few numeric
metrics (word count, pause count, etc.) are meant to be kept in
st.session_state.

Transcription runs 100% locally with faster-whisper - no audio or text
is ever sent to a third-party API. Nothing here claims to be a certified
language test (IELTS/CEFR) or a pronunciation/accent score.
"""
import io
import os
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from typing import Optional

import streamlit as st

DEFAULT_MODEL_SIZE = "tiny.en"          # smallest English model - fastest on a CPU-only laptop
ALLOWED_MODEL_SIZES = ("tiny.en", "base.en")

MAX_AUDIO_BYTES = 15 * 1024 * 1024   # ~15 MB safety cap for a short answer
MIN_TRANSCRIPT_WORDS = 3             # fewer words than this = "too short to use"

# How long we're willing to wait for a transcription before giving up and
# letting the candidate switch to typing instead of staring at a spinner
# forever. Generous enough to cover the model's one-time download on a
# slower connection; short enough that the app never feels frozen.
TRANSCRIBE_TIMEOUT_SECONDS = 75

FLUENCY_RESULT_KEY = "interview_fluency"

# Shown for any real transcription-engine failure (not a fixable input
# problem like an empty recording) so the app never crashes and the
# candidate always has a way forward.
VOICE_UNAVAILABLE_MESSAGE = (
    "Voice transcription is temporarily unavailable. You can switch to "
    "Type and continue your mock interview."
)

# A single reusable background worker. Creating one ThreadPoolExecutor at
# import time (instead of one per call) avoids extra thread-creation
# overhead on every answer, and - because Python only imports a module
# once per process - this same executor survives every Streamlit rerun.
_EXECUTOR = ThreadPoolExecutor(max_workers=1)

# How many CPU threads faster-whisper itself is allowed to use per call.
# A small, fixed number keeps things fast without starving the rest of a
# modest student laptop.
_CPU_THREADS = max(2, min(4, os.cpu_count() or 4))


class VoiceError(Exception):
    """A problem with the recording or transcription. str() is a friendly message."""


def _noop_stage(stage: str) -> None:
    pass


# =============================================================================
# 1. Local transcription (faster-whisper, CPU + INT8, lazy-loaded & cached)
# =============================================================================

@st.cache_resource(show_spinner=False)
def _load_model(model_size: str = DEFAULT_MODEL_SIZE):
    """Load the faster-whisper model once per model size and reuse it for
    every question, instead of reloading it on every transcription call.

    st.cache_resource stores this in a process-wide cache keyed by the
    function's arguments, so as long as `model_size` doesn't change, this
    body only ever runs once per running app - not on every rerun and not
    on every answer. This is also the ONE place a model download can ever
    happen, and it happens at most once per model size.
    """
    from faster_whisper import WhisperModel  # imported lazily: optional dependency
    return WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=_CPU_THREADS)


@dataclass
class Transcript:
    text: str
    word_count: int
    words: list = field(default_factory=list)   # [(word, start_seconds, end_seconds), ...]
    duration_seconds: float = 0.0


def ensure_model_loaded(
    model_size: str = DEFAULT_MODEL_SIZE,
    timeout_seconds: float = TRANSCRIBE_TIMEOUT_SECONDS,
) -> None:
    """Warm up (download the first time, then load) the speech model
    WITHOUT transcribing anything yet.

    Call this once, right when the candidate chooses "Record" - not at
    app startup - so the one-time download/load happens up front with a
    clear "preparing" message, and the later per-answer transcription is
    fast because the model is already cached. Raises VoiceError (with the
    exact fallback message) on failure or timeout; never raises anything
    else, so it can't crash the app.
    """
    if model_size not in ALLOWED_MODEL_SIZES:
        model_size = DEFAULT_MODEL_SIZE
    future = _EXECUTOR.submit(_load_model, model_size)
    try:
        future.result(timeout=timeout_seconds)
    except Exception as exc:
        # Covers FutureTimeoutError, ImportError (faster-whisper missing),
        # and any error the model backend can raise while loading/downloading.
        raise VoiceError(VOICE_UNAVAILABLE_MESSAGE) from exc


def _load_and_transcribe(audio_bytes: bytes, model_size: str):
    """The actual blocking work: load the (cached) model and run it. This
    runs on a background thread so the caller can enforce a timeout - it
    must not touch any Streamlit UI calls itself."""
    model = _load_model(model_size)
    segments, _info = model.transcribe(
        io.BytesIO(audio_bytes),
        language="en",
        word_timestamps=True,
        beam_size=1,                     # greedy decoding - much faster on CPU than the default beam of 5
        best_of=1,
        temperature=0.0,
        condition_on_previous_text=False,  # avoids extra passes / drift on short answers
    )
    words = []
    text_parts = []
    for segment in segments:
        text_parts.append(segment.text.strip())
        for w in (segment.words or []):
            token = (w.word or "").strip()
            if token:
                words.append((token, float(w.start), float(w.end)))
    return words, text_parts


def transcribe_audio(
    audio_bytes: bytes,
    model_size: str = DEFAULT_MODEL_SIZE,
    stage_callback=None,
    timeout_seconds: float = TRANSCRIBE_TIMEOUT_SECONDS,
) -> Transcript:
    """Transcribe a short WAV/audio recording entirely on this machine.

    Raises VoiceError with a friendly message for every failure case:
    no/empty recording, unreadable audio, background noise with nothing
    recognizable, a transcription engine problem, or a transcription that
    took too long (so the candidate is never stuck on a spinner forever
    and can switch to typing instead).

    `stage_callback`, if given, is called on the MAIN thread only (never
    from the background worker) with one of: "preparing", "transcribing",
    "analysing" - so a caller can show live progress in the UI.
    """
    notify = stage_callback or _noop_stage

    notify("preparing")
    if not audio_bytes:
        raise VoiceError("No recording was captured. Please try recording again.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise VoiceError(
            "That recording is too long. Please keep your answer to about "
            "60-90 seconds and record again."
        )
    if model_size not in ALLOWED_MODEL_SIZES:
        model_size = DEFAULT_MODEL_SIZE

    notify("transcribing")
    future = _EXECUTOR.submit(_load_and_transcribe, audio_bytes, model_size)
    try:
        words, text_parts = future.result(timeout=timeout_seconds)
    except FutureTimeoutError:
        # Don't block forever waiting for the (possibly still-downloading
        # or still-running) worker - let the candidate move on. The
        # abandoned future finishes quietly in the background and its
        # result is discarded when it does.
        raise VoiceError(VOICE_UNAVAILABLE_MESSAGE)
    except ImportError as exc:
        raise VoiceError(VOICE_UNAVAILABLE_MESSAGE) from exc
    except Exception as exc:
        raise VoiceError(VOICE_UNAVAILABLE_MESSAGE) from exc

    notify("analysing")
    text = " ".join(part for part in text_parts if part).strip()
    text = re.sub(r"\s{2,}", " ", text)

    if len(words) < MIN_TRANSCRIPT_WORDS:
        raise VoiceError(
            "We couldn't hear enough clear speech in that recording (it may "
            "have been mostly silence or background noise). Please try "
            "again, or type your answer instead."
        )

    duration = (words[-1][2] - words[0][1]) if words else 0.0
    return Transcript(text=text, word_count=len(words), words=words, duration_seconds=max(duration, 0.0))


# =============================================================================
# 2. English speaking fluency - simulation (separate from interview content score)
# =============================================================================

FILLERS = [
    "um", "umm", "uh", "uhh", "erm", "hmm", "like", "you know", "i mean",
    "kind of", "sort of", "basically", "actually", "literally", "so yeah",
]
CONNECTORS = [
    "because", "so", "then", "however", "but", "although", "first",
    "second", "finally", "for example", "as a result", "in addition",
    "on the other hand", "therefore", "meanwhile", "after that",
]

MIN_WORDS_FOR_FLUENCY = 40     # across all voice answers combined
MIN_ANSWERS_FOR_FLUENCY = 2    # at least this many voice answers


def _band(score: int, labels=("Developing", "Moderate", "Good", "Strong")) -> str:
    """Turn a 0-100 sub-score into a plain-language band."""
    if score >= 80:
        return labels[3]
    if score >= 60:
        return labels[2]
    if score >= 35:
        return labels[1]
    return labels[0]


def _count_phrases(text_lower: str, phrases: list) -> int:
    total = 0
    for phrase in phrases:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        total += len(re.findall(pattern, text_lower))
    return total


def analyze_fluency(voice_answers: list) -> dict:
    """voice_answers: list of {"text": str, "words": [(word, start, end), ...],
    "duration_seconds": float}. Returns a dict describing the simulation
    result, or {"insufficient": True, "message": ...} if there isn't enough
    voice data for a meaningful read.
    """
    usable = [a for a in voice_answers if a.get("text")]
    total_words = sum(a.get("word_count") or len(a["text"].split()) for a in usable)

    if len(usable) < MIN_ANSWERS_FOR_FLUENCY or total_words < MIN_WORDS_FOR_FLUENCY:
        return {
            "insufficient": True,
            "message": "Not enough voice data for a reliable simulation score.",
        }

    all_text = " ".join(a["text"] for a in usable)
    all_text_lower = all_text.lower()
    all_words_lower = re.findall(r"[a-z']+", all_text_lower)

    # --- Pace: words per minute, from word timestamps -----------------------
    total_duration = sum(a.get("duration_seconds") or 0 for a in usable)
    pace_wpm = (total_words / (total_duration / 60)) if total_duration > 0 else None
    if pace_wpm is None:
        pace_score, pace_label = 60, "Not available"
    elif 100 <= pace_wpm <= 160:
        pace_score, pace_label = 90, "Good"
    elif 80 <= pace_wpm < 100 or 160 < pace_wpm <= 190:
        pace_score, pace_label = 65, "Moderate"
    else:
        pace_score, pace_label = 35, "Developing"

    # --- Pauses: gaps of 0.6s+ between consecutive words --------------------
    pause_count = 0
    for a in usable:
        words = a.get("words") or []
        for prev, cur in zip(words, words[1:]):
            if cur[1] - prev[2] >= 0.6:
                pause_count += 1
    pauses_per_100_words = (pause_count / total_words) * 100 if total_words else 0
    if pauses_per_100_words <= 4:
        pause_score, pause_label = 85, "Low"
    elif pauses_per_100_words <= 9:
        pause_score, pause_label = 65, "Moderate"
    else:
        pause_score, pause_label = 40, "Frequent"

    # --- Filler words ---------------------------------------------------
    filler_count = _count_phrases(all_text_lower, FILLERS)
    fillers_per_100_words = (filler_count / total_words) * 100 if total_words else 0
    if fillers_per_100_words <= 2:
        filler_score, filler_label = 90, "Low"
    elif fillers_per_100_words <= 6:
        filler_score, filler_label = 65, "Moderate"
    else:
        filler_score, filler_label = 35, "High"

    # --- Response completeness (average length vs. a healthy minimum) ------
    avg_words = total_words / len(usable)
    completeness_score = max(0, min(100, round((avg_words / 45) * 100)))
    completeness_label = _band(completeness_score, ("Brief", "Developing", "Solid", "Strong"))

    # --- Vocabulary & phrase variety ----------------------------------------
    unique_ratio = (len(set(all_words_lower)) / len(all_words_lower)) if all_words_lower else 0
    connector_count = _count_phrases(all_text_lower, CONNECTORS)
    variety_score = max(0, min(100, round(unique_ratio * 130) + min(20, connector_count * 4)))
    variety_label = _band(variety_score)

    overall = round(
        0.20 * pace_score + 0.20 * pause_score + 0.20 * filler_score
        + 0.20 * completeness_score + 0.20 * variety_score
    )

    tips = []
    if filler_score < 65:
        tips.append("Try to notice and reduce filler words like 'um' or 'like' - short pauses work better than filler sounds.")
    if pause_score < 65:
        tips.append("Practice speaking in slightly longer, connected phrases to reduce frequent short pauses.")
    if variety_score < 65:
        tips.append("Use more varied linking phrases (for example, 'as a result', 'on the other hand') and vocabulary.")
    if completeness_score < 65:
        tips.append("Aim for fuller answers - briefly explain the situation, what you did, and the result.")
    if pace_label == "Developing":
        tips.append("Work on a steady, natural speaking pace - not rushed, not too slow.")
    if not tips:
        tips.append("Keep practicing with varied questions to build consistency under interview conditions.")

    return {
        "insufficient": False,
        "overall": overall,
        "metrics": [
            {"name": "Speaking pace", "label": pace_label, "detail": f"{round(pace_wpm)} words/min" if pace_wpm else "Not available"},
            {"name": "Pauses", "label": pause_label, "detail": f"{round(pauses_per_100_words, 1)} per 100 words"},
            {"name": "Filler words", "label": filler_label, "detail": f"{round(fillers_per_100_words, 1)} per 100 words"},
            {"name": "Response completeness", "label": completeness_label, "detail": f"~{round(avg_words)} words/answer"},
            {"name": "Vocabulary variety", "label": variety_label, "detail": f"{round(unique_ratio * 100)}% unique words"},
        ],
        "tips": tips[:5],
        "voice_answer_count": len(usable),
        "total_words": total_words,
    }
