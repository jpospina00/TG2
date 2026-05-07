// Stats.js
// Propósito: Pantalla de estadísticas del usuario con métricas de rendimiento
// Dependencias: react, react-router-dom, @auth0/auth0-react, axios, react-icons
// Fecha: 2026-05-07

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import {
  FiArrowLeft,
  FiAward,
  FiTarget,
  FiClock,
  FiZap,
  FiTrendingUp,
  FiCheckCircle,
} from "react-icons/fi";
import "./Stats.css";

const API_URL = process.env.REACT_APP_API_URL;

const MODULE_OPTIONS = [
  { value: "todos", label: "Todos" },
  { value: "empathy", label: "Empatía" },
  { value: "networking", label: "Networking" },
];

const DIM_LABELS = {
  precision_emocional: "Precisión emocional",
  calidad_mensaje: "Calidad del mensaje",
  tono_empatico: "Tono empático",
  coherencia_contextual: "Coherencia contextual",
};

function StatCard({ icon, label, value, sub, accent }) {
  return (
    <div className={`st-card ${accent ? "st-card-accent" : ""}`}>
      <div className="st-card-icon">{icon}</div>
      <div className="st-card-body">
        <p className="st-card-value">{value}</p>
        <p className="st-card-label">{label}</p>
        {sub && <p className="st-card-sub">{sub}</p>}
      </div>
    </div>
  );
}

function RadarBar({ label, value }) {
  return (
    <div className="st-dim-row">
      <div className="st-dim-header">
        <span className="st-dim-label">{label}</span>
        <span className="st-dim-value">{value}/10</span>
      </div>
      <div className="st-dim-bar-bg">
        <div
          className="st-dim-bar-fill"
          style={{ width: `${(value / 10) * 100}%` }}
        />
      </div>
    </div>
  );
}

function Stats() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth0();
  const navigate = useNavigate();

  const [moduleFilter, setModuleFilter] = useState("todos");
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dbUserId, setDbUserId] = useState(null);

  // Obtener usuario de DB al montar
  useEffect(() => {
    if (!authLoading && isAuthenticated && user) {
      fetchUser();
    }
  }, [user, isAuthenticated, authLoading]);

  // Re-fetch stats cuando cambia el filtro o ya tenemos el userId
  useEffect(() => {
    if (dbUserId) {
      fetchStats(dbUserId, moduleFilter);
    }
  }, [dbUserId, moduleFilter]);

  async function fetchUser() {
    try {
      const res = await axios.get(`${API_URL}/users/auth0/${user.sub}`);
      setDbUserId(res.data.id);
    } catch {
      setError("No se pudo obtener el perfil de usuario.");
      setLoading(false);
    }
  }

  async function fetchStats(userId, module) {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(
        `${API_URL}/stats/user/${userId}?module=${module}`
      );
      setStats(res.data);
    } catch {
      setError("No se pudieron cargar las estadísticas.");
    } finally {
      setLoading(false);
    }
  }

  const approvalColor =
    !stats
      ? "#2563eb"
      : stats.approval_rate >= 70
      ? "#10B981"
      : stats.approval_rate >= 40
      ? "#F59E0B"
      : "#EF4444";

  return (
    <div className="st-wrap">
      {/* Navbar */}
      <div className="st-navbar">
        <button className="st-back-btn" onClick={() => navigate("/dashboard")}>
          <FiArrowLeft size={18} />
        </button>
        <div className="st-navbar-center">
          <FiTrendingUp size={16} color="#2563eb" />
          <span className="st-navbar-title">Mis estadísticas</span>
        </div>
        <button
          className="st-logros-btn"
          onClick={() => navigate("/achievements")}
        >
          <FiAward size={16} />
          <span>Logros</span>
        </button>
      </div>

      <div className="st-content">
        {/* Filtros */}
        <div className="st-filters">
          {MODULE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              className={`st-filter-btn ${
                moduleFilter === opt.value ? "st-filter-active" : ""
              }`}
              onClick={() => setModuleFilter(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="st-loading">
            <div className="st-spinner" />
            <p>Calculando estadísticas…</p>
          </div>
        ) : error ? (
          <div className="st-error">{error}</div>
        ) : stats ? (
          <>
            {/* Tarjetas principales */}
            <div className="st-cards-grid">
              <StatCard
                icon={<FiTarget size={20} color="#2563eb" />}
                label="Intentos totales"
                value={stats.total_attempts}
                sub={`${stats.total_completed} aprobados`}
              />
              <StatCard
                icon={
                  <FiCheckCircle
                    size={20}
                    color={approvalColor}
                  />
                }
                label="Tasa de aprobación"
                value={`${stats.approval_rate}%`}
                accent={stats.approval_rate >= 70}
              />
              <StatCard
                icon={<FiClock size={20} color="#0EA5E9" />}
                label="Tiempo total"
                value={stats.total_time || "0m"}
                sub="en sesiones activas"
              />
              <StatCard
                icon={<FiZap size={20} color="#F59E0B" />}
                label="Racha actual"
                value={`${stats.streak_days}d`}
                sub="días consecutivos"
                accent={stats.streak_days >= 3}
              />
            </div>

            {/* Aprobación por nivel */}
            {Object.keys(stats.approval_by_level).length > 0 && (
              <div className="st-section">
                <p className="st-section-title">Aprobación por nivel</p>
                <div className="st-level-bars">
                  {Object.entries(stats.approval_by_level).map(
                    ([level, pct]) => (
                      <div key={level} className="st-level-row">
                        <span className="st-level-name">
                          {level === "beginner"
                            ? "Principiante"
                            : level === "intermediate"
                            ? "Intermedio"
                            : "Avanzado"}
                        </span>
                        <div className="st-level-bar-bg">
                          <div
                            className="st-level-bar-fill"
                            style={{
                              width: `${pct}%`,
                              background:
                                level === "beginner"
                                  ? "#2563eb"
                                  : level === "intermediate"
                                  ? "#0EA5E9"
                                  : "#10B981",
                            }}
                          />
                        </div>
                        <span className="st-level-pct">{pct}%</span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Tiempo promedio por tipo */}
            {Object.keys(stats.avg_time_by_type).length > 0 && (
              <div className="st-section">
                <p className="st-section-title">Tiempo promedio por tipo</p>
                <div className="st-type-chips">
                  {Object.entries(stats.avg_time_by_type).map(
                    ([type, time]) => (
                      <div key={type} className="st-type-chip">
                        <span className="st-type-label">
                          {type === "simple"
                            ? "Simple"
                            : type === "conversational"
                            ? "Conversacional"
                            : type === "analysis"
                            ? "Análisis"
                            : type}
                        </span>
                        <span className="st-type-time">{time}</span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Dimensiones de empatía */}
            {Object.keys(stats.empathy_dimensions || {}).length > 0 && (
              <div className="st-section">
                <p className="st-section-title">
                  Dimensiones de empatía
                  <span className="st-section-badge">Promedio</span>
                </p>
                <div className="st-dims">
                  {Object.entries(stats.empathy_dimensions).map(
                    ([key, val]) => (
                      <RadarBar
                        key={key}
                        label={DIM_LABELS[key] || key}
                        value={val}
                      />
                    )
                  )}
                </div>
              </div>
            )}

            {/* Niveles desbloqueados */}
            <div className="st-footer-card">
              <FiAward size={18} color="#F59E0B" />
              <p className="st-footer-text">
                Has desbloqueado{" "}
                <strong>{stats.levels_unlocked}</strong>{" "}
                {stats.levels_unlocked === 1 ? "nivel" : "niveles"} superiores
                en el sistema
              </p>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

export default Stats;