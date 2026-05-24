// SessionExpiredModal.js
// Propósito: Modal global que aparece cuando el token expira (401 del backend).
//            Se controla desde SessionExpiredContext y se dispara desde AxiosInterceptor.
// Fecha: 2026-05-08

import React, { createContext, useContext, useState, useCallback } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import "./SessionExpiredModal.css";

// ── Contexto ──────────────────────────────────────────────────────────────────
const SessionExpiredContext = createContext(null);

export function useSessionExpired() {
  return useContext(SessionExpiredContext);
}

// ── Provider — envuelve la app en App.js ──────────────────────────────────────
export function SessionExpiredProvider({ children }) {
  const [visible, setVisible] = useState(false);
  const { loginWithRedirect, logout } = useAuth0();

  const trigger = useCallback(() => setVisible(true), []);

  function handleRelogin() {
    setVisible(false);
    logout({ logoutParams: { returnTo: window.location.origin } });
  }

  return (
    <SessionExpiredContext.Provider value={{ trigger }}>
      {children}
      {visible && (
        <div className="sem-overlay" role="dialog" aria-modal="true" aria-labelledby="sem-title">
          <div className="sem-card">
            <div className="sem-icon">🔒</div>
            <h2 className="sem-title" id="sem-title">Sesión expirada</h2>
            <p className="sem-body">
              Tu sesión ha caducado o no tenés permisos para realizar esta acción.
              Iniciá sesión nuevamente para continuar.
            </p>
            <button className="sem-btn" onClick={handleRelogin}>
              Iniciar sesión nuevamente
            </button>
          </div>
        </div>
      )}
    </SessionExpiredContext.Provider>
  );
}