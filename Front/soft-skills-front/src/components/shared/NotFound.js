// NotFound.js
// Propósito: Página 404 para rutas inexistentes
// Dependencias: react, react-router-dom, react-icons
// Fecha: 2026-03-20

import React from "react";
import { useNavigate } from "react-router-dom";
import { FiHome, FiAlertCircle } from "react-icons/fi";
import "./NotFound.css";

function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="notfound-wrap">
      <div className="notfound-content">
        <div className="notfound-icon">
          <FiAlertCircle size={48} color="#2563EB" />
        </div>
        <h1 className="notfound-code">404</h1>
        <h2 className="notfound-title">Página no encontrada</h2>
        <p className="notfound-desc">
          La página que buscas no existe o fue movida.
          Vuelve al inicio para continuar entrenando.
        </p>
        <button
          className="notfound-btn"
          onClick={() => navigate("/dashboard")}
        >
          <FiHome size={16} />
          Volver al inicio
        </button>
      </div>
    </div>
  );
}

export default NotFound;