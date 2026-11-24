// ORION — Interview Page
// Full webcam recording flow: create session → 4 questions → record each → upload → complete
import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { sessionsAPI } from "../api/client";
import "./InterviewPage.css";

const STAGES = { SETUP: "setup", READY: "ready", RECORDING: "recording", REVIEW: "review", UPLOADING: "uploading", DONE: "done" };

export default function InterviewPage() {
  const navigate = useNavigate();
  const videoRef      = useRef(null);
  const mediaRecorder = useRef(null);
  const streamRef     = useRef(null);
  const chunksRef     = useRef([]);
  const timerRef      = useRef(null);

  const [stage, setStage]           = useState(STAGES.SETUP);
  const [session, setSession]       = useState(null);   // { session_id, questions }
  const [qIndex, setQIndex]         = useState(0);
  const [recordings, setRecordings] = useState([]);     // array of Blobs
  const [currentBlob, setCurrentBlob] = useState(null);
  const [elapsed, setElapsed]       = useState(0);
  const [permError, setPermError]   = useState("");
  const [uploading, setUploading]   = useState(false);
  const [error, setError]           = useState("");

  const question = session?.questions?.[qIndex];

  // ── Camera setup ────────────────────────────────────────────────────────────
  const startCamera = useCallback(async () => {
    setPermError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, facingMode: "user" },
        audio: true,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.muted = true; // prevent echo
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
        };
      }
    } catch (err) {
      setPermError("Camera/microphone access denied. Please allow permissions and reload.");
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  // ── Session creation ─────────────────────────────────────────────────────────
  const handleStartSession = async () => {
    setError("");
    try {
      const { data } = await sessionsAPI.create();
      setSession(data);
      await startCamera();
      setStage(STAGES.READY);
    } catch (e) {
      setError("Failed to start session. Please try again.");
    }
  };

  // ── Recording ────────────────────────────────────────────────────────────────
  const startRecording = () => {
    if (!streamRef.current) return;
    chunksRef.current = [];
    setElapsed(0);

    const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
      ? "video/webm;codecs=vp9"
      : "video/webm";

    mediaRecorder.current = new MediaRecorder(streamRef.current, { mimeType });
    mediaRecorder.current.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    mediaRecorder.current.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "video/webm" });
      setCurrentBlob(blob);
      setStage(STAGES.REVIEW);
    };

    mediaRecorder.current.start(1000);
    setStage(STAGES.RECORDING);

    timerRef.current = setInterval(() => {
      setElapsed((e) => {
        if (e >= 120) { stopRecording(); return e; }
        return e + 1;
      });
    }, 1000);
  };

  const stopRecording = () => {
    clearInterval(timerRef.current);
    if (mediaRecorder.current?.state !== "inactive") {
      mediaRecorder.current.stop();
    }
  };

  // ── Save answer & move to next ───────────────────────────────────────────────
  const acceptAnswer = () => {
    setRecordings((prev) => [...prev, { blob: currentBlob, question }]);
    setCurrentBlob(null);

    const isLast = qIndex >= session.questions.length - 1;
    if (isLast) {
      setStage(STAGES.UPLOADING);
    } else {
      setQIndex((i) => i + 1);
      setElapsed(0);
      setStage(STAGES.READY);
    }
  };

  const retakeAnswer = () => {
    setCurrentBlob(null);
    setElapsed(0);
    setStage(STAGES.READY);
  };

  // ── Upload all answers ────────────────────────────────────────────────────────
  useEffect(() => {
    if (stage !== STAGES.UPLOADING) return;
    const upload = async () => {
      setUploading(true);
      try {
        for (const rec of recordings) {
          const form = new FormData();
          form.append("question_id",   rec.question.id);
          form.append("question_text", rec.question.text);
          form.append("video", rec.blob, `answer_q${rec.question.id}.webm`);
          await sessionsAPI.uploadAnswer(session.session_id, form);
        }
        await sessionsAPI.complete(session.session_id);
        stopCamera();
        navigate(`/analysis/${session.session_id}`);
      } catch (e) {
        setError("Upload failed. Please check your connection and try again.");
        setUploading(false);
        setStage(STAGES.REVIEW);
      }
    };
    upload();
  }, [stage]);

  // Cleanup camera on unmount
  useEffect(() => () => { stopCamera(); clearInterval(timerRef.current); }, []);

  const formatTime = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  const progressPct = session ? ((qIndex + (stage === STAGES.UPLOADING ? 1 : 0)) / session.questions.length) * 100 : 0;

  // ── Render ────────────────────────────────────────────────────────────────────
  if (stage === STAGES.SETUP) {
    return (
      <div className="interview-setup">
        <div className="setup-card">
          <h1 className="setup-title">Ready to practise?</h1>
          <p className="setup-body">
            You'll be given <strong>4 randomly selected</strong> interview questions.<br />
            Answer each one on camera — speak naturally for 30–90 seconds.
          </p>
          <div className="setup-tips">
            {["Sit facing a window or lamp — light on your face", "Position camera at eye level", "Use a quiet room with a plain background", "Speak naturally — don't read from notes"].map((t) => (
              <div key={t} className="tip-row"><span className="tip-dot" />  {t}</div>
            ))}
          </div>
          {error && <div className="interview-error">{error}</div>}
          <button className="btn-primary-lg" onClick={handleStartSession}>Start Session →</button>
        </div>
      </div>
    );
  }

  if (stage === STAGES.UPLOADING) {
    return (
      <div className="interview-setup">
        <div className="setup-card" style={{ textAlign: "center" }}>
          <div className="upload-spinner" />
          <h2 style={{ marginBottom: 8 }}>Analysing your session…</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
            Transcribing speech, scoring content, and evaluating non-verbal cues.<br />
            This takes about 30–60 seconds.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="interview-page">
      {/* Top progress bar */}
      <div className="progress-header">
        <div className="progress-label">
          Question {qIndex + 1} of {session?.questions?.length}
        </div>
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
      </div>

      <div className="interview-layout">
        {/* Video panel */}
        <div className="video-panel">
          <div className={`video-frame ${stage === STAGES.RECORDING ? "recording" : ""}`}>
            <video ref={videoRef} autoPlay playsInline muted className="video-feed" />
            {stage === STAGES.RECORDING && (
              <div className="rec-overlay">
                <span className="rec-dot" />
                <span className="rec-timer">{formatTime(elapsed)}</span>
              </div>
            )}
            {permError && <div className="video-error">{permError}</div>}
          </div>

          {/* Recording controls */}
          <div className="video-controls">
            {stage === STAGES.READY && (
              <button className="btn-record" onClick={startRecording}>
                ● Start Recording
              </button>
            )}
            {stage === STAGES.RECORDING && (
              <button className="btn-stop" onClick={stopRecording}>
                ■ Stop Recording
                <span className="hint-text">({formatTime(elapsed)} / 1:30)</span>
              </button>
            )}
          </div>
        </div>

        {/* Question panel */}
        <div className="question-panel">
          <div className="q-domain">{question?.domain}</div>
          <div className="q-text">"{question?.text}"</div>

          <div className="q-dots">
            {session?.questions?.map((_, i) => (
              <div key={i} className={`q-dot ${i < qIndex ? "done" : i === qIndex ? "active" : ""}`} />
            ))}
          </div>

          <div className="q-tips-box">
            <div className="q-tips-title">Tips</div>
            <ul className="q-tips-list">
              <li>Take 10 seconds to gather your thoughts first</li>
              <li>Use a specific example (STAR method)</li>
              <li>Look at the camera, not the screen</li>
              <li>Aim for 45–70 seconds</li>
            </ul>
          </div>

          {/* Review controls (after recording) */}
          {stage === STAGES.REVIEW && currentBlob && (
            <div className="review-section">
              <div className="review-label">Review your answer</div>
              <video
                src={URL.createObjectURL(currentBlob)}
                controls
                className="review-video"
              />
              <div className="review-btns">
                <button className="btn-retake" onClick={retakeAnswer}>↩ Retake</button>
                <button className="btn-accept" onClick={acceptAnswer}>
                  {qIndex >= (session?.questions?.length ?? 0) - 1 ? "Submit all →" : "Next question →"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}