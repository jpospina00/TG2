// Diagnostic.js
// Propósito: Test diagnóstico inicial por módulo — opción múltiple + escritura
// Dependencias: react, react-router-dom, axios, react-icons
// Fecha: 2026-03-20

import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import { FiArrowLeft, FiArrowRight, FiCheckCircle } from "react-icons/fi";
import ErrorMessage from "../shared/ErrorMessage";
import "./Diagnostic.css";

const API_URL = process.env.REACT_APP_API_URL;

const STEPS = {
  LOADING: "loading",
  INTRO: "intro",
  QUESTIONS: "questions",
  WRITING: "writing",
  SUBMITTING: "submitting",
  RESULT: "result",
};

function Diagnostic() {
  const { moduleId } = useParams();
  const { user } = useAuth0();
  const navigate = useNavigate();

  const [step, setStep] = useState(STEPS.LOADING);
  const [userId, setUserId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [scenario, setScenario] = useState(null);
  const [answers, setAnswers] = useState({});
  const [writtenResponse, setWrittenResponse] = useState("");
  const [result, setResult] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [error, setError] = useState(null);

  const moduleName = moduleId === "1" ? "empathy" : "networking";
  const moduleLabel = moduleName === "empathy" ? "Comunicación Empática" : "Networking Profesional";
  const MAX_CHARS = 500;

  useEffect(() => {
    if (user) loadDiagnostic();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  async function loadDiagnostic() {
    try {
      const userRes = await axios.get(`${API_URL}/users/auth0/${user.sub}`);
      setUserId(userRes.data.id);

      const diagRes = await axios.get(
        `${API_URL}/diagnostic/user/${userRes.data.id}/module/${moduleId}`
      );

      if (diagRes.data.has_diagnostic) {
        // Ya tiene diagnóstico — ir directo al módulo
        navigate(`/module/${moduleId}`);
        return;
      }

      // Cargar preguntas
      const qRes = await axios.get(`${API_URL}/diagnostic/questions/${moduleName}`);
      setQuestions(qRes.data.questions);
      setScenario(qRes.data.scenario);
      setStep(STEPS.INTRO);
    } catch (err) {
      console.error("Error cargando diagnóstico:", err);
      setError("No se pudo cargar el diagnóstico. Verifica tu conexión.");
      setStep(STEPS.INTRO);
    }
  }

  function handleAnswer(questionId, option) {
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  }

  function calculateScore() {
    return questions.filter((q) => answers[q.id] === q.correct).length;
  }

  async function handleSubmit() {
    if (!writtenResponse.trim()) return;
    setStep(STEPS.SUBMITTING);
    setError(null);

    try {
      const score = calculateScore();
      const res = await axios.post(`${API_URL}/diagnostic/submit`, {
        user_id: userId,
        module_id: parseInt(moduleId),
        module_name: moduleName,
        multiple_choice_score: score,
        scenario,
        written_response: writtenResponse,
      });
      setResult(res.data);
      setStep(STEPS.RESULT);
    } catch (err) {
      console.error("Error enviando diagnóstico:", err);
      setError("No se pudo procesar el diagnóstico. Intenta de nuevo.");
      setStep(STEPS.WRITING);
    }
  }

  function getLevelLabel(level) {
    const labels = {
      beginner: "Nivel Inicial",
      intermediate: "Nivel Intermedio",
      advanced: "Nivel Avanzado",
    };
    return labels[level] || level;
  }

  function getLevelColor(level) {
    const colors = {
      beginner: "#60A5FA",
      intermediate: "#0EA5E9",
      advanced: "#10B981",
    };
    return colors[level] || "#60A5FA";
  }

  // LOADING
  if (step === STEPS.LOADING) {
    return (
      <div className="diag-loading">
        <div className="diag-spinner" />
        <p>Preparando tu diagnóstico...</p>
      </div>
    );
  }

  // INTRO
  if (step === STEPS.INTRO) {
    return (
      <div className="diag-wrap">
        <nav className="diag-navbar">
          <button className="diag-back-btn" onClick={() => navigate("/dashboard")}>
            <FiArrowLeft size={16} />
            Volver
          </button>
          <span className="diag-navbar-title">Diagnóstico inicial</span>
          <div style={{ width: 60 }} />
        </nav>
        <div className="diag-content">
          <div className="diag-intro-card">
            <div className="diag-intro-icon" style={{ background: moduleName === "empathy" ? "rgba(37,99,235,0.15)" : "rgba(14,165,233,0.15)" }}>
              <span style={{ fontSize: 32 }}>{moduleName === "empathy" ? "💬" : "🤝"}</span>
            </div>
            <h1 className="diag-intro-title">Diagnóstico de {moduleLabel}</h1>
            <p className="diag-intro-desc">
              Antes de comenzar a practicar, evaluaremos tu nivel actual para
              asignarte retos personalizados que se adapten a tus fortalezas y
              áreas de mejora.
            </p>
            <div className="diag-intro-steps">
              <div className="diag-intro-step">
                <div className="diag-step-num">1</div>
                <div>
                  <p className="diag-step-title">3 preguntas de opción múltiple</p>
                  <p className="diag-step-desc">Situaciones comunicativas reales</p>
                </div>
              </div>
              <div className="diag-intro-step">
                <div className="diag-step-num">2</div>
                <div>
                  <p className="diag-step-title">1 reto de escritura</p>
                  <p className="diag-step-desc">Responde a un escenario real</p>
                </div>
              </div>
              <div className="diag-intro-step">
                <div className="diag-step-num">3</div>
                <div>
                  <p className="diag-step-title">Retos personalizados</p>
                  <p className="diag-step-desc">La IA genera retos para ti</p>
                </div>
              </div>
            </div>
            {error && <ErrorMessage title="Error de carga" message={error} onRetry={loadDiagnostic} />}
            <button className="diag-start-btn" onClick={() => setStep(STEPS.QUESTIONS)}>
              Comenzar diagnóstico
              <FiArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // QUESTIONS
  if (step === STEPS.QUESTIONS) {
    const q = questions[currentQuestion];
    const isLast = currentQuestion === questions.length - 1;
    const allAnswered = questions.every((q) => answers[q.id]);

    return (
      <div className="diag-wrap">
        <nav className="diag-navbar">
          <button className="diag-back-btn" onClick={() => currentQuestion > 0 ? setCurrentQuestion(c => c - 1) : setStep(STEPS.INTRO)}>
            <FiArrowLeft size={16} />
            Atrás
          </button>
          <span className="diag-navbar-title">Pregunta {currentQuestion + 1} de {questions.length}</span>
          <div style={{ width: 60 }} />
        </nav>

        {/* Barra de progreso */}
        <div className="diag-progress-bar-wrap">
          <div
            className="diag-progress-bar-fill"
            style={{ width: `${((currentQuestion + 1) / questions.length) * 50}%` }}
          />
        </div>

        <div className="diag-content">
          <p className="diag-step-label">Opción múltiple</p>
          <div className="diag-question-card">
            <p className="diag-situation">{q.situation}</p>
            <p className="diag-question">{q.question}</p>
            <div className="diag-options">
              {Object.entries(q.options).map(([key, value]) => (
                <button
                  key={key}
                  className={`diag-option ${answers[q.id] === key ? "option-selected" : ""}`}
                  onClick={() => handleAnswer(q.id, key)}
                >
                  <span className="diag-option-key">{key}</span>
                  <span className="diag-option-text">{value}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="diag-nav-btns">
            {isLast ? (
              <button
                className="diag-next-btn"
                onClick={() => setStep(STEPS.WRITING)}
                disabled={!allAnswered}
              >
                Continuar al reto de escritura
                <FiArrowRight size={16} />
              </button>
            ) : (
              <button
                className="diag-next-btn"
                onClick={() => setCurrentQuestion(c => c + 1)}
                disabled={!answers[q.id]}
              >
                Siguiente pregunta
                <FiArrowRight size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // WRITING
  if (step === STEPS.WRITING) {
    const charColor = writtenResponse.length > 450 ? "#EF4444" : "#60A5FA";

    return (
      <div className="diag-wrap">
        <nav className="diag-navbar">
          <button className="diag-back-btn" onClick={() => setStep(STEPS.QUESTIONS)}>
            <FiArrowLeft size={16} />
            Atrás
          </button>
          <span className="diag-navbar-title">Reto de escritura</span>
          <div style={{ width: 60 }} />
        </nav>

        {/* Barra de progreso */}
        <div className="diag-progress-bar-wrap">
          <div className="diag-progress-bar-fill" style={{ width: "75%" }} />
        </div>

        <div className="diag-content">
          <p className="diag-step-label">Reto de escritura</p>

          {scenario && (
            <div className="diag-scenario-card">
              <div className="diag-scenario-agent">
                <div className="diag-agent-avatar">
                  {scenario.agent_profile?.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <p className="diag-agent-name">
                    {scenario.agent_profile?.split(" ").slice(0, 3).join(" ")}
                  </p>
                  <p className="diag-agent-role">{scenario.agent_profile}</p>
                </div>
              </div>
              <div className="diag-scenario-context">
                <p className="diag-context-label">Contexto</p>
                <p className="diag-context-text">{scenario.context}</p>
              </div>
              <div className="diag-scenario-message">
                <p className="diag-message-label">Mensaje</p>
                <p className="diag-message-text">"{scenario.opening_message}"</p>
              </div>
            </div>
          )}

          <div className="diag-write-section">
            <div className="diag-char-counter">
              <span style={{ color: charColor }}>{writtenResponse.length}</span> / {MAX_CHARS}
            </div>
            <textarea
              className="diag-textarea"
              placeholder={moduleName === "empathy"
                ? "Escribe tu respuesta empática aquí..."
                : "Escribe tu mensaje de networking aquí..."}
              maxLength={MAX_CHARS}
              value={writtenResponse}
              onChange={(e) => setWrittenResponse(e.target.value)}
            />
            {error && <ErrorMessage title="Error" message={error} onRetry={() => setError(null)} />}
            <button
              className="diag-next-btn"
              onClick={handleSubmit}
              disabled={!writtenResponse.trim()}
            >
              Enviar y ver mi nivel
              <FiArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // SUBMITTING
  if (step === STEPS.SUBMITTING) {
    return (
      <div className="diag-loading">
        <div className="diag-spinner" />
        <p>Analizando tu diagnóstico...</p>
        <p className="diag-loading-sub">La IA está generando tus retos personalizados</p>
      </div>
    );
  }

  // RESULT
  if (step === STEPS.RESULT && result) {
    const levelColor = getLevelColor(result.level_result);

    return (
      <div className="diag-wrap">
        <nav className="diag-navbar">
          <div style={{ width: 60 }} />
          <span className="diag-navbar-title">Resultado del diagnóstico</span>
          <div style={{ width: 60 }} />
        </nav>

        <div className="diag-content">
          <div className="diag-result-card">
            <div className="diag-result-icon" style={{ background: levelColor + "20", borderColor: levelColor + "40" }}>
              <FiCheckCircle size={36} color={levelColor} />
            </div>

            <p className="diag-result-congrats">¡Diagnóstico completado!</p>
            <h1 className="diag-result-level" style={{ color: levelColor }}>
              {getLevelLabel(result.level_result)}
            </h1>
            <p className="diag-result-module">Módulo de {moduleLabel}</p>
            <p className="diag-result-desc">
              Basándose en tu desempeño, la IA ha asignado este nivel de entrada
              y generado {result.challenges_generated} retos personalizados para ti.
            </p>

            <div className="diag-result-sections">
              <div className="diag-result-section section-ok">
                <p className="diag-result-section-label">Fortalezas detectadas</p>
                <p className="diag-result-section-text">{result.strengths}</p>
              </div>
              <div className="diag-result-section section-improve">
                <p className="diag-result-section-label">Áreas de mejora</p>
                <p className="diag-result-section-text">{result.weaknesses}</p>
              </div>
              <div className="diag-result-section section-feedback">
                <p className="diag-result-section-label">Retroalimentación general</p>
                <p className="diag-result-section-text">{result.written_feedback}</p>
              </div>
            </div>

            <button
              className="diag-start-btn"
              onClick={() => navigate(`/module/${moduleId}`)}
            >
              Ver mis retos personalizados
              <FiArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default Diagnostic;