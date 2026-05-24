// Achievements.js
// Propósito: Pantalla de logros del usuario con progreso y estado de desbloqueo
// Dependencias: react, react-router-dom, @auth0/auth0-react, axios, react-icons
// Fecha: 2026-05-07

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { api } from "../../api";
import { FiArrowLeft, FiTrendingUp, FiLock } from "react-icons/fi";
import "./Achievements.css";


const CATEGORY_ORDER = [
  "Primeros pasos",
  "Constancia",
  "Hitos de retos",
  "Progresión",
  "Excelencia",
];

const COLOR_MAP = {
  teal: { border: "rgba(16,185,129,0.35)", glow: "rgba(16,185,129,0.1)", text: "#10B981" },
  blue: { border: "rgba(14,165,233,0.35)", glow: "rgba(14,165,233,0.1)", text: "#0EA5E9" },
  purple: { border: "rgba(139,92,246,0.35)", glow: "rgba(139,92,246,0.1)", text: "#8B5CF6" },
  gold: { border: "rgba(245,158,11,0.35)", glow: "rgba(245,158,11,0.1)", text: "#F59E0B" },
  bronze: { border: "rgba(180,110,60,0.35)", glow: "rgba(180,110,60,0.08)", text: "#CD7F32" },
  silver: { border: "rgba(148,163,184,0.35)", glow: "rgba(148,163,184,0.08)", text: "#94A3B8" },
};

function ProgressBar({ value, goal, color }) {
  const pct = goal > 0 ? Math.min((value / goal) * 100, 100) : 0;
  const c = COLOR_MAP[color] || COLOR_MAP.blue;
  return (
    <div className="ach-bar-bg">
      <div
        className="ach-bar-fill"
        style={{ width: `${pct}%`, background: c.text }}
      />
    </div>
  );
}

function AchievementCard({ ach }) {
  const c = COLOR_MAP[ach.color] || COLOR_MAP.blue;
  const locked = !ach.unlocked;

  return (
    <div
      className={`ach-card ${locked ? "ach-card-locked" : "ach-card-unlocked"}`}
      style={
        !locked
          ? { borderColor: c.border, background: c.glow }
          : {}
      }
    >
      {/* Icon */}
      <div className={`ach-icon ${locked ? "ach-icon-locked" : ""}`}>
        {locked ? <FiLock size={18} color="rgba(241,245,249,0.2)" /> : <span>{ach.icon}</span>}
      </div>

      {/* Text */}
      <div className="ach-info">
        <div className="ach-name-row">
          <span
            className="ach-name"
            style={{ color: locked ? "rgba(241,245,249,0.35)" : "#f1f5f9" }}
          >
            {ach.name}
          </span>
          {ach.unlocked && ach.unlocked_date && (
            <span className="ach-date">{ach.unlocked_date}</span>
          )}
        </div>
        <p className="ach-desc">{ach.description}</p>

        {/* Progress label or bar */}
        {ach.progress_label ? (
          <p className="ach-progress-label" style={{ color: c.text }}>
            {ach.progress_label}
          </p>
        ) : (
          !ach.unlocked && (
            <div className="ach-progress-row">
              <ProgressBar value={ach.progress} goal={ach.goal} color={ach.color} />
              <span className="ach-progress-text">
                {ach.progress}/{ach.goal}
              </span>
            </div>
          )
        )}
      </div>

      {/* Badge */}
      {ach.unlocked && (
        <div className="ach-badge" style={{ color: c.text, borderColor: c.border }}>
          ✓
        </div>
      )}
    </div>
  );
}

function Achievements() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth0();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!authLoading && isAuthenticated && user) {
      loadAchievements();
    }
  }, [user, isAuthenticated, authLoading]);

  async function loadAchievements() {
    setLoading(true);
    setError(null);
    try {
      const userRes = await api.get(`/users/auth0/${user.sub}`);
      const userId = userRes.data.id;
      const achRes = await api.get(`/achievements/user/${userId}`);
      setData(achRes.data);
    } catch {
      setError("No se pudieron cargar los logros.");
    } finally {
      setLoading(false);
    }
  }

  // Agrupar logros por categoría
  const grouped = data
    ? CATEGORY_ORDER.reduce((acc, cat) => {
        const items = data.achievements.filter((a) => a.category === cat);
        if (items.length > 0) acc[cat] = items;
        return acc;
      }, {})
    : {};

  return (
    <div className="ach-wrap">
      {/* Navbar */}
      <div className="ach-navbar">
        <button className="ach-back-btn" onClick={() => navigate(-1)}>
          <FiArrowLeft size={18} />
        </button>
        <div className="ach-navbar-center">
          <span className="ach-navbar-icon">🏆</span>
          <span className="ach-navbar-title">Logros</span>
        </div>
        <button
          className="ach-stats-btn"
          onClick={() => navigate("/stats")}
        >
          <FiTrendingUp size={16} />
          <span>Stats</span>
        </button>
      </div>

      <div className="ach-content">
        {loading ? (
          <div className="ach-loading">
            <div className="ach-spinner" />
            <p>Cargando logros…</p>
          </div>
        ) : error ? (
          <div className="ach-error">{error}</div>
        ) : data ? (
          <>
            {/* Resumen */}
            <div className="ach-summary">
              <div className="ach-summary-main">
                <span className="ach-summary-count">{data.total_unlocked}</span>
                <span className="ach-summary-total">/ {data.total}</span>
              </div>
              <p className="ach-summary-label">logros desbloqueados</p>
              <div className="ach-summary-bar-bg">
                <div
                  className="ach-summary-bar-fill"
                  style={{
                    width: `${Math.round((data.total_unlocked / data.total) * 100)}%`,
                  }}
                />
              </div>
              {data.streak_days > 0 && (
                <p className="ach-summary-streak">
                  🔥 {data.streak_days} {data.streak_days === 1 ? "día" : "días"} de racha
                </p>
              )}
            </div>

            {/* Logros por categoría */}
            {Object.entries(grouped).map(([cat, items]) => (
              <div key={cat} className="ach-category">
                <div className="ach-category-header">
                  <span className="ach-category-name">{cat}</span>
                  <span className="ach-category-count">
                    {items.filter((a) => a.unlocked).length}/{items.length}
                  </span>
                </div>
                <div className="ach-list">
                  {items.map((ach) => (
                    <AchievementCard key={ach.id} ach={ach} />
                  ))}
                </div>
              </div>
            ))}
          </>
        ) : null}
      </div>
    </div>
  );
}

export default Achievements;