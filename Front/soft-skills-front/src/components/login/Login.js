// Login.js
// Propósito: Pantalla de entrada con autenticación Auth0
// Dependencias: @auth0/auth0-react, react-icons
// Fecha: 2026-03-20

import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { FiClock, FiCheckCircle, FiUsers } from "react-icons/fi";
import "./Login.css";

function Login() {
  const { loginWithRedirect } = useAuth0();

  return (
    <div className="login-wrap">
      <div className="login-card">

        <div className="login-logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <path d="M16 4C9.373 4 4 9.373 4 16s5.373 12 12 12 12-5.373 12-12S22.627 4 16 4z" fill="rgba(255,255,255,0.15)"/>
            <path d="M11 13c0-1.1.9-2 2-2h6a2 2 0 012 2v2a2 2 0 01-2 2h-1l-2 3-2-3h-1a2 2 0 01-2-2v-2z" fill="white"/>
            <circle cx="13.5" cy="13.8" r="1" fill="#2563EB"/>
            <circle cx="16" cy="13.8" r="1" fill="#2563EB"/>
            <circle cx="18.5" cy="13.8" r="1" fill="#2563EB"/>
          </svg>
        </div>

        <h1 className="login-title">Entrenador Virtual</h1>
        <p className="login-subtitle">
          Desarrolla tus habilidades de comunicación empática
          y networking profesional con apoyo de IA
        </p>

        <hr className="login-divider" />

        <div className="login-features">
          <div className="feature-item">
            <div className="feature-icon icon-blue">
              <FiClock size={16} color="#2563EB" />
            </div>
            <span className="feature-text">
              Retos comunicativos con retroalimentación inmediata de IA
            </span>
          </div>
          <div className="feature-item">
            <div className="feature-icon icon-green">
              <FiCheckCircle size={16} color="#10B981" />
            </div>
            <span className="feature-text">
              Progreso gamificado con 3 niveles por módulo
            </span>
          </div>
          <div className="feature-item">
            <div className="feature-icon icon-cyan">
              <FiUsers size={16} color="#0EA5E9" />
            </div>
            <span className="feature-text">
              Módulos de empatía y networking profesional
            </span>
          </div>
        </div>

        <button
          className="login-btn"
          onClick={() => loginWithRedirect()}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="8" stroke="white" strokeWidth="1.5"/>
            <path d="M9 5v4l3 2" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          Iniciar sesión con Auth0
        </button>

        <p className="login-footer">
          Al continuar aceptas los{" "}
          <span className="login-link">términos de uso</span>{" "}
          del sistema
        </p>

      </div>
    </div>
  );
}

export default Login;