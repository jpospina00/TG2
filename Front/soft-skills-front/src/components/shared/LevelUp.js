// LevelUp.js
// Propósito: Pantalla de celebración cuando el estudiante sube de nivel
// Dependencias: react, react-router-dom, react-icons
// Fecha: 2026-03-20

import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { FiStar, FiArrowRight } from "react-icons/fi";
import "./LevelUp.css";

const LEVEL_INFO = {
  intermediate: {
    label: "Nivel Intermedio",
    desc: "Ahora enfrentarás situaciones más complejas que requieren interpretar el contexto y adaptar tu tono. ¡Estás listo para el siguiente desafío!",
    color: "#0EA5E9",
  },
  advanced: {
    label: "Nivel Avanzado",
    desc: "Has llegado al nivel más alto. Aquí encontrarás interacciones ambiguas y situaciones complejas que pondrán a prueba todas tus habilidades. ¡Demuestra lo que aprendiste!",
    color: "#10B981",
  },
};

function LevelUp() {
  const navigate = useNavigate();
  const { state } = useLocation();
  const { newLevel, moduleId, moduleName } = state || {};
  const [show, setShow] = useState(false);

  const info = LEVEL_INFO[newLevel];
  const isEmpathy = moduleName === "empathy";

  useEffect(() => {
    setTimeout(() => setShow(true), 100);
  }, []);

  if (!newLevel || !info) {
    navigate("/dashboard");
    return null;
  }

  return (
    <div className={`levelup-wrap ${show ? "levelup-visible" : ""}`}>
      <div className="levelup-content">

        {/* Partículas decorativas */}
        <div className="levelup-particles">
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className="levelup-particle"
              style={{
                left: `${10 + i * 12}%`,
                animationDelay: `${i * 0.15}s`,
                background: i % 2 === 0 ? info.color : "#F59E0B",
              }}
            />
          ))}
        </div>

        {/* Icono */}
        <div className="levelup-icon-wrap" style={{ borderColor: info.color + "40", background: info.color + "15" }}>
          <FiStar size={48} color={info.color} />
        </div>

        {/* Texto */}
        <p className="levelup-congrats">¡Felicitaciones!</p>
        <h1 className="levelup-title">
          Subiste al<br />
          <span style={{ color: info.color }}>{info.label}</span>
        </h1>
        <p className="levelup-module">
          Módulo de {isEmpathy ? "Comunicación Empática" : "Networking Profesional"}
        </p>
        <p className="levelup-desc">{info.desc}</p>

        {/* Stats */}
        <div className="levelup-stats">
          <div className="levelup-stat">
            <span className="levelup-stat-num" style={{ color: info.color }}>4+</span>
            <span className="levelup-stat-label">Retos superados</span>
          </div>
          <div className="levelup-stat-divider" />
          <div className="levelup-stat">
            <span className="levelup-stat-num" style={{ color: info.color }}>
              {newLevel === "intermediate" ? "2/3" : "3/3"}
            </span>
            <span className="levelup-stat-label">Niveles completados</span>
          </div>
        </div>

        {/* Botón */}
        <button
          className="levelup-btn"
          style={{ background: `linear-gradient(135deg, ${info.color}, ${isEmpathy ? "#2563EB" : "#2563EB"})` }}
          onClick={() => moduleId === '1' ? navigate(`/empathy/${moduleId}`) : navigate(`/module/${moduleId}`)}
        >
          Continuar al {info.label}
          <FiArrowRight size={16} />
        </button>

        <button
          className="levelup-btn-secondary"
          onClick={() => navigate("/dashboard")}
        >
          Ir al inicio
        </button>

      </div>
    </div>
  );
}

export default LevelUp;