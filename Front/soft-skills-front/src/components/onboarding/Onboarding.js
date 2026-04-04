// Onboarding.js
// Propósito: Pantalla de perfil inicial del estudiante — aparece una sola vez al registrarse
// Dependencias: react, react-router-dom, axios, @auth0/auth0-react
// Fecha: 2026-03-29

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import { FiArrowRight, FiArrowLeft, FiBarChart2,
  FiTarget,
  FiCpu,
  FiTrendingUp } from "react-icons/fi";
import "./Onboarding.css";
import {
  LuBrain,
  LuServer,
  LuMonitor,
  LuRocket,
  LuShield,
  LuSmartphone,
  LuCode,
  LuSmile
} from "react-icons/lu";
const API_URL = process.env.REACT_APP_API_URL;

const SPECIALIZATIONS = [
  {
    id: "ai",
    label: "Inteligencia Artificial",
    icon: <LuBrain />,
    desc: "Machine Learning, Deep Learning, NLP",
  },
  {
    id: "backend",
    label: "Desarrollo Backend",
    icon: <LuServer />,
    desc: "APIs, bases de datos, servidores",
  },
  {
    id: "frontend",
    label: "Desarrollo Frontend",
    icon: <LuMonitor />,
    desc: "React, Vue, interfaces de usuario",
  },
  {
    id: "devops",
    label: "DevOps",
    icon: <LuRocket />,
    desc: "CI/CD, Docker, infraestructura en la nube",
  },
  {
    id: "data",
    label: "Ciencia de Datos",
    icon: <FiBarChart2 />,
    desc: "Analytics, visualización, Big Data",
  },
  {
    id: "security",
    label: "Ciberseguridad",
    icon: <LuShield />,
    desc: "Ethical hacking, seguridad de redes",
  },
  {
    id: "mobile",
    label: "Desarrollo Móvil",
    icon: <LuSmartphone />,
    desc: "Android, iOS, React Native",
  },
  {
    id: "other",
    label: "General / Otro",
    icon: <LuCode />,
    desc: "Otras áreas de Ingeniería de Sistemas",
  },
];

const SEMESTERS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];

const LEVELS = [
  {
    id: "beginner",
    label: "Principiante",
    desc: "Pocas o ninguna experiencia en habilidades blandas formales",
  },
  {
    id: "intermediate",
    label: "Intermedio",
    desc: "Algo de experiencia, pero quiero mejorar",
  },
  {
    id: "advanced",
    label: "Avanzado",
    desc: "Tengo buenas habilidades y quiero perfeccionarlas",
  },
];

const STEPS = { WELCOME: 0, SEMESTER: 1, SPECIALIZATION: 2, LEVEL: 3 };

function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuth0();
  const [userId, setUserId] = useState(null);

  const [step, setStep] = useState(STEPS.WELCOME);
  const [semester, setSemester] = useState("");
  const [specialization, setSpecialization] = useState("");
  const [selfLevel, setSelfLevel] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) {
      axios
        .get(`${API_URL}/users/auth0/${user.sub}`)
        .then((res) => setUserId(res.data.id))
        .catch((err) => console.error(err));
    }
  }, [user]);

  async function handleFinish() {
    if (!semester || !specialization || !selfLevel || !userId) return;
    setSaving(true);
    try {
      await axios.post(`${API_URL}/students/profile`, {
        user_id: userId,
        semester,
        specialization,
        self_assessed_level: selfLevel,
      });
      navigate("/dashboard");
    } catch (err) {
      console.error("Error guardando perfil:", err);
      navigate("/dashboard");
    }
  }

  const firstName = user?.name?.split(" ")[0] || "estudiante";

  return (
    <div className="ob-wrap">
      <div className="ob-card">
        {/* Barra de progreso */}
        {step > STEPS.WELCOME && (
          <div className="ob-progress-bar">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`ob-progress-step ${step >= s ? "ob-step-active" : ""}`}
              />
            ))}
          </div>
        )}

        {/* STEP 0 — BIENVENIDA */}
        {step === STEPS.WELCOME && (
  <div className="ob-step">

    <div className="ob-welcome-icon">
      <LuSmile size={42} />
    </div>

    <h1 className="ob-title">¡Bienvenido, {firstName}!</h1>

    <p className="ob-desc">
      Antes de comenzar, queremos conocerte un poco para personalizar tu
      experiencia de entrenamiento. Solo tomará un momento.
    </p>

    <div className="ob-features">

      <div className="ob-feature">
        <span className="ob-feature-icon">
          <FiTarget size={20} />
        </span>
        <p>Retos adaptados a tu área de especialización</p>
      </div>

      <div className="ob-feature">
        <span className="ob-feature-icon">
          <FiCpu size={20} />
        </span>
        <p>Escenarios reales del mundo tech</p>
      </div>

      <div className="ob-feature">
        <span className="ob-feature-icon">
          <FiTrendingUp size={20} />
        </span>
        <p>Nivel de entrada personalizado</p>
      </div>

    </div>

    <button
      className="ob-btn-primary"
      onClick={() => setStep(STEPS.SEMESTER)}
    >
      Comenzar
      <FiArrowRight size={16} />
    </button>

  </div>
)}

        {/* STEP 1 — SEMESTRE */}
        {step === STEPS.SEMESTER && (
          <div className="ob-step">
            <p className="ob-step-label">Paso 1 de 3</p>
            <h2 className="ob-title">¿En qué semestre estás?</h2>
            <p className="ob-desc">
              Esto nos ayuda a calibrar la dificultad de los retos.
            </p>
            <div className="ob-semester-grid">
              {SEMESTERS.map((s) => (
                <button
                  key={s}
                  className={`ob-semester-btn ${semester === s ? "ob-selected" : ""}`}
                  onClick={() => setSemester(s)}
                >
                  {s}°
                </button>
              ))}
            </div>
            <div className="ob-nav">
              <button
                className="ob-btn-secondary"
                onClick={() => setStep(STEPS.WELCOME)}
              >
                <FiArrowLeft size={16} /> Atrás
              </button>
              <button
                className="ob-btn-primary"
                onClick={() => setStep(STEPS.SPECIALIZATION)}
                disabled={!semester}
              >
                Siguiente <FiArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2 — ESPECIALIZACIÓN */}
        {step === STEPS.SPECIALIZATION && (
          <div className="ob-step">
            <p className="ob-step-label">Paso 2 de 3</p>
            <h2 className="ob-title">¿Cuál es tu área de interés?</h2>
            <p className="ob-desc">
              Los retos usarán contextos de tu especialización.
            </p>
            <div className="ob-spec-grid">
              {SPECIALIZATIONS.map((spec) => (
                <button
                  key={spec.id}
                  className={`ob-spec-btn ${specialization === spec.id ? "ob-selected" : ""}`}
                  onClick={() => setSpecialization(spec.id)}
                >
                  <span className="ob-spec-icon">{spec.icon}</span>
                  <span className="ob-spec-label">{spec.label}</span>
                  <span className="ob-spec-desc">{spec.desc}</span>
                </button>
              ))}
            </div>
            <div className="ob-nav">
              <button
                className="ob-btn-secondary"
                onClick={() => setStep(STEPS.SEMESTER)}
              >
                <FiArrowLeft size={16} /> Atrás
              </button>
              <button
                className="ob-btn-primary"
                onClick={() => setStep(STEPS.LEVEL)}
                disabled={!specialization}
              >
                Siguiente <FiArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3 — NIVEL */}
        {step === STEPS.LEVEL && (
          <div className="ob-step">
            <p className="ob-step-label">Paso 3 de 3</p>
            <h2 className="ob-title">
              ¿Cómo describes tus habilidades blandas actuales?
            </h2>
            <p className="ob-desc">
              Tu respuesta honesta nos ayuda a asignarte el punto de partida
              correcto.
            </p>
            <div className="ob-level-grid">
              {LEVELS.map((lv) => (
                <button
                  key={lv.id}
                  className={`ob-level-btn ${selfLevel === lv.id ? "ob-selected" : ""}`}
                  onClick={() => setSelfLevel(lv.id)}
                >
                  <span className="ob-level-label">{lv.label}</span>
                  <span className="ob-level-desc">{lv.desc}</span>
                </button>
              ))}
            </div>
            <div className="ob-nav">
              <button
                className="ob-btn-secondary"
                onClick={() => setStep(STEPS.SPECIALIZATION)}
              >
                <FiArrowLeft size={16} /> Atrás
              </button>
              <button
                className="ob-btn-primary"
                onClick={handleFinish}
                disabled={!selfLevel || saving}
              >
                {saving ? "Guardando..." : "Comenzar entrenamiento"}
                {!saving && <FiArrowRight size={16} />}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Onboarding;
