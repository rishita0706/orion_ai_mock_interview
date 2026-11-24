// ORION — Register Page
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import "./AuthPage.css";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", institution: "" });
  const [error, setError]   = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form.name, form.email, form.password, form.institution);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-bg">
      <div className="auth-card">
        <div className="auth-logo">ORION</div>
        <div className="auth-logo-sub">Oral Reasoning &amp; Interview Network</div>
        <h1 className="auth-title">Create account</h1>
        <p className="auth-subtitle">Start practising today — it's free</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Full name</label>
            <input type="text" value={form.name} onChange={set("name")} placeholder="Arjun Sharma" required />
          </div>
          <div className="field">
            <label>Email address</label>
            <input type="email" value={form.email} onChange={set("email")} placeholder="you@university.ac.in" required />
          </div>
          <div className="field">
            <label>Institution (optional)</label>
            <input type="text" value={form.institution} onChange={set("institution")} placeholder="Delhi University" />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={form.password} onChange={set("password")} placeholder="Min. 8 characters" required minLength={8} />
          </div>
          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? "Creating account…" : "Create account →"}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
