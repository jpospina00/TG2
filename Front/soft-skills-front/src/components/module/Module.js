// Module.js
// Propósito: Pantalla del módulo con personajes y panel de detalle
// Dependencias: react, react-router-dom, @auth0/auth0-react, axios, react-icons
// Fecha: 2026-03-20

import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import {
  FiArrowLeft,
  FiLock,
  FiMessageCircle,
  FiUsers,
  FiBookOpen,
  FiRefreshCw,
} from "react-icons/fi";
import "./Module.css";

const API_URL = process.env.REACT_APP_API_URL;

const LEVELS = ["beginner", "intermediate", "advanced"];
const LEVEL_LABELS = {
  beginner: "Inicial",
  intermediate: "Intermedio",
  advanced: "Avanzado",
};

const AVATAR_COLORS = [
  "linear-gradient(135deg, #F59E0B, #EF4444)",
  "linear-gradient(135deg, #EC4899, #8B5CF6)",
  "linear-gradient(135deg, #2563EB, #0EA5E9)",
  "linear-gradient(135deg, #10B981, #0EA5E9)",
  "linear-gradient(135deg, #8B5CF6, #EC4899)",
];

function getInitials(text) {
  const words = text.trim().split(" ");
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
  return text.slice(0, 2).toUpperCase();
}

function getShortName(agentProfile) {
  const words = agentProfile.trim().split(" ");
  
  // Si empieza con nombre propio (mayúscula y corto) usarlo
  if (words[0].length <= 10 && words[0][0] === words[0][0].toUpperCase()) {
    return words[0];
  }
  
  // Buscar patrones como "Profesor X", "Reclutador X", "Compañero X"
  const roles = ["Profesor", "Profesora", "Reclutador", "Reclutadora", 
                 "Compañero", "Compañera", "Director", "Directora",
                 "Gerente", "Inversor", "Inversora", "Mentor", "Mentora",
                 "Gatekeeper", "Colega", "Estudiante", "Amigo", "Amiga"];
  
  for (const role of roles) {
    if (agentProfile.includes(role)) {
      const idx = agentProfile.indexOf(role);
      const afterRole = agentProfile.slice(idx).split(" ");
      if (afterRole.length >= 2 && afterRole[1].length > 2) {
        return `${afterRole[0]} ${afterRole[1]}`;
      }
      return afterRole[0];
    }
  }
  
  // Fallback: primeras 2 palabras
  return words.slice(0, 2).join(" ");
}

function Module() {
  const { moduleId } = useParams();
  const { user } = useAuth0();
  const navigate = useNavigate();

  const [moduleInfo, setModuleInfo] = useState(null);
  const [challenges, setChallenges] = useState([]);
  const [progress, setProgress] = useState(null);
  const [userId, setUserId] = useState(null);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [activeLevel, setActiveLevel] = useState("beginner");
  const [completedIds, setCompletedIds] = useState([]);
  const [failedIds, setFailedIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showResetModal, setShowResetModal] = useState(false);

  const [challengeConvMap, setChallengeConvMap] = useState({});

  useEffect(() => {
    if (user) loadModule();
  }, [user, moduleId]);

  async function loadModule() {
    try {
      const userRes = await axios.get(`${API_URL}/users/auth0/${user.sub}`);
      const dbUser = userRes.data;
      setUserId(dbUser.id);

      const modRes = await axios.get(`${API_URL}/modules/${moduleId}`);
      setModuleInfo(modRes.data);

      const diagRes = await axios.get(
        `${API_URL}/diagnostic/user/${dbUser.id}/module/${moduleId}`,
      );

      if (!diagRes.data.has_diagnostic) {
        navigate(`/module/${moduleId}/diagnostic`);
        return;
      }

      const progRes = await axios.get(`${API_URL}/progress/user/${dbUser.id}`);
      const modProgress = progRes.data.find(
        (p) => p.module_id === parseInt(moduleId),
      );
      setProgress(modProgress);
      setActiveLevel(modProgress?.current_level || "beginner");

      // Pasar dbUser.id directamente para no depender del estado
      await loadChallengesWithUser(
        moduleId,
        modProgress?.current_level || "beginner",
        dbUser.id,
      );

      const convRes = await axios.get(
  `${API_URL}/conversations/user/${dbUser.id}`,
);
const conversations = convRes.data;

const completed = [];
const failed = [];
const convMap = {};

for (const conv of conversations) {
  try {
    const fbRes = await axios.get(
      `${API_URL}/feedback/conversation/${conv.id}`,
    );
    if (fbRes.data.completed) {
      completed.push(conv.challenge_id);
      // Guardar la conversacion mas reciente completada por reto
      convMap[conv.challenge_id] = conv.id;
    } else {
      failed.push(conv.challenge_id);
    }
  } catch {}
}
setCompletedIds(completed);
setFailedIds(failed);
setChallengeConvMap(convMap);
    } catch (err) {
      console.error("Error cargando módulo:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadChallengesWithUser(modId, level, uid) {
    try {
      const res = await axios.get(
        `${API_URL}/challenges/module/${modId}/level/${level}`,
        { params: { user_id: uid } },
      );
      setChallenges(res.data);
    } catch (err) {
      console.error("Error cargando retos:", err);
    }
  }

  async function loadChallenges(moduleName, level) {
    try {
      const res = await axios.get(
        `${API_URL}/challenges/module/${moduleId}/level/${level}`,
        { params: { user_id: userId } },
      );
      setChallenges(res.data);
    } catch (err) {
      console.error("Error cargando retos:", err);
    }
  }

  async function handleResetDiagnostic() {
    try {
      await axios.delete(
        `${API_URL}/diagnostic/user/${userId}/module/${moduleId}/reset`,
      );
      navigate(`/module/${moduleId}/diagnostic`);
    } catch (err) {
      console.error("Error reseteando diagnóstico:", err);
    }
  }

  async function handleLevelChange(level) {
    if (!canAccessLevel(level)) return;
    setActiveLevel(level);
    setSelectedChallenge(null);
    await loadChallenges(moduleInfo?.name, level);
  }

  function canAccessLevel(level) {
    const currentIndex = LEVELS.indexOf(progress?.current_level || "beginner");
    const targetIndex = LEVELS.indexOf(level);
    return targetIndex <= currentIndex;
  }

  function getChallengeStatus(challengeId) {
    if (completedIds.includes(challengeId)) return "completed";
    if (failedIds.includes(challengeId)) return "failed";
    return "available";
  }

  function getCompletedCount() {
    return challenges.filter((c) => completedIds.includes(c.id)).length;
  }

  function handleStartChallenge(challenge) {
    if (challenge.type === "simple") {
      navigate(`/challenge/simple/${challenge.id}`, {
        state: { userId, challenge, moduleId: parseInt(moduleId) },
      });
    } else {
      navigate(`/challenge/conversational/${challenge.id}`, {
        state: { userId, challenge, moduleId: parseInt(moduleId) },
      });
    }
  }

  const isEmpathy = moduleInfo?.name === "empathy";
  const completedCount = getCompletedCount();
  const progressPct = Math.min(Math.round((completedCount / 5) * 100), 100);

  if (loading) {
    return (
      <div className="mod-loading">
        <div className="mod-loading-spinner"></div>
        <p>Cargando módulo...</p>
      </div>
    );
  }

  return (
    <div className="mod-wrap">
      {/* Navbar */}
      <nav className="mod-navbar">
        <button className="mod-back-btn" onClick={() => navigate("/dashboard")}>
          <FiArrowLeft size={16} />
          Volver
        </button>
        <div className="mod-avatar">
          {user?.name
            ?.split(" ")
            .map((n) => n[0])
            .join("")
            .slice(0, 2)
            .toUpperCase()}
        </div>
      </nav>

      <div className="mod-content">
        {/* Header del módulo */}
        <div className="mod-header">
          <div className={`mod-icon ${isEmpathy ? "icon-blue" : "icon-cyan"}`}>
            {isEmpathy ? (
              <FiMessageCircle size={26} color="#2563EB" />
            ) : (
              <FiUsers size={26} color="#0EA5E9" />
            )}
          </div>
          <div>
            <h1 className="mod-title">
              {isEmpathy ? "Comunicación Empática" : "Networking Profesional"}
            </h1>
            <p className="mod-desc">
              {isEmpathy
                ? "Practica responder con empatía en situaciones reales"
                : "Practica interacciones profesionales escritas"}
            </p>
          </div>
        </div>
        <button
          className="mod-guide-btn"
          onClick={() => navigate(`/module/${moduleId}/guide`)}
        >
          <FiBookOpen size={14} />
          Ver guía de aprendizaje
        </button>

        <button
  className="mod-reset-btn"
  onClick={() => setShowResetModal(true)}
>
  <FiRefreshCw size={14} />
  Repetir diagnóstico
</button>
        {/* Tabs de nivel */}
        <div className="mod-level-tabs">
          {LEVELS.map((level) => {
            const accessible = canAccessLevel(level);
            const isActive = activeLevel === level;
            return (
              <button
                key={level}
                className={`mod-tab ${isActive ? "tab-active" : ""} ${!accessible ? "tab-locked" : ""}`}
                onClick={() => handleLevelChange(level)}
                disabled={!accessible}
              >
                {!accessible && <FiLock size={10} style={{ marginRight: 4 }} />}
                {LEVEL_LABELS[level]}
              </button>
            );
          })}
        </div>

        {/* Barra de progreso */}
        <div className="mod-progress-section">
          <div className="mod-progress-header">
            <span className="mod-progress-label">
              Progreso nivel {LEVEL_LABELS[activeLevel].toLowerCase()}
            </span>
            <span
              className={`mod-progress-count ${isEmpathy ? "count-blue" : "count-cyan"}`}
            >
              {completedCount} / 5 retos
            </span>
          </div>
          <div className="mod-progress-bar-wrap">
            <div
              className={`mod-progress-bar-fill ${isEmpathy ? "fill-blue" : "fill-cyan"}`}
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <p className="mod-progress-hint">
            Completa 4 de 5 retos para desbloquear el siguiente nivel
          </p>
        </div>

        {/* Personajes */}
        <p className="mod-section-title">Personajes del nivel</p>
        <div className="mod-characters-grid">
          {challenges.map((challenge, index) => {
            const status = getChallengeStatus(challenge.id);
            const color = AVATAR_COLORS[index % AVATAR_COLORS.length];
            const initials = getInitials(challenge.agent_profile);

            return (
              <div
                key={challenge.id}
                className={`mod-char-card ${status}`}
                onClick={() =>
                  status !== "locked" && setSelectedChallenge(challenge)
                }
              >
                <div className="mod-char-avatar-wrap">
                  <div
                    className="mod-char-avatar"
                    style={{ background: color }}
                  >
                    {initials}
                  </div>
                  <div className={`mod-status-badge badge-${status}`}>
                    {status === "completed" && (
                      <svg
                        width="10"
                        height="10"
                        viewBox="0 0 10 10"
                        fill="none"
                      >
                        <path
                          d="M2 5l2.5 2.5 3.5-4"
                          stroke="white"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    )}
                    {status === "failed" && (
                      <svg
                        width="10"
                        height="10"
                        viewBox="0 0 10 10"
                        fill="none"
                      >
                        <path
                          d="M3 3l4 4M7 3l-4 4"
                          stroke="white"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                        />
                      </svg>
                    )}
                    {status === "available" && (
                      <div
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          background: "white",
                        }}
                      />
                    )}
                  </div>
                </div>
                <p className="mod-char-name">
                  {getShortName(challenge.agent_profile)}
                </p>
                <span
                  className={`mod-char-type ${challenge.type === "simple" ? "type-simple" : "type-conv"}`}
                >
                  {challenge.type === "simple" ? "Simple" : "Conversacional"}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Panel de detalle */}
      {selectedChallenge && (
        <div
          className="mod-detail-overlay"
          onClick={() => setSelectedChallenge(null)}
        >
          <div
            className="mod-detail-panel"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mod-detail-handle" />
            <button
              className="mod-detail-close"
              onClick={() => setSelectedChallenge(null)}
            >
              ✕
            </button>

            <div className="mod-detail-top">
              <div
                className="mod-detail-avatar"
                style={{
                  background:
                    AVATAR_COLORS[
                      challenges.indexOf(selectedChallenge) %
                        AVATAR_COLORS.length
                    ],
                }}
              >
                {getInitials(selectedChallenge.agent_profile)}
              </div>
              <div>
                <p className="mod-detail-name">
                  {selectedChallenge.agent_profile
                    .split(" ")
                    .slice(0, 3)
                    .join(" ")}
                </p>
                <p className="mod-detail-role">
                  {selectedChallenge.agent_profile}
                </p>
              </div>
            </div>

            <hr className="mod-detail-divider" />

            <p className="mod-detail-label">Contexto del reto</p>
            <p className="mod-detail-context">{selectedChallenge.context}</p>

            <p className="mod-detail-label">Mensaje inicial</p>
            <div className="mod-detail-message">
              "{selectedChallenge.opening_message}"
            </div>

            {getChallengeStatus(selectedChallenge.id) === "completed" ? (
  <button
    className="mod-detail-btn btn-review"
    onClick={() => {
      const convId = challengeConvMap[selectedChallenge.id];
      if (convId) {
        navigate(`/feedback/${convId}`, {
          state: {
            challenge: selectedChallenge,
            moduleId: parseInt(moduleId),
            userId,
            readOnly: true,
          },
        });
      }
    }}
  >
    Ver retroalimentación
  </button>
            ) : getChallengeStatus(selectedChallenge.id) === "failed" ? (
              <button
                className="mod-detail-btn btn-retry"
                onClick={() => handleStartChallenge(selectedChallenge)}
              >
                Reintentar reto
              </button>
            ) : (
              <button
                className="mod-detail-btn btn-start"
                onClick={() => handleStartChallenge(selectedChallenge)}
              >
                Iniciar reto
              </button>
            )}
          </div>
        </div>
      )}
      {showResetModal && (
  <div className="modal-overlay" onClick={() => setShowResetModal(false)}>
    <div className="modal-card" onClick={(e) => e.stopPropagation()}>
      <div className="modal-icon modal-icon-warning">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 4L3 19h18L12 4z" stroke="#F59E0B" strokeWidth="1.5" strokeLinejoin="round"/>
          <path d="M12 10v4M12 16.5v.5" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      </div>
      <h3 className="modal-title">¿Repetir diagnóstico?</h3>
      <p className="modal-desc">
        Si repites el diagnóstico, tu nivel actual y todos tus retos
        se reiniciarán. Tu historial de retroalimentaciones se conservará.
        Esta acción no se puede deshacer.
      </p>
      <button
        className="modal-btn-warning"
        onClick={() => {
          setShowResetModal(false);
          handleResetDiagnostic();
        }}
      >
        Sí, repetir diagnóstico
      </button>
      <button
        className="modal-btn-cancel"
        onClick={() => setShowResetModal(false)}
      >
        Cancelar
      </button>
    </div>
  </div>
)}
    </div>
  );
}

export default Module;
