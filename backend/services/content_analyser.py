
import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Load sentence-transformers model once
_SBERT_MODEL = None
_CUSTOM_MODEL = None
CUSTOM_MODEL_PATH = os.getenv("CUSTOM_MODEL_PATH", "")

STRUCTURE_MARKERS = {
    "intro":       ["i", "my", "when i", "in my experience", "i'd like to", "to answer", "i believe","so","yeah","basically"],
    "example":     ["for example", "for instance", "specifically", "one time", "in one case", "i remember","like","that's why","hence"],
    "result":      ["as a result", "which led to", "because of this", "the outcome", "we achieved","so","because","therefore",],
    "conclusion":  ["in conclusion", "to summarise", "overall", "in summary", "ultimately", "to wrap up","so yeah","overall","in the end","basically"],
}


def _get_sbert():
    global _SBERT_MODEL
    if _SBERT_MODEL is None:
        print("[ORION] Loading sentence-transformers model...")
        _SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _SBERT_MODEL


def _load_custom_model():
    global _CUSTOM_MODEL
    if _CUSTOM_MODEL is None and CUSTOM_MODEL_PATH and os.path.exists(CUSTOM_MODEL_PATH):
        import joblib
        try:
            _CUSTOM_MODEL = joblib.load(CUSTOM_MODEL_PATH)
            print(f"[ORION] Custom model loaded from {CUSTOM_MODEL_PATH}")
        except Exception as e:
            print(f"[ORION] Failed to load custom model: {e}")
    return _CUSTOM_MODEL


def analyse_content(transcript: str, question_text: str) -> dict:
    """
    Returns content metrics and an overall content_score (0–100).
    """
    metrics = {}

    if not transcript or len(transcript.strip()) < 10:
        metrics["content_score"] = 0.0
        return metrics

    # ── Relevance score (semantic similarity to question) ─────────────────────
    sbert = _get_sbert()
    q_emb = sbert.encode(question_text, convert_to_tensor=True)
    a_emb = sbert.encode(transcript, convert_to_tensor=True)
    relevance = float(util.cos_sim(q_emb, a_emb).item())
    relevance_score = round(max(0.0, min(1.0, (relevance + 0.5) / 1.2)) * 100, 1)
    metrics["relevance_score"] = relevance_score

    # ── Structure detection ────────────────────────────────────────────────────
    lower = transcript.lower()
    structure_hits = {}
    for category, markers in STRUCTURE_MARKERS.items():
        structure_hits[category] = any(m in lower for m in markers)

    structure_count = sum(structure_hits.values())
    structure_score = round(min(structure_count / 4, 1.0) * 100, 1)
    metrics["structure_score"] = structure_score
    metrics["has_example"] = structure_hits.get("example", False)
    metrics["has_conclusion"] = structure_hits.get("conclusion", False)

    # ── Vocabulary richness (type-token ratio) ────────────────────────────────
    words = re.findall(r"\b[a-z]+\b", lower)
    ttr = len(set(words)) / len(words) if words else 0.0
    vocab_score = round(min(ttr * 150, 100), 1)
    metrics["vocab_richness"] = round(ttr, 3)
    metrics["vocab_score"] = vocab_score

    # ── Length adequacy ────────────────────────────────────────────────────────
    # Ideal answer: 80–200 words
    word_count = len(words)
    if 80 <= word_count <= 200:
        length_score = 100.0
    elif word_count < 80:
        length_score = max(0.0, word_count / 80 * 100)
    else:
        length_score = max(50.0, 100 - (word_count - 200) * 0.3)
    metrics["length_score"] = round(length_score, 1)

    # ── Custom model boost (if available) ────────────────────────────────────
    custom_boost = 0.0
    custom_model = _load_custom_model()
    if custom_model is not None:
        try:
            embedding = sbert.encode([transcript])
            prediction = custom_model.predict_proba(embedding)[0]
            # Assumes labels: [weak=0, average=1, strong=2]
            custom_boost = round(float(prediction[2]) * 100, 1)  # "strong" probability → 0–100
            metrics["custom_model_score"] = custom_boost
            use_custom = True
        except Exception as e:
            print(f"[ORION] Custom model inference failed: {e}")
            use_custom = False
    else:
        use_custom = False

    # ── Aggregate content score ────────────────────────────────────────────────
    if use_custom:
        content_score = round(
            0.25 * relevance_score +
            0.20 * structure_score +
            0.15 * vocab_score     +
            0.15 * length_score    +
            0.25 * custom_boost,
            1,
        )
    else:
        content_score = round(
            0.35 * relevance_score +
            0.25 * structure_score +
            0.20 * vocab_score     +
            0.20 * length_score,
            1,
        )

    metrics["content_score"] = max(0.0, min(100.0, content_score))
    return metrics