// SlowRequestBanner.js
// Propósito: Banner que aparece cuando una petición tarda más de lo esperado
// Fecha: 2026-04-26

import React from "react";
import "./SlowRequestBanner.css";

function SlowRequestBanner({ message = "Esto está tardando más de lo esperado..." }) {
  return (
    <div className="srb-wrap">
      <div className="srb-spinner" />
      <div className="srb-text">
        <p className="srb-title">{message}</p>
        <p className="srb-sub">La IA está procesando tu respuesta. Por favor espera.</p>
      </div>
    </div>
  );
}

export default SlowRequestBanner;