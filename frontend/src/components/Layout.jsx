
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import "./Layout.css";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-text">ORION</span>
          <span className="logo-sub">AI Interview Coach</span>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            <span className="nav-icon">⊞</span> Dashboard
          </NavLink>
          <NavLink to="/interview" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            <span className="nav-icon">◉</span> New Session
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="user-pill">
            <div className="user-avatar">{user?.name?.[0]?.toUpperCase()}</div>
            <div className="user-info">
              <div className="user-name">{user?.name}</div>
              <div className="user-email">{user?.email}</div>
            </div>
          </div>
          <button className="logout-btn" onClick={handleLogout}>Sign out</button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
