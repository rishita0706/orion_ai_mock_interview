
import re
import numpy as np
import librosa
import parselmouth
from parselmouth.praat import call


FILLER_WORDS = {
    "um", "uh", "like", "you know", "basically", "literally",
    "right", "so", "actually", "kind of", "sort of", "i mean",
}


def analyse_speech(audio_path: str, transcript: str) -> dict:
    """
    Returns a dict of speech metrics and an overall fluency_score (0–100).
    """
    metrics = {}

    # ── Load audio ────────────────────────────────────────────────────────────
    y, sr = librosa.load(audio_path, sr=16000)
    duration = librosa.get_duration(y=y, sr=sr)
    metrics["duration_seconds"] = round(duration, 2)

    # ── Words per minute ──────────────────────────────────────────────────────
    words = transcript.split() if transcript else []
    wpm = round((len(words) / duration) * 60, 1) if duration > 0 else 0.0
    metrics["word_count"] = len(words)
    metrics["wpm"] = wpm

    # ── Filler words ──────────────────────────────────────────────────────────
    lower_transcript = transcript.lower() if transcript else ""
    filler_count = sum(
        len(re.findall(r"\b" + re.escape(fw) + r"\b", lower_transcript))
        for fw in FILLER_WORDS
    )
    metrics["filler_count"] = filler_count
    metrics["filler_rate"] = round(filler_count / max(len(words), 1) * 100, 1)

    # ── Pause detection ───────────────────────────────────────────────────────
    # Detect silent segments (< -40dB RMS)
    hop_length = 512
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    threshold = np.percentile(rms, 10)  # bottom 10% = silence
    silent_frames = rms < threshold
    
    # Count transitions into silence (proxy for pause count)
    transitions = np.diff(silent_frames.astype(int))
    pause_count = int(np.sum(transitions == 1))
    metrics["pause_count"] = pause_count
    metrics["silence_ratio"] = round(float(np.mean(silent_frames)), 3)

    # ── Pitch analysis via Praat ──────────────────────────────────────────────
    try:
        snd = parselmouth.Sound(audio_path)
        pitch = call(snd, "To Pitch", 0.0, 75, 500)
        pitch_values = pitch.selected_array["frequency"]
        voiced = pitch_values[pitch_values > 0]
        if len(voiced) > 10:
            metrics["pitch_mean_hz"]     = round(float(np.mean(voiced)), 1)
            metrics["pitch_std_hz"]      = round(float(np.std(voiced)), 1)
            metrics["pitch_range_hz"]    = round(float(np.ptp(voiced)), 1)
        else:
            metrics["pitch_mean_hz"]     = 0.0
            metrics["pitch_std_hz"]      = 0.0
            metrics["pitch_range_hz"]    = 0.0
    except Exception as e:
        print(f"[ORION] Pitch analysis failed: {e}")
        metrics["pitch_mean_hz"] = 0.0
        metrics["pitch_std_hz"] = 0.0
        metrics["pitch_range_hz"] = 0.0

    # ── Fluency score (heuristic formula) ────────────────────────────────────
    # Ideal WPM: 110–150. Penalise if too fast (>180) or too slow (<80).
    wpm_score = _score_wpm(wpm)

    # Filler penalty: > 10% filler rate → heavy penalty
    filler_penalty = min(filler_count * 3, 30)

    # Pause reward: some pauses are good (show thinking); too many = disfluent
    pause_score = 100 if 2 <= pause_count <= 8 else max(0, 100 - abs(pause_count - 5) * 5)

    # Pitch variety reward: monotone (low std) → subtract up to 10 pts
    pitch_variety = min(metrics["pitch_std_hz"] / 3, 10)

    fluency_score = round(
        0.40 * wpm_score +
        0.30 * (100 - filler_penalty) +
        0.20 * pause_score +
        0.10 * pitch_variety * 10,
        1,
    )
    fluency_score = max(0.0, min(100.0, fluency_score))
    metrics["fluency_score"] = fluency_score

    return metrics


def _score_wpm(wpm: float) -> float:
    """Score WPM on a 0–100 scale. Ideal = 110–150 wpm."""
    if wpm == 0:
        return 0.0
    if 110 <= wpm <= 150:
        return 100.0
    if wpm < 110:
        return max(0.0, 100 - (110 - wpm) * 1.5)
    # wpm > 150
    return max(0.0, 100 - (wpm - 150) * 2.0)
