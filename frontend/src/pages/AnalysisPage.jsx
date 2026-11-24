// ORION — Analysis Page
// Displays full session analysis: scores, improvement deltas, detailed metrics, AI feedback
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts";
import { analysisAPI } from "../api/client";
import "./AnalysisPage.css";

export default function AnalysisPage() {
  const { sessionId } = useParams();
  const navigate      = useNavigate();
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState("");

  useEffect(() => {
    analysisAPI.get(sessionId)
      .then((r) => setData(r.data))
      .catch((e) => setError(e.response?.data?.detail || "Failed to load analysis."))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <div className="page-loading">Loading analysis…</div>;
  if (error)   return (
    <div className="analysis-error">
      <p>{error}</p>
      <button onClick={() => navigate("/dashboard")}>← Back to Dashboard</button>
    </div>
  );

  const { overall_score, content_score, fluency_score, nonverbal_score,
          delta_overall, delta_content, delta_fluency, delta_nonverbal,
          speech_metrics, nonverbal_metrics, content_metrics, ai_feedback } = data;

  const scoreColor = (s) => {
    if (s == null) return "var(--text-muted)";
    if (s >= 75) return "var(--green)";
    if (s >= 55) return "var(--amber)";
    return "var(--red)";
  };

  const deltaLabel = (d) => {
    if (d == null) return { text: "First session", color: "var(--text-muted)" };
    if (d > 0)     return { text: `+${d.toFixed(1)}`, color: "var(--green)" };
    if (d < 0)     return { text: d.toFixed(1),       color: "var(--red)" };
    return { text: "No change", color: "var(--text-muted)" };
  };

  const radarData = [
    { subject: "Content",   value: content_score   ?? 0 },
    { subject: "Fluency",   value: fluency_score   ?? 0 },
    { subject: "Non-verbal",value: nonverbal_score ?? 0 },
    { subject: "Relevance", value: _avg(content_metrics?.relevance_score) },
    { subject: "Structure", value: _avg(content_metrics?.structure_score) },
    { subject: "Vocab",     value: _avg(content_metrics?.vocab_score) },
  ];

  const speechRows = [
    ["Words per minute",  _avg(speech_metrics?.wpm)?.toFixed(0), "110–150 ideal"],
    ["Filler words",      _avg(speech_metrics?.filler_count)?.toFixed(0), "< 5 ideal"],
    ["Pauses detected",   _avg(speech_metrics?.pause_count)?.toFixed(0), "2–8 ideal"],
    ["Pitch variance",    _avg(speech_metrics?.pitch_std_hz)?.toFixed(1) + " Hz", "Higher = varied"],
  ];

  const nonverbalRows = [
    ["Eye contact",       _avg(nonverbal_metrics?.eye_contact_pct)?.toFixed(0) + "%", "> 70% ideal"],
    ["Posture score",     _avg(nonverbal_metrics?.posture_score)?.toFixed(0), "> 70 ideal"],
    ["Distraction events",_avg(nonverbal_metrics?.distraction_events)?.toFixed(0), "< 3 ideal"],
    ["Dominant emotion",  nonverbal_metrics?.dominant_emotion ?? "—", "Neutral/positive"],
  ];

  const sentimentClass = (s) =>
    s === "positive" ? "feedback-positive" : s === "warning" ? "feedback-warning" : "feedback-neutral";

  return (
    <div className="analysis-page">
      {/* Header */}
      <div className="analysis-header">
        <div>
          <button className="btn-back" onClick={() => navigate("/dashboard")}>← Dashboard</button>
          <h1 className="analysis-title">Session Analysis</h1>
        </div>
        <div className="overall-badge" style={{ color: scoreColor(overall_score), borderColor: scoreColor(overall_score) }}>
          {overall_score?.toFixed(1) ?? "—"} / 100
        </div>
      </div>

      {/* Score cards */}
      <div className="score-cards">
        {[
          { label: "Overall",     score: overall_score,   delta: delta_overall },
          { label: "Content",     score: content_score,   delta: delta_content },
          { label: "Fluency",     score: fluency_score,   delta: delta_fluency },
          { label: "Non-verbal",  score: nonverbal_score, delta: delta_nonverbal },
        ].map(({ label, score, delta }) => {
          const d = deltaLabel(delta);
          return (
            <div key={label} className="score-card">
              <div className="score-card-label">{label}</div>
              <div className="score-card-value" style={{ color: scoreColor(score) }}>
                {score?.toFixed(1) ?? "—"}
              </div>
              <div className="score-card-bar">
                <div className="score-bar-fill" style={{ width: `${score ?? 0}%`, background: scoreColor(score) }} />
              </div>
              <div className="score-card-delta" style={{ color: d.color }}>{d.text}</div>
            </div>
          );
        })}
      </div>

      <div className="analysis-grid">
        {/* Radar chart */}
        <div className="a-card">
          <div className="a-card-title">Skills Radar</div>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: "var(--text-primary)" }}
              />
              <Radar name="Score" dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.2} dot />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Improvement deltas */}
        <div className="a-card">
          <div className="a-card-title">vs Previous Session</div>
          {delta_overall == null ? (
            <div className="no-delta">This is your first session. Complete another to see improvement tracking.</div>
          ) : (
            <div className="delta-list">
              {[
                ["Overall Score",  delta_overall],
                ["Content",        delta_content],
                ["Fluency",        delta_fluency],
                ["Non-verbal",     delta_nonverbal],
              ].map(([label, d]) => {
                const dl = deltaLabel(d);
                return (
                  <div key={label} className="delta-row">
                    <span className="delta-label">{label}</span>
                    <span className="delta-val" style={{ color: dl.color }}>{dl.text}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Speech metrics */}
        <div className="a-card">
          <div className="a-card-title">Speech Metrics</div>
          <table className="metrics-table">
            <tbody>
              {speechRows.map(([label, val, hint]) => (
                <tr key={label}>
                  <td className="metric-label">{label}</td>
                  <td className="metric-val">{val ?? "—"}</td>
                  <td className="metric-hint">{hint}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Non-verbal metrics */}
        <div className="a-card">
          <div className="a-card-title">Non-Verbal Metrics</div>
          <table className="metrics-table">
            <tbody>
              {nonverbalRows.map(([label, val, hint]) => (
                <tr key={label}>
                  <td className="metric-label">{label}</td>
                  <td className="metric-val">{val ?? "—"}</td>
                  <td className="metric-hint">{hint}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* AI Feedback */}
        <div className="a-card a-card-full">
          <div className="a-card-title">AI Coaching Feedback</div>
          {(!ai_feedback || ai_feedback.length === 0) ? (
            <div className="no-delta">No feedback available for this session.</div>
          ) : (
            <div className="feedback-list">
              {ai_feedback.map((f, i) => (
                <div key={i} className={`feedback-item ${sentimentClass(f.sentiment)}`}>
                  <div className="feedback-category">{f.category}</div>
                  <div className="feedback-text">{f.text}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="analysis-actions">
        <button className="btn-new-session" onClick={() => navigate("/interview")}>
          + Start New Session
        </button>
      </div>
    </div>
  );
}

function _avg(val) {
  if (val == null) return null;
  if (Array.isArray(val)) return val.length ? val.reduce((a, b) => a + b, 0) / val.length : null;
  return val;
}
