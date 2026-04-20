// EmpathyFeedback.js
// Propósito: Retroalimentación del Laboratorio de Empatía
// Dependencias: react, react-router-dom, axios
// Fecha: 2026-04-16

import React, { useState, useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import "./EmpathyFeedback.css";

const API_URL = process.env.REACT_APP_API_URL;

function EmpathyFeedback() {
  const { conversationId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();

  const {
    scores, average, feedback: feedbackFromState,
    completed: completedFromState, levelUp, challenge,
    moduleId, userId, readOnly, isMultiple, isAnalysis,
    options, selectedOptionId,
  } = state || {};

  const [feedbackData, setFeedbackData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (readOnly && conversationId) {
      setLoading(true);
      axios.get(`${API_URL}/feedback/conversation/${conversationId}`)
        .then((res) => {
          setFeedbackData(res.data);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [readOnly, conversationId]);

  const completed = readOnly ? feedbackData?.completed : completedFromState;
  const feedbackText = readOnly
    ? (() => { try { return JSON.parse(feedbackData?.content)?.feedback; } catch { return feedbackData?.content; } })()
    : feedbackFromState;

  const parsedScores = readOnly
    ? (() => { try { return JSON.parse(feedbackData?.content)?.scores; } catch { return null; } })()
    : scores;

  const parsedOptions = readOnly
    ? (() => { try { return JSON.parse(feedbackData?.content)?.options; } catch { return null; } })()
    : options;

  const isMultipleMode = readOnly ? !!parsedOptions : isMultiple;

  if (loading) {
    return <div className="ef-loading"><p>Cargando retroalimentación...</p></div>;
  }

  const SCORE_LABELS = {
    precision_emocional: "Precisión emocional",
    calidad_mensaje: "Calidad del mensaje",
    tono_empatico: "Tono empático",
    coherencia_contextual: "Coherencia contextual",
  };

  return (
    <div className="ef-wrap">
      <nav className="ef-nav">
        <button className="ef-back-btn" onClick={() => navigate(`/empathy/${moduleId}`)}>
          Volver al módulo
        </button>
        <span className="ef-nav-title">Retroalimentación</span>
        <div style={{ width: 80 }} />
      </nav>

      <div className="ef-content">
        {/* Banner resultado */}
        <div className={`ef-banner ${completed ? "ef-banner-ok" : "ef-banner-fail"}`}>
          <div className={`ef-banner-dot ${completed ? "dot-ok" : "dot-fail"}`} />
          <div>
            <p className={`ef-banner-title ${completed ? "title-ok" : "title-fail"}`}>
              {completed ? "Respuesta empática" : "Sigue practicando"}
            </p>
            <p className={`ef-banner-sub ${completed ? "sub-ok" : "sub-fail"}`}>
              {completed
                ? isMultipleMode ? "Elegiste la respuesta más empática" : "Tu análisis y mensaje fueron empáticos"
                : isMultipleMode ? "No era la respuesta más empática" : "Tu análisis necesita mejorar en algunas dimensiones"}
            </p>
          </div>
          {levelUp && !readOnly && (
            <div className="ef-levelup-badge">Nuevo nivel</div>
          )}
        </div>

        {/* Situación */}
        <div className="ef-situation">
          <p className="ef-situation-ctx">{challenge?.context}</p>
          <div className="ef-situation-quote">
            <div className="ef-quote-bar" />
            <p className="ef-quote-text">"{challenge?.opening_message?.slice(0, 100)}..."</p>
          </div>
        </div>

        {/* Resultados análisis — dimensiones */}
        {!isMultipleMode && parsedScores && (
          <>
            <p className="ef-section-title">Evaluación por dimensión</p>
            <div className="ef-scores-grid">
              {Object.entries(parsedScores).map(([key, value]) => (
                <div key={key} className="ef-score-card">
                  <p className="ef-score-name">{SCORE_LABELS[key] || key}</p>
                  <div className="ef-score-bar-wrap">
                    <div
                      className="ef-score-bar"
                      style={{
                        width: `${value * 10}%`,
                        background: value >= 7 ? "#1D9E75" : value >= 5 ? "#BA7517" : "#E24B4A"
                      }}
                    />
                  </div>
                  <p className="ef-score-val" style={{ color: value >= 7 ? "#5DCAA5" : value >= 5 ? "#EF9F27" : "#EF4444" }}>
                    {value.toFixed(1)}
                  </p>
                </div>
              ))}
            </div>
            {average && (
              <div className="ef-average">
                <span className="ef-average-label">Promedio general</span>
                <span className={`ef-average-val ${average >= 7 ? "avg-ok" : average >= 5 ? "avg-mid" : "avg-fail"}`}>
                  {average.toFixed(1)} / 10
                </span>
              </div>
            )}
          </>
        )}

        {/* Resultados selección múltiple — opciones */}
        {isMultipleMode && (parsedOptions || options) && (
          <>
            <p className="ef-section-title">Análisis de opciones</p>
            <div className="ef-options-result">
              {(parsedOptions || options).map((opt) => {
                const isSelected = opt.id === selectedOptionId;
                const isCorrect = opt.is_correct;
                let cls = "ef-opt-idle";
                if (isCorrect) cls = "ef-opt-correct";
                else if (isSelected && !isCorrect) cls = "ef-opt-wrong";
                else cls = "ef-opt-dimmed";
                return (
                  <div key={opt.id} className={`ef-option ${cls}`}>
                    <div className={`ef-opt-letter ${isCorrect ? "letter-ok" : isSelected ? "letter-no" : ""}`}>
                      {opt.id}
                    </div>
                    <div className="ef-opt-body">
                      <p className="ef-opt-text">{opt.text}</p>
                      <p className={`ef-opt-explain ${isCorrect ? "explain-ok" : isSelected && !isCorrect ? "explain-no" : ""}`}>
                        {opt.explanation}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}

        {/* Feedback textual — solo para análisis */}
        {!isMultipleMode && feedbackText && (
          <>
            <p className="ef-section-title">Comentarios de la IA</p>
            <div className="ef-feedback-box">
              <p className="ef-feedback-text">{feedbackText}</p>
            </div>
          </>
        )}

        {/* Acciones */}
        {!readOnly && (
          <div className="ef-actions">
            {levelUp ? (
              <button
                className="ef-btn-primary"
                onClick={() => navigate("/levelup", {
                  state: { newLevel: "intermediate", moduleId, moduleName: "empathy", userId }
                })}
              >
                Ver mi nuevo nivel
              </button>
            ) : completed ? (
              <button className="ef-btn-primary" onClick={() => navigate(`/empathy/${moduleId}`)}>
                Siguiente situación
              </button>
            ) : (
              <button
                className="ef-btn-retry"
                onClick={() => navigate(`/empathy/challenge/${challenge?.id}`, {
                  state: { userId, challenge, moduleId }
                })}
              >
                Reintentar situación
              </button>
            )}
            <button className="ef-btn-secondary" onClick={() => navigate(`/empathy/${moduleId}`)}>
              Volver al módulo
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default EmpathyFeedback;