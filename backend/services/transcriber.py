
import os
import whisper
import librosa

# Load model once at module level — avoids reloading on every request
_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")
_whisper_model = None


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        print(f"[ORION] Loading Whisper model: {_MODEL_SIZE}")
        _whisper_model = whisper.load_model(_MODEL_SIZE)
    return _whisper_model


def transcribe_audio(audio_path: str) -> tuple[str, float]:
    """
    Transcribes audio to text using Whisper.
    Returns (transcript, duration_in_seconds).
    """
    model = _get_model()

    # Get audio duration via librosa
    try:
        duration = librosa.get_duration(path=audio_path)
    except Exception:
        duration = 0.0

    # Transcribe
    result = model.transcribe(audio_path, language="en", fp16=False)
    transcript = result.get("text", "").strip()

    is_speaking = len(transcript.strip()) > 10

    return transcript, round(duration, 2), is_speaking
