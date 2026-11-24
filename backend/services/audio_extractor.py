
import subprocess
import os


def extract_audio_from_video(video_path: str) -> str:
    """
    Extracts 16kHz mono WAV audio from a video file.
    Whisper and librosa both work best with 16kHz mono WAV.
    Returns path to the .wav file.
    """
    base = os.path.splitext(video_path)[0]
    audio_path = base + "_audio.wav"

    if os.path.exists(audio_path):
        return audio_path

    cmd = [
        "ffmpeg",
        "-y",                   # overwrite if exists
        "-i", video_path,       # input video
        "-ac", "1",             # mono
        "-ar", "16000",         # 16kHz sample rate
        "-vn",                  # no video
        "-f", "wav",
        audio_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    return audio_path
