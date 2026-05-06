// ConversationalChallenge.js
// Propósito: Pantalla de reto conversacional — máximo 3 turnos del estudiante
// Dependencias: react, react-router-dom, axios, react-icons
// Fecha: 2026-03-20

import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import { FiArrowLeft, FiSend } from "react-icons/fi";
import ErrorMessage from "../shared/ErrorMessage";
import "./Challenge.css";

const API_URL = process.env.REACT_APP_API_URL;
const MAX_TURNS = 3;
const MAX_CHARS = 500;

function ConversationalChallenge() {
  const { challengeId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();
  const chatEndRef = useRef(null);

  const { userId, challenge, moduleId } = state || {};

  const [response, setResponse] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [turnCount, setTurnCount] = useState(0);
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);
  const [showExitModal, setShowExitModal] = useState(false);
  const [showFinishModal, setShowFinishModal] = useState(false);
  const [inputDisabled, setInputDisabled] = useState(false);
  const [error, setError] = useState(null);

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
  }, [messages, isAgentTyping]);

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

      const initialHistory = [{ role: "agent", content: challenge.opening_message }];
      setMessages(initialHistory);
      setHistory(initialHistory);
    } catch (err) {
      console.error("Error iniciando conversación:", err);
    }
  }

  async function handleSend() {
    if (!response.trim() || isAgentTyping || inputDisabled || turnCount >= MAX_TURNS) return;

    const studentMessage = response.trim();
    setResponse("");
    setError(null);

    const newTurn = turnCount + 1;
    setTurnCount(newTurn);

    const updatedHistory = [...history, { role: "user", content: studentMessage }];
    setHistory(updatedHistory);
    setMessages((prev) => [...prev, { role: "user", content: studentMessage }]);

    axios.post(`${API_URL}/messages`, {
      conversation_id: conversationId,
      role: "user",
      content: studentMessage,
      order: updatedHistory.length,
    });

    if (newTurn >= MAX_TURNS) {
      setInputDisabled(true);
      await finishConversation(updatedHistory);
      return;
    }

    setIsAgentTyping(true);
    try {
      const turnRes = await axios.post(`${API_URL}/ai/conversational/turn`, {
        conversation_id: conversationId,
        student_message: studentMessage,
        history: updatedHistory,
      });

      const agentReply = turnRes.data.agent_reply;
      const newHistory = [...updatedHistory, { role: "agent", content: agentReply }];
      setHistory(newHistory);
      setMessages((prev) => [...prev, { role: "agent", content: agentReply }]);

      axios.post(`${API_URL}/messages`, {
        conversation_id: conversationId,
        role: "agent",
        content: agentReply,
        order: newHistory.length,
      });
    } catch (err) {
      console.error("Error obteniendo respuesta del agente:", err);
      setError("No se pudo obtener la respuesta del agente. Intenta de nuevo.");
    } finally {
      setIsAgentTyping(false);
    }
  }

  async function finishConversation(currentHistory) {
    setIsFinishing(true);
    setInputDisabled(true);
    setShowFinishModal(false);
    setError(null);

    setMessages((prev) => [
      ...prev,
      { role: "system", content: "Conversación cerrada — generando evaluación..." },
    ]);

    try {
      const closeRes = await axios.post(`${API_URL}/ai/conversational/close`, {
        conversation_id: conversationId,
        history: currentHistory || history,
      });

      let newLevel = null;
      if (closeRes.data.level_up) {
        try {
          const progressRes = await axios.get(`${API_URL}/progress/user/${userId}`);
          const modProgress = progressRes.data.find((p) => p.module_id === moduleId);
          newLevel = modProgress?.current_level || null;
        } catch {}
      }

      navigate(`/feedback/${conversationId}`, {
        state: {
          feedback: closeRes.data.feedback,
          completed: closeRes.data.completed,
          levelUp: closeRes.data.level_up,
          newLevel,
          moduleName: moduleId === 1 ? "empathy" : "networking",
          challenge,
          moduleId,
          userId,
        },
      });
    } catch (err) {
      console.error("Error cerrando conversación:", err);
      setError("No se pudo generar la evaluación. Intenta de nuevo.");
      setIsFinishing(false);
      setInputDisabled(false);
    }
  }

  const isEmpathy = moduleId === 1;
  const charColor = response.length > 450 ? "#EF4444" : "#60A5FA";
  const turnsLeft = MAX_TURNS - turnCount;

  const agentInitials = challenge?.name?.slice(0, 2).toUpperCase() ||
    challenge?.agent_profile?.slice(0, 2).toUpperCase();

  const agentShortName = challenge?.name ||
    challenge?.agent_profile?.split(" ").slice(0, 2).join(" ");

  const levelLabel = challenge?.level === "beginner" ? "Nivel inicial" :
    challenge?.level === "intermediate" ? "Nivel intermedio" : "Nivel avanzado";

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
          <span className="ch-navbar-title">Reto conversacional</span>
          <span className="ch-navbar-sub">
            {isEmpathy ? "Empatía" : "Networking"} · {levelLabel}
          </span>
        </div>
        <span className="ch-navbar-badge ch-badge-purple">Conv.</span>
      </nav>

      {/* Header agente con turnos */}
      <div className="ch-agent-bar">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            className="ch-agent-avatar-sm"
            style={{ background: "linear-gradient(135deg, #F59E0B, #EF4444)" }}
          >
            {agentInitials}
          </div>
          <div>
            <p className="ch-agent-name-sm">{agentShortName}</p>
            <p className="ch-agent-role-sm">{challenge.agent_profile}</p>
          </div>
        </div>
        <div className="ch-turns-indicator">
          <span className="ch-turns-label">Tus turnos</span>
          <div className="ch-turns-dots">
            {[1, 2, 3].map((t) => (
              <div
                key={t}
                className={`ch-turn-dot ${
                  t <= turnCount ? "used" : t === turnCount + 1 ? "current" : ""
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Barra de contexto */}
      <div className="ch-context-bar">
        <p className="ch-context-bar-text">{challenge.context}</p>
      </div>

      {/* Chat */}
      <div className="ch-chat-area">
        {messages.map((msg, i) => {
          if (msg.role === "system") {
            return (
              <div key={i} className="ch-system-msg">
                <span>{msg.content}</span>
              </div>
            );
          }
          return (
            <div
              key={i}
              className={`ch-msg-wrap ${msg.role === "user" ? "msg-user" : "msg-agent"}`}
            >
              {msg.role === "agent" && (
                <div
                  className="ch-msg-mini-avatar"
                  style={{ background: "linear-gradient(135deg, #F59E0B, #EF4444)" }}
                >
                  {agentInitials}
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
          );
        })}

        {isAgentTyping && (
          <div className="ch-msg-wrap msg-agent">
            <div
              className="ch-msg-mini-avatar"
              style={{ background: "linear-gradient(135deg, #F59E0B, #EF4444)" }}
            >
              {agentInitials}
            </div>
            <div className="ch-waiting">
              <span>escribiendo</span>
              <div className="ch-dot-anim">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}

        {isFinishing && (
          <div className="ch-system-msg">
            <span>Generando evaluación final...</span>
          </div>
        )}

        {error && (
          <ErrorMessage
            title="Error de conexión"
            message={error}
            onRetry={() => setError(null)}
          />
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="ch-input-area">
        <div className="ch-input-top">
          <div className="ch-char-counter">
            <span style={{ color: charColor }}>{response.length}</span> / {MAX_CHARS}
          </div>
          <button
            className="ch-finish-btn"
            onClick={() => setShowFinishModal(true)}
            disabled={inputDisabled || isAgentTyping || turnCount === 0}
          >
            Finalizar conversación
          </button>
        </div>
        <textarea
          className="ch-input"
          placeholder={isEmpathy ? "Escribe tu respuesta empática aquí..." : "Escribe tu mensaje de networking aquí..."}
          maxLength={MAX_CHARS}
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          disabled={inputDisabled || isAgentTyping || turnCount >= MAX_TURNS}
        />
        <div className="ch-input-actions">
          <span className="ch-turns-remaining">
            {turnsLeft > 0
              ? `${turnsLeft} turno${turnsLeft !== 1 ? "s" : ""} disponible${turnsLeft !== 1 ? "s" : ""}`
              : "Límite alcanzado"}
          </span>
          <button
            className="ch-send-btn"
            onClick={handleSend}
            disabled={
              !response.trim() || isAgentTyping || inputDisabled || turnCount >= MAX_TURNS
            }
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
                <path d="M12 4L3 19h18L12 4z" stroke="#F59E0B" strokeWidth="1.5" strokeLinejoin="round"/>
                <path d="M12 10v4M12 16.5v.5" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 className="modal-title">¿Salir del reto?</h3>
            <p className="modal-desc">Si sales ahora perderás tu progreso en este reto.</p>
            <button className="modal-btn-warning" onClick={() => navigate(`/module/${moduleId}`)}>
              Sí, salir
            </button>
            <button className="modal-btn-cancel" onClick={() => setShowExitModal(false)}>
              Continuar el reto
            </button>
          </div>
        </div>
      )}

      {/* Modal finalizar */}
      {showFinishModal && (
        <div className="modal-overlay" onClick={() => setShowFinishModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon modal-icon-info">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="9" stroke="#2563EB" strokeWidth="1.5"/>
                <path d="M12 8v4M12 14.5v.5" stroke="#2563EB" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 className="modal-title">¿Finalizar conversación?</h3>
            <p className="modal-desc">
              La conversación se cerrará y recibirás tu retroalimentación final.
            </p>
            <button className="modal-btn-info" onClick={() => finishConversation(history)}>
              Finalizar y ver retroalimentación
            </button>
            <button className="modal-btn-cancel" onClick={() => setShowFinishModal(false)}>
              Seguir conversando
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ConversationalChallenge;