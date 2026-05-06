// SimpleChallenge.js
// Propósito: Pantalla de reto simple — el estudiante responde una vez y recibe evaluación
// Dependencias: react, react-router-dom, axios, react-icons
// Fecha: 2026-03-20

import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import { FiArrowLeft, FiSend } from "react-icons/fi";
import ErrorMessage from "../shared/ErrorMessage";
import { useSlowRequest } from "../../hooks/useSlowRequest";
import SlowRequestBanner from "../shared/SlowRequestBanner";
import "./Challenge.css";

const API_URL = process.env.REACT_APP_API_URL;

function SimpleChallenge() {
  const { challengeId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();
  const chatEndRef = useRef(null);

  const { userId, challenge, moduleId } = state || {};

  const [response, setResponse] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluated, setEvaluated] = useState(false);
  const [showExitModal, setShowExitModal] = useState(false);
  const [error, setError] = useState(null);
  const { isSlow, start, stop } = useSlowRequest(2000);

  const MAX_CHARS = 500;

  useEffect(() => {
    if (challenge) {
      initConversation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  async function initConversation() {
    try {
      const convRes = await axios.post(`${API_URL}/conversations`, {
        user_id: userId,
        challenge_id: challenge.id,
      });
      setConversationId(convRes.data.id);

      axios.post(`${API_URL}/messages`, {
        conversation_id: convRes.data.id,
        role: "agent",
        content: challenge.opening_message,
        order: 1,
      });

      setMessages([{ role: "agent", content: challenge.opening_message }]);
    } catch (err) {
      console.error("Error iniciando conversación:", err);
    }
  }

  async function handleSubmit() {
    if (!response.trim() || isEvaluating || evaluated) return;

    const studentResponse = response.trim();
    setResponse("");
    setIsEvaluating(true);
    start();
    setError(null);

    setMessages((prev) => [...prev, { role: "user", content: studentResponse }]);

    try {
      const evalRes = await axios.post(`${API_URL}/ai/simple/evaluate`, {
        conversation_id: conversationId,
        student_response: studentResponse,
      });
      stop();
      // Si hubo level_up, obtener el nivel actualizado desde la API
      let newLevel = null;
      if (evalRes.data.level_up) {
        try {
          const progressRes = await axios.get(`${API_URL}/progress/user/${userId}`);
          const modProgress = progressRes.data.find((p) => p.module_id === moduleId);
          newLevel = modProgress?.current_level || null;
        } catch {
          stop();
        }
      }

      navigate(`/feedback/${conversationId}`, {
        state: {
          feedback: evalRes.data.feedback,
          completed: evalRes.data.completed,
          levelUp: evalRes.data.level_up,
          newLevel,
          moduleName: moduleId === 1 ? "empathy" : "networking",
          challenge,
          moduleId,
          userId,
        },
      });
    } catch (err) {
      console.error("Error evaluando:", err);
      setError("No se pudo evaluar tu respuesta. Verifica tu conexión e intenta de nuevo.");
      setIsEvaluating(false);
    }
  }

  const isEmpathy = moduleId === 1;
  const charColor = response.length > 450 ? "#EF4444" : "#60A5FA";

  if (!challenge) {
    return (
      <div className="ch-loading">
        <p>Cargando reto...</p>
      </div>
    );
  }

  return (
    <div className="ch-wrap">
      {/* Navbar */}
      <nav className="ch-navbar">
        <button className="ch-back-btn" onClick={() => setShowExitModal(true)}>
          <FiArrowLeft size={16} />
          Salir
        </button>
        <div className="ch-navbar-center">
          <span className="ch-navbar-title">Reto simple</span>
          <span className="ch-navbar-sub">
            {isEmpathy ? "Empatía" : "Networking"} · {
    challenge?.level === "beginner" ? "Nivel inicial" :
    challenge?.level === "intermediate" ? "Nivel intermedio" : "Nivel avanzado"
  }
          </span>
        </div>
        <span className="ch-navbar-badge ch-badge-blue">Simple</span>
      </nav>

      {/* Header del agente */}
      <div className="ch-agent-header">
        <div className="ch-agent-avatar-wrap">
          <div
            className="ch-agent-avatar"
            style={{ background: "linear-gradient(135deg, #10B981, #0EA5E9)" }}
          >
            {challenge.name?.slice(0, 2).toUpperCase() || challenge.agent_profile.slice(0, 2).toUpperCase()}
          </div>
          <div className="ch-agent-online" />
        </div>
        <p className="ch-agent-name">
          {challenge.name || challenge.agent_profile.split(" ").slice(0, 2).join(" ")}
        </p>
        <p className="ch-agent-role">{challenge.agent_profile}</p>
        <p className="ch-context-pill">{challenge.context}</p>
      </div>

      {/* Chat */}
      <div className="ch-chat-area">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`ch-msg-wrap ${msg.role === "user" ? "msg-user" : "msg-agent"}`}
          >
            {msg.role === "agent" && (
              <div
                className="ch-msg-mini-avatar"
                style={{ background: "linear-gradient(135deg, #10B981, #0EA5E9)" }}
              >
                {challenge.name?.slice(0, 2).toUpperCase() || challenge.agent_profile.slice(0, 2).toUpperCase()}
              </div>
            )}
            <div>
              <div className={`ch-bubble ${msg.role === "user" ? "bubble-user" : "bubble-agent"}`}>
                {msg.content}
              </div>
              <p className={`ch-msg-time ${msg.role === "user" ? "time-right" : ""}`}>
                Ahora
              </p>
            </div>
          </div>
        ))}

        {isEvaluating && (
  <div className="ch-msg-wrap msg-agent">
    <div className="bubble-agent ch-evaluating">
      Evaluando tu respuesta...
    </div>
    {isSlow && <SlowRequestBanner message="La IA está analizando tu respuesta..." />}
  </div>
)}

        {error && (
          <ErrorMessage
            title="Error al evaluar"
            message={error}
            onRetry={() => setError(null)}
          />
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="ch-input-area">
        <div className="ch-char-counter">
          <span style={{ color: charColor }}>{response.length}</span> / {MAX_CHARS}
        </div>
        <textarea
          className="ch-input"
          placeholder={isEmpathy ? "Escribe tu respuesta empática aquí..." : "Escribe tu mensaje de networking aquí..."}
          maxLength={MAX_CHARS}
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          disabled={isEvaluating || evaluated}
        />
        <div className="ch-input-actions">
          <span className="ch-tip">Responde con empatía y comprensión</span>
          <button
            className="ch-send-btn"
            onClick={handleSubmit}
            disabled={!response.trim() || isEvaluating || evaluated}
          >
            Enviar
            <FiSend size={14} />
          </button>
        </div>
      </div>

      {/* Modal salir */}
      {showExitModal && (
        <div className="modal-overlay" onClick={() => setShowExitModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon modal-icon-warning">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 4L3 19h18L12 4z"
                  stroke="#F59E0B"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
                <path
                  d="M12 10v4M12 16.5v.5"
                  stroke="#F59E0B"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <h3 className="modal-title">¿Salir del reto?</h3>
            <p className="modal-desc">
              Si sales ahora perderás tu progreso en este reto.
            </p>
            <button
              className="modal-btn-warning"
              onClick={() => navigate(`/module/${moduleId}`)}
            >
              Sí, salir
            </button>
            <button
              className="modal-btn-cancel"
              onClick={() => setShowExitModal(false)}
            >
              Continuar el reto
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default SimpleChallenge;