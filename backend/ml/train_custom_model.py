
import os
import sys
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from sentence_transformers import SentenceTransformer

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))
from services.transcriber import transcribe_audio


DATASET_DIR = Path(__file__).parent / "dataset"
MODEL_OUTPUT = Path(__file__).parent / "orion_model.joblib"

LABELS = {"weak": 0, "average": 1, "strong": 2}


def load_dataset():
    """
    Loads audio files from dataset/weak, dataset/average, dataset/strong.
    Transcribes each, then encodes with sentence-transformers.
    Returns X (embeddings), y (labels).
    """
    print("[ORION] Loading sentence-transformer model...")
    sbert = SentenceTransformer("all-MiniLM-L6-v2")

    X, y = [], []
    for label_name, label_id in LABELS.items():
        folder = DATASET_DIR / label_name
        if not folder.exists():
            print(f"[WARN] Folder not found: {folder} — skipping")
            continue

        audio_files = list(folder.glob("*.wav"))
        print(f"[ORION] Processing {len(audio_files)} '{label_name}' files...")

        for audio_path in audio_files:
            try:
                transcript, _ = transcribe_audio(str(audio_path))
                if not transcript or len(transcript.strip().split()) < 3:
                    print(f"  [SKIP] Empty transcript: {audio_path.name}")
                    continue

                embedding = sbert.encode(transcript)
                X.append(embedding)
                y.append(label_id)
                print(f"  [OK] {audio_path.name[:40]}")
            except Exception as e:
                print(f"  [ERR] {audio_path.name}: {e}")

    return np.array(X), np.array(y)


def train():
    print("=" * 60)
    print("ORION Custom Model Training")
    print("=" * 60)

    X, y = load_dataset()
    print("\n[DEBUG] Sample transcripts:")
    for i in range(min(3, len(X))):
        print(f"  Sample {i+1}: {y[i]}")

    if len(X) == 0:
        print("\n[ERROR] No samples loaded. Check your dataset folder structure:")
        print("  ml/dataset/weak/*.wav")
        print("  ml/dataset/average/*.wav")
        print("  ml/dataset/strong/*.wav")
        sys.exit(1)

    print(f"\n[ORION] Total samples: {len(X)}")
    for name, idx in LABELS.items():
        count = np.sum(y == idx)
        print(f"  {name}: {count} samples")

    if len(X) < 20:
        print("\n[WARN] You have fewer than 20 samples. Cross-validation may be unreliable.")
        print("       Consider collecting more data for better model performance.")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(X) >= 10 else None
    )

    print(f"\n[ORION] Training GradientBoostingClassifier on {len(X_train)} samples...")
    model = GradientBoostingClassifier(
        n_estimators=250,
        learning_rate=0.05,
        max_depth=4,
        random_state=42,
    )
    model.fit(X_train, y_train)

    # Evaluate
    print("\n[ORION] Evaluation on test set:")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["weak", "average", "strong"]))

    # Cross-validation
    if len(X) >= 15:
        cv_scores = cross_val_score(model, X, y, cv=min(5, len(X) // 3), scoring="accuracy")
        print(f"[ORION] Cross-validation accuracy: {cv_scores.mean():.2f} ± {cv_scores.std():.2f}")

    # Save model
    joblib.dump(model, MODEL_OUTPUT)
    print(f"\n[ORION] Model saved to: {MODEL_OUTPUT}")
    print(f"[ORION] Set CUSTOM_MODEL_PATH={MODEL_OUTPUT} in your .env file")


if __name__ == "__main__":
    train()
