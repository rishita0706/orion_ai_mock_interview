// ORION — Dashboard Page
import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { useAuth } from "../hooks/useAuth";
import { sessionsAPI, analysisAPI } from "../api/client";
import "./DashboardPage.css";

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions]   = useState([]);
  const [history, setHistory]     = useState([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    Promise.all([sessionsAPI.list(), analysisAPI.getHistory()])
      .then(([s, h]) => {
        setSessions(s.data);
        setHistory(h.data.map((d, i) => ({
          label: `S${i + 1}`,
          overall:   d.overall_score,
          content:   d.content_score,
          fluency:   d.fluency_score,
          nonverbal: d.nonverbal_score,
        })));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const completedSessions = sessions.filter((s) => s.completed && s.overall_score != null);
  const latestScore = completedSessions[0]?.overall_score;
  const improvement = completedSessions.length >= 2
    ? (completedSessions[0].overall_score - completedSessions[1].overall_score).toFixed(1)
    : null;

  const scoreColor = (s) => {
    if (s == null) return "var(--text-muted)";
    if (s >= 75) return "var(--green)";
    if (s >= 55) return "var(--amber)";
    return "var(--red)";
  };

  const formatDate = (iso) =>
    new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="chart-tooltip">
        <div className="tooltip-label">{label}</div>
        {payload.map((p) => (
          <div key={p.dataKey} className="tooltip-row">
            <span style={{ color: p.color }}>{p.name}</span>
            <span>{p.value?.toFixed(1)}</span>
          </div>
        ))}
      </div>
    );
  };

  if (loading) return <div className="page-loading">Loading dashboard…</div>;

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="dash-header">
        <div>
          <h1 className="dash-greeting">Hello, {user?.name?.split(" ")[0]} </h1>
          <p className="dash-subtext">
            {completedSessions.length === 0
              ? "Start your first session to see your analysis."
              : `${completedSessions.length} session${completedSessions.length > 1 ? "s" : ""} completed`}
          </p>
        </div>
        <button className="btn-start-session" onClick={() => navigate("/interview")}>
          + New Session
        </button>
      </div>

      {/* Stats row */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-label">Latest Score</div>
          <div className="stat-value" style={{ color: scoreColor(latestScore) }}>
            {latestScore != null ? latestScore.toFixed(1) : "—"}
          </div>
          <div className="stat-hint">out of 100</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Change</div>
          <div className="stat-value" style={{ color: improvement > 0 ? "var(--green)" : improvement < 0 ? "var(--red)" : "var(--text-muted)" }}>
            {improvement != null ? (improvement > 0 ? `+${improvement}` : improvement) : "—"}
          </div>
          <div className="stat-hint">vs previous</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Sessions</div>
          <div className="stat-value">{completedSessions.length}</div>
          <div className="stat-hint">completed</div>
        </div>
      </div>

      {/* Score trend chart */}
      {history.length >= 2 && (
        <div className="chart-card">
          <div className="card-title">Score Trend</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={history} margin={{ top: 8, right: 16, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="label" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="overall"   stroke="#5c7cfa" strokeWidth={2} dot={{ r: 4, fill: "#5c7cfa" }} name="Overall" />
              <Line type="monotone" dataKey="content"   stroke="#34d399" strokeWidth={1.5} dot={false} name="Content" strokeDasharray="4 2" />
              <Line type="monotone" dataKey="fluency"   stroke="#fbbf24" strokeWidth={1.5} dot={false} name="Fluency" strokeDasharray="4 2" />
              <Line type="monotone" dataKey="nonverbal" stroke="#f87171" strokeWidth={1.5} dot={false} name="Non-verbal" strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
          <div className="chart-legend">
            {[["#5c7cfa","Overall"],["#34d399","Content"],["#fbbf24","Fluency"],["#f87171","Non-verbal"]].map(([c,l]) => (
              <span key={l} className="legend-item"><span style={{ background: c }} className="legend-dot" />{l}</span>
            ))}
          </div>
        </div>
      )}

      {/* Session list */}
      <div className="section-header">
        <div className="card-title">Past Sessions</div>
      </div>

      {sessions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">◉</div>
          <div className="empty-title">No sessions yet</div>
          <div className="empty-body">Start a mock interview to get your first analysis.</div>
          <button className="btn-start-session" onClick={() => navigate("/interview")}>Start now</button>
        </div>
      ) : (
        <div className="session-list">
          {sessions.map((s, i) => (
            <div key={s.id} className="session-row">
              <div className="session-meta">
                <span className="session-num">Session #{sessions.length - i}</span>
                <span className="session-date">{formatDate(s.created_at)}</span>
              </div>
              <div className="session-scores">
                {s.overall_score != null && (
                  <>
                    <span className="score-pill" style={{ color: scoreColor(s.overall_score), borderColor: scoreColor(s.overall_score) }}>
                      {s.overall_score.toFixed(1)}
                    </span>
                  </>
                )}
                {!s.completed && <span className="badge-pending">Processing…</span>}
              </div>
              {s.completed && s.overall_score != null && (
                <Link to={`/analysis/${s.id}`} className="btn-view-analysis">View Analysis →</Link>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
