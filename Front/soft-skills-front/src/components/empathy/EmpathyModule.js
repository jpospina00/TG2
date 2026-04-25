// EmpathyModule.js
// Propósito: Módulo de empatía — lista de situaciones sin personajes
// Dependencias: react, react-router-dom, axios, @auth0/auth0-react
// Fecha: 2026-04-16

import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import { FiArrowLeft, FiRefreshCw, FiBookOpen, FiLock } from "react-icons/fi";
import "./EmpathyModule.css";

const API_URL = process.env.REACT_APP_API_URL;
const LEVELS = ["beginner", "intermediate", "advanced"];
const LEVEL_LABELS = { beginner: "Inicial", intermediate: "Intermedio", advanced: "Avanzado" };

function EmpathyModule() {
  const { moduleId } = useParams();
  const { user } = useAuth0();
  const navigate = useNavigate();

  const [challenges, setChallenges] = useState([]);
  const [progress, setProgress] = useState(null);
  const [userId, setUserId] = useState(null);
  const [activeLevel, setActiveLevel] = useState("beginner");
  const [completedIds, setCompletedIds] = useState([]);
  const [failedIds, setFailedIds] = useState([]);
  const [challengeConvMap, setChallengeConvMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [showResetModal, setShowResetModal] = useState(false);
  const [selectedChallenge, setSelectedChallenge] = useState(null);

  useEffect(() => {
    if (user) loadModule();
  }, [user, moduleId]);

  async function loadModule() {
    try {
      const userRes = await axios.get(`${API_URL}/users/auth0/${user.sub}`);
      const dbUser = userRes.data;
      setUserId(dbUser.id);

      const diagRes = await axios.get(
        `${API_URL}/diagnostic/user/${dbUser.id}/module/${moduleId}`
      );
      if (!diagRes.data.has_diagnostic) {
        navigate(`/module/${moduleId}/diagnostic`);
        return;
      }

      const progRes = await axios.get(`${API_URL}/progress/user/${dbUser.id}`);
      const modProgress = progRes.data.find(
        (p) => p.module_id === parseInt(moduleId)
      );
      setProgress(modProgress);
      const level = modProgress?.current_level || "beginner";
      setActiveLevel(level);

      await loadChallenges(moduleId, level, dbUser.id);

      const convRes = await axios.get(`${API_URL}/conversations/user/${dbUser.id}`);
      const completed = [];
      const failed = [];
      const convMap = {};
      for (const conv of convRes.data) {
        try {
          const fbRes = await axios.get(`${API_URL}/feedback/conversation/${conv.id}`);
          if (fbRes.data.completed) {
            completed.push(conv.challenge_id);
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
      console.error("Error cargando módulo de empatía:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadChallenges(modId, level, uid) {
    try {
      const res = await axios.get(
        `${API_URL}/challenges/module/${modId}/level/${level}`,
        { params: { user_id: uid } }
      );
      setChallenges(res.data);
    } catch (err) {
      console.error("Error cargando situaciones:", err);
    }
  }

  async function handleLevelChange(level) {
    if (!canAccessLevel(level)) return;
    setActiveLevel(level);
    setSelectedChallenge(null);
    await loadChallenges(moduleId, level, userId);
  }

  async function handleResetDiagnostic() {
    try {
      await axios.delete(
        `${API_URL}/diagnostic/user/${userId}/module/${moduleId}/reset`
      );
      navigate(`/module/${moduleId}/diagnostic`);
    } catch (err) {
      console.error("Error reseteando diagnóstico:", err);
    }
  }

  function canAccessLevel(level) {
    const currentIndex = LEVELS.indexOf(progress?.current_level || "beginner");
    return LEVELS.indexOf(level) <= currentIndex;
  }

  function getChallengeStatus(id) {
    if (completedIds.includes(id)) return "completed";
    if (failedIds.includes(id)) return "failed";
    return "available";
  }

  function getCompletedCount() {
    return challenges.filter((c) => completedIds.includes(c.id)).length;
  }

  function handleStartChallenge(challenge) {
    navigate(`/empathy/challenge/${challenge.id}`, {
      state: { userId, challenge, moduleId: parseInt(moduleId) },
    });
  }

  const completedCount = getCompletedCount();
  const progressPct = Math.min(Math.round((completedCount / 5) * 100), 100);

  if (loading) {
    return (
      <div className="em-loading">
        <div className="em-spinner"></div>
        <p>Cargando laboratorio...</p>
      </div>
    );
  }

  return (
    <div className="em-wrap">
      <nav className="em-nav">
        <button className="em-back" onClick={() => navigate("/dashboard")}>
          <FiArrowLeft size={15} /> Volver
        </button>
        <div className="em-nav-avatar">
          {user?.name?.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
        </div>
      </nav>

      <div className="em-content">
        <div className="em-header">
          <div className="em-header-icon">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <path d="M11 4C7.686 4 5 6.686 5 10c0 2.5 1.4 4.7 3.5 5.85L9 19h4l.5-3.15C15.6 14.7 17 12.5 17 10c0-3.314-2.686-6-6-6z" stroke="#085041" strokeWidth="1.2" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <h1 className="em-title">Laboratorio de empatía</h1>
            <p className="em-desc">Analiza situaciones reales y practica la comunicación empática</p>
          </div>
        </div>

        <div className="em-actions-row">
          <button className="em-guide-btn" onClick={() => navigate(`/module/${moduleId}/guide`)}>
            <FiBookOpen size={13} /> Guía de aprendizaje
          </button>
          <button className="em-reset-btn" onClick={() => setShowResetModal(true)}>
            <FiRefreshCw size={13} /> Repetir diagnóstico
          </button>
        </div>

        <div className="em-level-tabs">
          {LEVELS.map((level) => {
            const accessible = canAccessLevel(level);
            return (
              <button
                key={level}
                className={`em-tab ${activeLevel === level ? "em-tab-active" : ""} ${!accessible ? "em-tab-locked" : ""}`}
                onClick={() => handleLevelChange(level)}
                disabled={!accessible}
              >
                {!accessible && <FiLock size={9} style={{ marginRight: 4 }} />}
                {LEVEL_LABELS[level]}
              </button>
            );
          })}
        </div>

        <div className="em-progress-section">
          <div className="em-progress-header">
            <span className="em-progress-label">Progreso nivel {LEVEL_LABELS[activeLevel].toLowerCase()}</span>
            <span className="em-progress-count">{completedCount} / 5 situaciones</span>
          </div>
          <div className="em-progress-bar">
            <div className="em-progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
          <p className="em-progress-hint">Completa 4 de 5 situaciones para desbloquear el siguiente nivel</p>
        </div>

        <p className="em-section-title">Situaciones del nivel</p>

        <div className="em-situations-list">
          {challenges.map((challenge) => {
            const status = getChallengeStatus(challenge.id);
            const isMultiple = challenge.type === "multiple_choice";
            return (
              <div
                key={challenge.id}
                className={`em-situation-card ${status}`}
                onClick={() => setSelectedChallenge(challenge)}
              >
                <div className="em-situation-left">
                  <div className={`em-type-badge ${isMultiple ? "badge-multiple" : "badge-analysis"}`}>
                    {isMultiple ? "Selección múltiple" : "Análisis"}
                  </div>
                  <p className="em-situation-context">{challenge.context}</p>
                  <p className="em-situation-preview">"{challenge.opening_message.slice(0, 80)}..."</p>
                </div>
                <div className="em-situation-right">
                  <div className={`em-status-dot dot-${status}`} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Panel de detalle */}
      {selectedChallenge && (
        <div className="em-overlay" onClick={() => setSelectedChallenge(null)}>
          <div className="em-detail-card" onClick={(e) => e.stopPropagation()}>
            <div className="em-detail-handle" />
            <button className="em-detail-close" onClick={() => setSelectedChallenge(null)}>✕</button>

            <div className={`em-detail-tag ${selectedChallenge.type === "multiple_choice" ? "tag-multiple" : "tag-analysis"}`}>
              {selectedChallenge.type === "multiple_choice" ? "Selección múltiple" : "Análisis de situación"}
            </div>

            <div className="em-detail-quote">
              <div className="em-detail-quote-bar" />
              <p className="em-detail-quote-text">"{selectedChallenge.opening_message}"</p>
            </div>

            <p className="em-detail-ctx-label">Contexto</p>
            <p className="em-detail-ctx">{selectedChallenge.context}</p>

            {selectedChallenge.type === "multiple_choice" && (
              <div className="em-detail-meta">
                <div className="em-meta-pill">4 opciones</div>
                <div className="em-meta-pill">1 intento</div>
              </div>
            )}

            {selectedChallenge.type === "analysis" && (
              <div className="em-detail-meta">
                <div className="em-meta-pill">2 pasos</div>
              </div>
            )}

            <div className="em-detail-divider" />

            {getChallengeStatus(selectedChallenge.id) === "completed" ? (
              <button
                className="em-detail-btn btn-review"
                onClick={() => navigate(`/empathy/feedback/${challengeConvMap[selectedChallenge.id]}`, {
                  state: {
                    challenge: selectedChallenge,
                    moduleId: parseInt(moduleId),
                    userId,
                    readOnly: true,
                  }
                })}
              >
                Ver retroalimentación
              </button>
            ) : (
              <button
                className="em-detail-btn btn-start"
                onClick={() => handleStartChallenge(selectedChallenge)}
              >
                Iniciar situación
              </button>
            )}
            <button className="em-detail-btn btn-cancel" onClick={() => setSelectedChallenge(null)}>
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Modal reset diagnóstico */}
      {showResetModal && (
        <div className="em-overlay" onClick={() => setShowResetModal(false)}>
          <div className="em-detail-card" onClick={(e) => e.stopPropagation()}>
            <div className="em-detail-handle" />
            <div className="em-modal-icon em-modal-icon-warn">
              <FiRefreshCw size={20} color="#633806" />
            </div>
            <h3 className="em-modal-title">¿Repetir el diagnóstico?</h3>
            <p className="em-modal-desc">Tu nivel actual y todas las situaciones se reiniciarán. Tu historial de retroalimentaciones se conservará. Esta acción no se puede deshacer.</p>
            <button className="em-detail-btn btn-danger" onClick={() => { setShowResetModal(false); handleResetDiagnostic(); }}>
              Sí, repetir diagnóstico
            </button>
            <button className="em-detail-btn btn-cancel" onClick={() => setShowResetModal(false)}>
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default EmpathyModule;