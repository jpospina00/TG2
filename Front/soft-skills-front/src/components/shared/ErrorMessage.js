// ErrorMessage.js
// Propósito: Componente reutilizable para mostrar errores al usuario
// Dependencias: react, react-icons
// Fecha: 2026-03-20

import React from "react";
import { FiAlertTriangle, FiRefreshCw } from "react-icons/fi";
import "./ErrorMessage.css";

function ErrorMessage({ title, message, onRetry }) {
  return (
    <div className="error-wrap">
      <div className="error-icon">
        <FiAlertTriangle size={28} color="#F59E0B" />
      </div>
      <h3 className="error-title">{title || "Algo salió mal"}</h3>
      <p className="error-message">{message || "Ocurrió un error inesperado. Por favor intenta de nuevo."}</p>
      {onRetry && (
        <button className="error-retry-btn" onClick={onRetry}>
          <FiRefreshCw size={14} />
          Intentar de nuevo
        </button>
      )}
    </div>
  );
}

export default ErrorMessage;