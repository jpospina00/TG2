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

// ── Sistema de personas para los personajes de retos ──────────────────────────

// Banco de nombres según género/rol detectado del agent_profile
const NAMES_MALE = [
  "Carlos Medina", "Andrés Torres", "Felipe Ruiz", "Sebastián Mora",
  "Julián Castro", "Diego Herrera", "Mateo Vargas", "Camilo Ríos",
  "Santiago López", "Nicolás Peña",
];
const NAMES_FEMALE = [
  "Laura Gómez", "Valentina Cruz", "Daniela Reyes", "Isabela Muñoz",
  "Mariana Ortiz", "Sofía Jiménez", "Natalia Soto", "Paula Ramírez",
  "Alejandra Gil", "Catalina Vega",
];
const NAMES_NEUTRAL = [
  "Alex Moreno", "Sam Guerrero", "Jordan Parra", "Morgan Salcedo",
  "Riley Ospina", "Casey Mendoza",
];

// Mapeo rol → etiqueta legible
const ROLE_LABELS = {
  reclutador: "Reclutador/a", reclutadora: "Reclutadora",
  gerente: "Gerente", director: "Director/a", directora: "Directora",
  profesor: "Profesor/a", profesora: "Profesora",
  mentor: "Mentor/a", mentora: "Mentora",
  inversor: "Inversor/a", inversora: "Inversora",
  colega: "Colega", compañero: "Compañero/a", compañera: "Compañera",
  cliente: "Cliente", jefe: "Jefe/a", estudiante: "Estudiante",
  coordinador: "Coordinador/a", líder: "Líder de equipo",
};

// Hash simple y determinístico para un string
function hashStr(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

// Detecta si el perfil menciona género femenino
function detectGender(profile) {
  const lower = profile.toLowerCase();
  const femaleKws = ["reclutadora", "profesora", "directora", "mentora",
                     "inversora", "compañera", "coordinadora", "jefa",
                     "gerenta", "lideresa", "amiga"];
  const maleKws  = ["reclutador", "profesor", "director", "mentor",
                    "inversor", "compañero", "coordinador", "jefe",
                    "gerente", "líder", "amigo", "colega"];
  if (femaleKws.some(k => lower.includes(k))) return "female";
  if (maleKws.some(k => lower.includes(k))) return "male";
  return "neutral";
}

// Detecta el rol principal del perfil para mostrarlo como subtítulo
function detectRoleLabel(profile) {
  const lower = profile.toLowerCase();
  for (const [kw, label] of Object.entries(ROLE_LABELS)) {
    if (lower.includes(kw)) return label;
  }
  // Fallback: primeras 3 palabras del perfil
  return profile.split(" ").slice(0, 3).join(" ");
}

// Devuelve { name, roleLabel, avatarUrl } determinístico para un agent_profile
function resolvePersona(agentProfile) {
  const h = hashStr(agentProfile);
  const gender = detectGender(agentProfile);

  let pool;
  if (gender === "female") pool = NAMES_FEMALE;
  else if (gender === "male") pool = NAMES_MALE;
  else pool = NAMES_NEUTRAL;

  const name = pool[h % pool.length];
  const roleLabel = detectRoleLabel(agentProfile);

  // DiceBear avataaars — seed determinístico, sin dependencia de paquete npm
  const seed = encodeURIComponent(name);
  const avatarUrl = `https://api.dicebear.com/9.x/avataaars/svg?seed=${seed}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf&radius=50`;

  return { name, roleLabel, avatarUrl };
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

const feedbackResults = await Promise.all(
  conversations.map(conv =>
    axios.get(`${API_URL}/feedback/conversation/${conv.id}`).catch(() => null)
  )
);

const completed = [];
const failed = [];
const convMap = {};

feedbackResults.forEach((fbRes, i) => {
  if (!fbRes) return;
  const conv = conversations[i];
  if (fbRes.data.completed) {
    completed.push(conv.challenge_id);
    convMap[conv.challenge_id] = conv.id;
  } else {
    failed.push(conv.challenge_id);
  }
});

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
            const persona = resolvePersona(challenge.agent_profile);
            const firstName = persona.name.split(" ")[0];

            return (
              <div
                key={challenge.id}
                className={`mod-char-card ${status}`}
                onClick={() =>
                  status !== "locked" && setSelectedChallenge(challenge)
                }
              >
                <div className="mod-char-avatar-wrap">
                  <img
                    className="mod-char-avatar mod-char-avatar-img"
                    src={persona.avatarUrl}
                    alt={persona.name}
                    onError={(e) => {
                      // Fallback: círculo con inicial si DiceBear falla
                      e.target.style.display = "none";
                      e.target.nextSibling.style.display = "flex";
                    }}
                  />
                  <div
                    className="mod-char-avatar mod-char-avatar-fallback"
                    style={{ display: "none", background: "linear-gradient(135deg,#2563eb,#0ea5e9)" }}
                  >
                    {persona.name[0]}
                  </div>
                  <div className={`mod-status-badge badge-${status}`}>
                    {status === "completed" && (
                      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                        <path d="M2 5l2.5 2.5 3.5-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                    {status === "failed" && (
                      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                        <path d="M3 3l4 4M7 3l-4 4" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                    )}
                    {status === "available" && (
                      <div style={{ width: 6, height: 6, borderRadius: "50%", background: "white" }} />
                    )}
                  </div>
                </div>
                <p className="mod-char-name">{firstName}</p>
                <p className="mod-char-role">{persona.roleLabel}</p>
                <span className={`mod-char-type ${challenge.type === "simple" ? "type-simple" : "type-conv"}`}>
                  {challenge.type === "simple" ? "Simple" : "Conversacional"}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Panel de detalle */}
      {selectedChallenge && (() => {
        const persona = resolvePersona(selectedChallenge.agent_profile);
        return (
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
              <img
                className="mod-detail-avatar mod-detail-avatar-img"
                src={persona.avatarUrl}
                alt={persona.name}
                onError={(e) => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }}
              />
              <div
                className="mod-detail-avatar mod-detail-avatar-fallback"
                style={{ display: "none", background: "linear-gradient(135deg,#2563eb,#0ea5e9)" }}
              >
                {persona.name[0]}
              </div>
              <div>
                <p className="mod-detail-name">
                  {persona.name}
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
        );
      })()}
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