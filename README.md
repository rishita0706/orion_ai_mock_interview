# ORION — Oral Reasoning & Interview Optimization Network

Full-stack AI-powered mock interview analysis system.

---

## Project Structure

```
orion/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # App entry point
│   ├── database.py             # PostgreSQL config (SQLAlchemy)
│   ├── models.py               # ORM models (User, Session, Answer, Analysis)
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variable template
│   ├── routers/
│   │   ├── auth.py             # Register, login, JWT
│   │   ├── sessions.py         # Create session, upload answers, complete
│   │   ├── analysis.py         # Fetch analysis results + score history
│   │   └── questions.py        # Question bank + random selection
│   ├── services/
│   │   ├── pipeline.py         # Master orchestrator — runs all models
│   │   ├── audio_extractor.py  # ffmpeg: extract audio from video
│   │   ├── transcriber.py      # Whisper: speech → text
│   │   ├── speech_analyser.py  # librosa + Praat: WPM, fillers, pitch
│   │   ├── content_analyser.py # sentence-transformers + custom model
│   │   ├── video_analyser.py   # MediaPipe + DeepFace: eye contact, posture
│   │   └── feedback_generator.py  # Rule-based coaching feedback
│   └── ml/
│       ├── train_custom_model.py   # Training script for your ORION dataset
│       └── dataset/
│           ├── weak/           # Place "weak" answer audio files here
│           ├── average/        # Place "average" answer audio files here
│           └── strong/         # Place "strong" answer audio files here
│
└── frontend/                   # React + Vite frontend
    ├── src/
    │   ├── App.jsx             # Router
    │   ├── main.jsx            # Entry point
    │   ├── index.css           # Global styles + CSS variables
    │   ├── api/client.js       # Axios API wrapper
    │   ├── hooks/useAuth.jsx   # Auth context + hook
    │   ├── components/
    │   │   ├── Layout.jsx      # Sidebar + page wrapper
    │   │   └── Layout.css
    │   └── pages/
    │       ├── LoginPage.jsx
    │       ├── RegisterPage.jsx
    │       ├── DashboardPage.jsx   # Score history + trend chart
    │       ├── InterviewPage.jsx   # Webcam recording flow
    │       └── AnalysisPage.jsx    # Full analysis results
    ├── index.html
    ├── vite.config.js
    └── package.json
```

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- ffmpeg (`sudo apt install ffmpeg` or `brew install ffmpeg`)

---

### 1. Database Setup

```bash
# Create the PostgreSQL database
psql -U postgres
CREATE DATABASE orion_db;
\q
```

---

### 2. Backend Setup

```bash
cd orion/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env — set your DATABASE_URL and SECRET_KEY

# Create database tables
python -c "from database import engine, Base; import models; Base.metadata.create_all(engine)"

# Start the server
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

### 3. Frontend Setup

```bash
cd orion/frontend

npm install
npm run dev
```

Frontend at: http://localhost:3000

---

### 4. Training Your Custom Model

Once you have your ORION audio dataset (40+ recordings labelled weak/average/strong):

```bash
# Organise files:
# backend/ml/dataset/weak/    ← "weak" answer .wav files
# backend/ml/dataset/average/ ← "average" answer .wav files  
# backend/ml/dataset/strong/  ← "strong" answer .wav files

cd orion/backend
source venv/bin/activate
python ml/train_custom_model.py
```

This will:
1. Transcribe all audio files using Whisper
2. Encode transcripts with sentence-transformers
3. Train a GradientBoostingClassifier
4. Save the model to `ml/orion_model.joblib`
5. Print accuracy and classification report

Then update your `.env`:
```
CUSTOM_MODEL_PATH=ml/orion_model.joblib
```

---

## How the Analysis Pipeline Works

When a user completes a session, `services/pipeline.py` runs for each answer:

```
Video file
    │
    ├──► audio_extractor.py  →  .wav file (ffmpeg, 16kHz mono)
    │
    ├──► transcriber.py      →  transcript text + duration (Whisper)
    │
    ├──► speech_analyser.py  →  WPM, filler count, pauses, pitch variance
    │       Uses: librosa, parselmouth (Praat)
    │
    ├──► content_analyser.py →  relevance, structure, vocabulary scores
    │       Uses: sentence-transformers (all-MiniLM-L6-v2)
    │             + your custom GradientBoosting model (if trained)
    │
    └──► video_analyser.py   →  eye contact %, posture score, emotion
            Uses: MediaPipe FaceMesh + Pose
                  DeepFace (emotion detection)

All scores → pipeline.py aggregates → overall_score = 
    0.40 × content + 0.35 × fluency + 0.25 × nonverbal

Deltas computed vs user's previous session.
feedback_generator.py produces 3–5 coaching feedback items.
Everything saved to PostgreSQL.
```

---

## Score Weights

| Component   | Weight | Sub-components |
|-------------|--------|----------------|
| Content     | 40%    | Relevance (35%), Structure (25%), Vocabulary (20%), Length (20%) + custom model boost |
| Fluency     | 35%    | WPM score (40%), Filler penalty (30%), Pause quality (20%), Pitch variety (10%) |
| Non-verbal  | 25%    | Eye contact (40%), Posture (30%), Emotion (20%), Face presence (10%) |

---

## Technology Stack

| Layer        | Technology |
|--------------|------------|
| Frontend     | React 18, Vite, Recharts |
| Backend      | FastAPI, SQLAlchemy |
| Database     | PostgreSQL |
| Auth         | JWT (python-jose + passlib) |
| Transcription| OpenAI Whisper (local) |
| Speech ML    | librosa, parselmouth/Praat |
| Content ML   | sentence-transformers, scikit-learn |
| Video ML     | MediaPipe, DeepFace |
| Custom Model | GradientBoostingClassifier (your data) |

---

## Environment Variables Reference

| Variable           | Description                                    | Default |
|--------------------|------------------------------------------------|---------|
| `DATABASE_URL`     | PostgreSQL connection string                   | required |
| `SECRET_KEY`       | JWT signing secret (change in production!)     | required |
| `WHISPER_MODEL`    | Whisper model size: tiny/base/small/medium     | `base` |
| `CUSTOM_MODEL_PATH`| Path to trained .joblib model file             | empty (disabled) |
| `UPLOAD_DIR`       | Directory to store uploaded video files        | `uploads` |
