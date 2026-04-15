// Feedback.js
// Propósito: Pantalla de retroalimentación después de completar un reto
// Dependencias: react, react-router-dom, react-icons
// Fecha: 2026-03-20

import React, { useState, useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import { FiCheckCircle, FiXCircle } from "react-icons/fi";
import "./Feedback.css";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL;

function Feedback() {
  // eslint-disable-next-line no-unused-vars
  const { conversationId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();

  const [feedbackData, setFeedbackData] = useState(null);
const [loading, setLoading] = useState(false);

const { feedback: feedbackFromState, completed: completedFromState, levelUp, newLevel, moduleName, challenge, moduleId, userId, readOnly } = state || {};

  useEffect(() => {
  if (readOnly && conversationId) {
    setLoading(true);
    axios.get(`${API_URL}/feedback/conversation/${conversationId}`)
      .then(res => {
        setFeedbackData(res.data);
      })
      .catch(err => console.error("Error cargando feedback:", err))
      .finally(() => setLoading(false));
  }
}, [readOnly, conversationId]);
const feedback = readOnly ? feedbackData?.content : feedbackFromState;
const completed = readOnly ? feedbackData?.completed : completedFromState;

  if (loading) {
  return (
    <div className="fb-loading">
      <p>Cargando retroalimentación...</p>
    </div>
  );
}

if (!feedback) {
  return (
    <div className="fb-loading">
      <p>Cargando retroalimentación...</p>
    </div>
  );
}



  function parseCriteria() {
    const criteriaNames = [
      { key: "emocional", label: "Reconocimiento emocional" },
      { key: "empático", label: "Lenguaje empático" },
      { key: "claridad", label: "Claridad" },
      { key: "coherencia", label: "Coherencia contextual" },
      { key: "objetivo", label: "Objetivo comunicativo" },
      { key: "estructura", label: "Estructura del mensaje" },
      { key: "formalidad", label: "Nivel de formalidad" },
      { key: "adecuación", label: "Adecuación al contexto" },
    ];

    return criteriaNames
      .filter((c) => feedback.toLowerCase().includes(c.key))
      .slice(0, 4)
      .map((c) => ({ name: c.label, pass: completed }));
  }

  const criteria = parseCriteria();

  function handleNext() {
    if (levelUp && newLevel) {
      navigate("/levelup", {
        state: { newLevel, moduleId, moduleName, userId },
      });
    } else {
      navigate(`/module/${moduleId}`);
    }
  }

  return (
    <div className="fb-wrap">
      {/* Navbar */}
      <nav className="fb-navbar">
        <button
          className="fb-back-btn"
          onClick={() => navigate(`/module/${moduleId}`)}
        >
          Volver al módulo
        </button>
        <span className="fb-navbar-title">Retroalimentación</span>
        <div style={{ width: 80 }} />
      </nav>

      <div className="fb-content">
        {/* Banner resultado */}
        <div className={`fb-result-banner ${completed ? "banner-ok" : "banner-fail"}`}>
          <div className={`fb-result-icon ${completed ? "icon-ok" : "icon-fail"}`}>
            {completed
              ? <FiCheckCircle size={28} color="#10B981" />
              : <FiXCircle size={28} color="#EF4444" />
            }
          </div>
          <p className={`fb-result-title ${completed ? "title-ok" : "title-fail"}`}>
            {completed ? "¡Reto superado!" : "Sigue practicando"}
          </p>
          <p className="fb-result-sub">
            {completed
              ? "Tu respuesta demostró buenas habilidades comunicativas"
              : "Tu respuesta no cumplió con los criterios mínimos"}
          </p>
          {levelUp && !readOnly && (
            <div className="fb-levelup-badge">¡Subiste de nivel!</div>
          )}
        </div>

        {/* Info del reto */}
        <div className="fb-challenge-row">
          <div
            className="fb-challenge-avatar"
            style={{ background: "linear-gradient(135deg, #10B981, #0EA5E9)" }}
          >
            {challenge?.agent_profile?.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <p className="fb-challenge-name">
              {challenge?.agent_profile?.split(" ").slice(0, 3).join(" ")}
            </p>
            <p className="fb-challenge-role">{challenge?.agent_profile}</p>
          </div>
          <span className="fb-type-badge">
            {challenge?.type === "simple" ? "Simple" : "Conversacional"}
          </span>
        </div>

        {/* Criterios */}
        {criteria.length > 0 && (
          <>
            <p className="fb-section-title">Evaluación por criterios</p>
            <div className="fb-criteria-grid">
              {criteria.map((c, i) => (
                <div key={i} className={`fb-criteria-card ${c.pass ? "crit-pass" : "crit-fail"}`}>
                  <div className="fb-criteria-top">
                    <span className="fb-criteria-name">{c.name}</span>
                    <div className={`fb-criteria-dot ${c.pass ? "dot-ok" : "dot-fail"}`} />
                  </div>
                  <p className="fb-criteria-desc">
                    {c.pass ? "Cumplido satisfactoriamente" : "Necesita mejora"}
                  </p>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Feedback completo */}
        <p className="fb-section-title">Comentarios de la IA</p>
        <div className="fb-feedback-box">
          <p className="fb-feedback-text">{feedback}</p>
        </div>

        {/* Acciones — solo se muestran si NO es modo readOnly */}
        {!readOnly && (
          <div className="fb-actions">
            {completed ? (
              <button className="fb-btn-primary" onClick={handleNext}>
                {levelUp ? "¡Ver mi nuevo nivel!" : "Siguiente reto"}
              </button>
            ) : (
              <button
                className="fb-btn-retry"
                onClick={() =>
                  navigate(
                    challenge?.type === "simple"
                      ? `/challenge/simple/${challenge.id}`
                      : `/challenge/conversational/${challenge.id}`,
                    { state: { userId, challenge, moduleId } }
                  )
                }
              >
                Reintentar reto
              </button>
            )}
            <button
              className="fb-btn-secondary"
              onClick={() => navigate(`/module/${moduleId}`)}
            >
              Ver módulo
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Feedback;