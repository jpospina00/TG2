// EmpathyLab.js
// Propósito: Reto del Laboratorio de Empatía — análisis + selección múltiple
// Dependencias: react, react-router-dom, axios
// Fecha: 2026-04-16

import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import "./EmpathyLab.css";

const API_URL = process.env.REACT_APP_API_URL;

function EmpathyLab() {
  const { challengeId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();

  const { userId, challenge, moduleId } = state || {};

  const [conversationId, setConversationId] = useState(null);
  const [emotionText, setEmotionText] = useState("");
  const [messageText, setMessageText] = useState("");
  const [options, setOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [showExitModal, setShowExitModal] = useState(false);
  const [step, setStep] = useState("loading");

  const isMultiple = challenge?.type === "multiple_choice";

  useEffect(() => {
    if (userId && challenge) initConversation();
  }, [userId, challenge]);

  async function initConversation() {
    try {
      const res = await axios.post(`${API_URL}/conversations`, {
        user_id: userId,
        challenge_id: challenge.id,
      });
      setConversationId(res.data.id);

      if (isMultiple) {
        setStep("loading-options");
        setLoadingOptions(true);
        const optRes = await axios.get(`${API_URL}/ai/empathy/options/${challenge.id}`);
        setOptions(optRes.data.options);
        setLoadingOptions(false);
        setStep("multiple");
      } else {
        setStep("analysis");
      }
    } catch (err) {
      console.error("Error iniciando conversación:", err);
    }
  }

  async function handleSubmitAnalysis() {
    if (!emotionText.trim() || !messageText.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/ai/empathy/evaluate`, {
        conversation_id: conversationId,
        emotion_identification: emotionText,
        student_message: messageText,
      });
      navigate(`/empathy/feedback/${conversationId}`, {
        state: {
          scores: res.data.scores,
          average: res.data.average,
          feedback: res.data.feedback,
          completed: res.data.completed,
          levelUp: res.data.level_up,
          challenge,
          moduleId,
          userId,
          isAnalysis: true,
        },
      });
    } catch (err) {
      console.error("Error evaluando:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmitMultiple() {
    if (!selectedOption) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/ai/empathy/multiple-choice`, {
        conversation_id: conversationId,
        selected_option_id: selectedOption.id,
        is_correct: selectedOption.is_correct,
        options,
      });
      navigate(`/empathy/feedback/${conversationId}`, {
        state: {
          completed: res.data.completed,
          levelUp: res.data.level_up,
          options: res.data.options,
          selectedOptionId: selectedOption.id,
          challenge,
          moduleId,
          userId,
          isMultiple: true,
        },
      });
    } catch (err) {
      console.error("Error enviando selección:", err);
    } finally {
      setLoading(false);
    }
  }

  if (!challenge) {
    return <div className="el-loading"><p>Cargando situación...</p></div>;
  }

  return (
    <div className="el-wrap">
      <nav className="el-nav">
        <button className="el-exit-btn" onClick={() => setShowExitModal(true)}>Salir</button>
        <span className="el-nav-title">Laboratorio de empatía</span>
        <span className="el-nav-badge">{isMultiple ? "Selección múltiple" : "Análisis"}</span>
      </nav>

      <div className="el-content">
        {/* Situación */}
        <div className="el-situation">
          <p className="el-situation-ctx">{challenge.context}</p>
          <div className="el-situation-quote">
            <div className="el-quote-bar" />
            <p className="el-quote-text">"{challenge.opening_message}"</p>
          </div>
        </div>

        {/* Selección múltiple */}
        {step === "loading-options" && (
          <div className="el-generating">
            <div className="el-spinner" />
            <p>Generando opciones...</p>
          </div>
        )}

        {step === "multiple" && (
          <>
            <p className="el-prompt">¿Cuál es la respuesta más empática?</p>
            <div className="el-options">
              {options.map((opt) => (
                <button
                  key={opt.id}
                  className={`el-option ${selectedOption?.id === opt.id ? "el-option-selected" : ""}`}
                  onClick={() => setSelectedOption(opt)}
                >
                  <div className={`el-opt-letter ${selectedOption?.id === opt.id ? "el-opt-letter-sel" : ""}`}>
                    {opt.id}
                  </div>
                  <p className="el-opt-text">{opt.text}</p>
                </button>
              ))}
            </div>
            <button
              className="el-submit-btn"
              onClick={handleSubmitMultiple}
              disabled={!selectedOption || loading}
            >
              {loading ? "Enviando..." : "Confirmar respuesta"}
            </button>
          </>
        )}

        {/* Análisis */}
        {step === "analysis" && (
          <>
            <div className="el-step">
              <div className="el-step-header">
                <div className="el-step-num">1</div>
                <p className="el-step-label">¿Qué emociones identificas en esta persona?</p>
              </div>
              <p className="el-step-hint">Describe qué siente y por qué crees que se siente así</p>
              <textarea
                className="el-textarea"
                value={emotionText}
                onChange={(e) => setEmotionText(e.target.value.slice(0, 300))}
                placeholder="Creo que está sintiendo..."
                rows={3}
              />
              <p className="el-char-count">{emotionText.length} / 300</p>
            </div>

            <div className="el-divider" />

            <div className="el-step">
              <div className="el-step-header">
                <div className="el-step-num">2</div>
                <p className="el-step-label">¿Qué le dirías?</p>
              </div>
              <p className="el-step-hint">Escribe el mensaje que le enviarías a esta persona</p>
              <textarea
                className="el-textarea"
                value={messageText}
                onChange={(e) => setMessageText(e.target.value.slice(0, 400))}
                placeholder="Escribe tu mensaje aquí..."
                rows={4}
              />
              <p className="el-char-count">{messageText.length} / 400</p>
            </div>

            <button
              className="el-submit-btn"
              onClick={handleSubmitAnalysis}
              disabled={emotionText.length < 5 || messageText.length < 10 || loading}
            >
              {loading ? "Analizando..." : "Enviar y analizar"}
            </button>
          </>
        )}
      </div>

      {/* Modal salir */}
      {showExitModal && (
        <div className="el-overlay" onClick={() => setShowExitModal(false)}>
          <div className="el-modal" onClick={(e) => e.stopPropagation()}>
            <div className="el-modal-handle" />
            <div className="el-modal-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 5v6M10 13.5v1" stroke="#633806" strokeWidth="1.5" strokeLinecap="round"/>
                <path d="M10 2L2 17h16L10 2z" stroke="#633806" strokeWidth="1.2" strokeLinejoin="round"/>
              </svg>
            </div>
            <h3 className="el-modal-title">¿Salir del análisis?</h3>
            <p className="el-modal-desc">Si sales ahora perderás lo que escribiste. Tu progreso en el módulo se mantiene.</p>
            <div className="el-modal-situation">
              <p className="el-modal-situation-label">Situación en curso</p>
              <p className="el-modal-situation-text">"{challenge.opening_message.slice(0, 60)}..."</p>
            </div>
            <button className="el-modal-btn el-modal-btn-danger" onClick={() => navigate(`/empathy/${moduleId}`)}>
              Sí, salir
            </button>
            <button className="el-modal-btn el-modal-btn-cancel" onClick={() => setShowExitModal(false)}>
              Continuar análisis
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default EmpathyLab;