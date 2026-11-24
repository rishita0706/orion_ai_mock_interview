from sentence_transformers import SentenceTransformer
from .model_loader import model
from services.transcriber import transcribe_audio

# load once
sbert = SentenceTransformer("all-MiniLM-L6-v2")

LABEL_MAP = {
    0: "weak",
    1: "average",
    2: "strong"
}

def predict_audio(audio_path: str):
    # Step 1: transcribe
    transcript, _ = transcribe_audio(audio_path)

    if not transcript or len(transcript.strip()) < 5:
        return {
            "label": "weak",
            "confidence": 0.0,
            "transcript": transcript
        }

    # Step 2: embedding
    embedding = sbert.encode(transcript).reshape(1, -1)

    # Step 3: prediction
    pred = model.predict(embedding)[0]
    probs = model.predict_proba(embedding)[0]

    return {
        "label": LABEL_MAP[pred],
        "confidence": float(max(probs)),
        "transcript": transcript
    }