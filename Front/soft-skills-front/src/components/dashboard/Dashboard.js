// Dashboard.js
// Propósito: Pantalla principal con módulos, progreso e historial de retroalimentaciones
// Dependencias: react, react-router-dom, @auth0/auth0-react, axios, react-icons
// Fecha: 2026-03-20

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import {
  FiLogOut,
  FiMessageCircle,
  FiUsers,
  FiCheckCircle,
  FiXCircle,
  FiChevronDown,
  FiChevronUp,
} from "react-icons/fi";
import ErrorMessage from "../shared/ErrorMessage";
import "./Dashboard.css";

const API_URL = process.env.REACT_APP_API_URL;

function Dashboard() {
  const { user, logout, isAuthenticated, isLoading: authLoading } = useAuth0();
  const navigate = useNavigate();

  const [progress, setProgress] = useState([]);
  const [modules, setModules] = useState([]);
  const [historial, setHistorial] = useState([]);
  const [filtroModulo, setFiltroModulo] = useState("todos");
  const [expandedFeedback, setExpandedFeedback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [error, setError] = useState(null);

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "??";

  useEffect(() => {
    if (!authLoading && isAuthenticated && user) {
      initDashboard();
    }
  }, [user, isAuthenticated, authLoading]);

  async function initDashboard() {
  try {
    let dbUser;
    try {
      const res = await axios.get(`${API_URL}/users/auth0/${user.sub}`);
      dbUser = res.data;
    } catch {
      const res = await axios.post(`${API_URL}/users`, {
        auth0_id: user.sub,
        name: user.name,
        email: user.email,
      });
      dbUser = res.data;
    }

    // Peticiones en paralelo — perfil, módulos y progreso al mismo tiempo
    const [profileRes, modsRes, progRes] = await Promise.all([
      axios.get(`${API_URL}/students/profile/user/${dbUser.id}`),
      axios.get(`${API_URL}/modules`),
      axios.get(`${API_URL}/progress/user/${dbUser.id}`).catch(() => ({ data: [] })),
    ]);

    if (!profileRes.data.has_profile) {
      navigate("/onboarding");
      return;
    }

    setModules(modsRes.data);
    let userProgress = progRes.data;

    // Crear progreso faltante en paralelo
    const missingProgress = modsRes.data.filter(
      (mod) => !userProgress.find((p) => p.module_id === mod.id)
    );

    if (missingProgress.length > 0) {
      const newProgressItems = await Promise.all(
        missingProgress.map((mod) =>
          axios.post(`${API_URL}/progress`, {
            user_id: dbUser.id,
            module_id: mod.id,
            current_level: "beginner",
          }).then((r) => r.data).catch(() => null)
        )
      );
      userProgress = [...userProgress, ...newProgressItems.filter(Boolean)];
    }

    setProgress(userProgress);

    // Cargar historial sin bloquear el render
    loadHistorial(dbUser.id, modsRes.data);

  } catch (err) {
    console.error("Error iniciando dashboard:", err);
    setError("No se pudo cargar tu información. Verifica que el servidor esté activo.");
  } finally {
    setLoading(false); // el dashboard ya es visible aunque el historial siga cargando
  }
}

  async function loadHistorial(userId, mods) {
  try {
    const convRes = await axios.get(`${API_URL}/conversations/user/${userId}`);
    const conversations = convRes.data;

    if (conversations.length === 0) {
      setHistorial([]);
      return;
    }

    // Todas las peticiones de feedback, mensajes y reto en paralelo
    const items = await Promise.all(
      conversations.map(async (conv) => {
        try {
          const [fbRes, msgRes, challengeRes] = await Promise.all([
            axios.get(`${API_URL}/feedback/conversation/${conv.id}`),
            axios.get(`${API_URL}/messages/conversation/${conv.id}`),
            axios.get(`${API_URL}/challenges/${conv.challenge_id}`),
          ]);

          const modulo = mods.find((m) => m.id === challengeRes.data.module_id);

          return {
            conversation: conv,
            feedback: fbRes.data,
            messages: msgRes.data,
            challenge: challengeRes.data,
            modulo,
          };
        } catch {
          return null;
        }
      })
    );

    const validItems = items
      .filter(Boolean)
      .sort(
        (a, b) =>
          new Date(b.conversation.started_at) -
          new Date(a.conversation.started_at)
      );

    setHistorial(validItems);
  } catch (err) {
    console.error("Error cargando historial:", err);
  }
}

  function getLevelLabel(level) {
    const labels = {
      beginner: "Nivel inicial",
      intermediate: "Nivel intermedio",
      advanced: "Nivel avanzado",
    };
    return labels[level] || level;
  }

  function getModuleProgress(moduleId) {
    return progress.find((p) => p.module_id === moduleId);
  }

  function getModuleIcon(moduleName) {
    if (moduleName === "empathy")
      return <FiMessageCircle size={22} color="#2563EB" />;
    return <FiUsers size={22} color="#0EA5E9" />;
  }

  function getCompletedCount(moduleId) {
    return historial.filter(
      (h) => h.modulo?.id === moduleId && h.feedback?.completed,
    ).length;
  }

  function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString("es-CO", {
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  const historialFiltrado =
    filtroModulo === "todos"
      ? historial
      : historial.filter((h) => h.modulo?.name === filtroModulo);

  const totalAprobados = historial.filter((h) => h.feedback?.completed).length;

  if (loading || authLoading) {
    return (
      <div className="db-loading">
        <div className="db-loading-spinner"></div>
        <p>Cargando tu progreso...</p>
      </div>
    );
  }

  return (
    <div className="db-wrap">
      {/* Navbar */}
      <nav className="db-navbar">
        <div className="db-brand">
          <div className="db-logo">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path
                d="M9 2a7 7 0 100 14A7 7 0 009 2zm0 2a1 1 0 110 2 1 1 0 010-2zm0 9a4 4 0 01-3.33-1.8c.03-.99 2.22-1.53 3.33-1.53 1.1 0 3.3.54 3.33 1.53A4 4 0 019 13z"
                fill="white"
              />
            </svg>
          </div>
          <span className="db-brand-name">Entrenador Virtual</span>
        </div>
        <button
          className="db-avatar"
          onClick={() => setShowLogoutModal(true)}
          title="Cerrar sesión"
        >
          {initials}
        </button>
      </nav>

      <div className="db-content">
        {/* Saludo */}
        <div className="db-greeting">
          <h1 className="db-greeting-title">
            Hola, {user?.name?.split(" ")[0] || "estudiante"}
          </h1>
          <p className="db-greeting-sub">
            Continúa entrenando tus habilidades blandas
          </p>
        </div>
        {error && (
          <ErrorMessage
            title="Error de conexión"
            message={error}
            onRetry={() => {
              setError(null);
              setLoading(true);
              initDashboard();
            }}
          />
        )}

        {/* Stats */}
        <div className="db-stats">
          <div className="db-stat-card">
            <p className="db-stat-number" style={{ color: "#60A5FA" }}>
              {totalAprobados}
            </p>
            <p className="db-stat-label">Retos aprobados</p>
          </div>
          <div className="db-stat-card">
            <p className="db-stat-number" style={{ color: "#38BDF8" }}>
              {historial.length}
            </p>
            <p className="db-stat-label">Intentos totales</p>
          </div>
          <div className="db-stat-card">
            <p className="db-stat-number" style={{ color: "#F1F5F9" }}>
              {progress.filter((p) => p.current_level !== "beginner").length}
            </p>
            <p className="db-stat-label">Niveles superados</p>
          </div>
        </div>

        {/* Módulos */}
        <p className="db-section-title">Mis módulos</p>
        <div className="db-modules">
          {modules.map((mod) => {
            const prog = getModuleProgress(mod.id);
            const completed = getCompletedCount(mod.id);
            const pct = Math.min(Math.round((completed / 5) * 100), 100);
            const isEmpathy = mod.name === "empathy";

            return (
              <div
                key={mod.id}
                className="db-module-card"
                onClick={() => {
                  if (mod.name === "empathy") {
                    navigate(`/empathy/${mod.id}`);
                  } else {
                    navigate(`/module/${mod.id}`);
                  }
                }}
              >
                <div
                  className={`db-module-icon ${isEmpathy ? "icon-blue" : "icon-cyan"}`}
                >
                  {getModuleIcon(mod.name)}
                </div>
                <p className="db-module-name">
                  {isEmpathy ? "Empatía" : "Networking"}
                </p>
                <span
                  className={`db-level-badge ${isEmpathy ? "badge-blue" : "badge-cyan"}`}
                >
                  {getLevelLabel(prog?.current_level || "beginner")}
                </span>
                <div className="db-progress-bar-wrap">
                  <div
                    className={`db-progress-bar-fill ${isEmpathy ? "fill-blue" : "fill-cyan"}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <div className="db-progress-meta">
                  <span>{pct}%</span>
                  <span>{completed}/5 retos</span>
                </div>
                <button
                  className={`db-continue-btn ${isEmpathy ? "" : "btn-cyan"}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (mod.name === "empathy") {
                      navigate(`/empathy/${mod.id}`);
                    } else {
                      navigate(`/module/${mod.id}`);
                    }
                  }}
                >
                  Continuar
                </button>
              </div>
            );
          })}
        </div>

        {/* Historial */}
        <div className="db-historial-header">
          <p className="db-section-title" style={{ margin: 0 }}>
            Historial de retroalimentaciones
          </p>
          <div className="db-filtros">
            {["todos", "empathy", "networking"].map((f) => (
              <button
                key={f}
                className={`db-filtro-btn ${filtroModulo === f ? "filtro-active" : ""}`}
                onClick={() => setFiltroModulo(f)}
              >
                {f === "todos"
                  ? "Todos"
                  : f === "empathy"
                    ? "Empatía"
                    : "Networking"}
              </button>
            ))}
          </div>
        </div>

        {historialFiltrado.length === 0 ? (
          <p className="db-empty">
            {filtroModulo === "todos"
              ? "Aún no has completado ningún reto. ¡Empieza ahora!"
              : "No hay intentos en este módulo todavía."}
          </p>
        ) : (
          <div className="db-historial-list">
            {historialFiltrado.map((item, i) => (
              <div key={i} className="db-historial-item">
                {/* Header tarjeta */}
                <div
                  className="db-historial-item-header"
                  onClick={() =>
                    setExpandedFeedback(expandedFeedback === i ? null : i)
                  }
                >
                  <div className="db-historial-item-left">
                    <div
                      className={`db-historial-icon ${item.feedback?.completed ? "icon-ok" : "icon-fail"}`}
                    >
                      {item.feedback?.completed ? (
                        <FiCheckCircle size={16} color="#10B981" />
                      ) : (
                        <FiXCircle size={16} color="#EF4444" />
                      )}
                    </div>
                    <div>
                      <p className="db-historial-title">
                        {item.challenge?.agent_profile
                          ?.split(" ")
                          .slice(0, 4)
                          .join(" ")}
                      </p>
                      <p className="db-historial-meta">
                        <span
                          className={`db-historial-modulo ${item.modulo?.name === "empathy" ? "mod-blue" : "mod-cyan"}`}
                        >
                          {item.modulo?.name === "empathy"
                            ? "Empatía"
                            : "Networking"}
                        </span>
                        · {formatDate(item.conversation.started_at)}
                      </p>
                    </div>
                  </div>
                  <div className="db-historial-item-right">
                    <span
                      className={`db-historial-result ${item.feedback?.completed ? "result-ok" : "result-fail"}`}
                    >
                      {item.feedback?.completed ? "Aprobado" : "No aprobado"}
                    </span>
                    {expandedFeedback === i ? (
                      <FiChevronUp size={16} color="rgba(241,245,249,0.4)" />
                    ) : (
                      <FiChevronDown size={16} color="rgba(241,245,249,0.4)" />
                    )}
                  </div>
                </div>

                {/* Detalle expandido */}
                {expandedFeedback === i && (
                  <div className="db-historial-body">
                    {/* Mensajes */}
                    {item.messages.length > 0 && (
                      <>
                        <p className="db-historial-section-label">
                          Conversación
                        </p>
                        <div className="db-historial-messages">
                          {item.messages.map((msg, j) => (
                            <div
                              key={j}
                              className={`db-historial-msg ${msg.role === "user" ? "msg-user-hist" : "msg-agent-hist"}`}
                            >
                              <span className="db-historial-msg-role">
                                {msg.role === "user" ? "Tú" : "Agente"}
                              </span>
                              <p className="db-historial-msg-content">
                                {msg.content}
                              </p>
                            </div>
                          ))}
                        </div>
                      </>
                    )}

                    {/* Retroalimentación */}
                    <p className="db-historial-section-label">
                      Retroalimentación de la IA
                    </p>
                    <div className="db-historial-feedback">
                      <p className="db-historial-feedback-text">
                        {(() => {
                          try {
                            const parsed = JSON.parse(item.feedback?.content);
                            return parsed.feedback || item.feedback?.content;
                          } catch {
                            return item.feedback?.content;
                          }
                        })()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal cerrar sesión */}
      {showLogoutModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowLogoutModal(false)}
        >
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon modal-icon-danger">
              <FiLogOut size={24} color="#EF4444" />
            </div>
            <h3 className="modal-title">¿Cerrar sesión?</h3>
            <p className="modal-desc">
              Tu progreso está guardado. Podrás continuar desde donde lo
              dejaste.
            </p>
            <button
              className="modal-btn-danger"
              onClick={() =>
                logout({ logoutParams: { returnTo: window.location.origin } })
              }
            >
              Sí, cerrar sesión
            </button>
            <button
              className="modal-btn-cancel"
              onClick={() => setShowLogoutModal(false)}
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
