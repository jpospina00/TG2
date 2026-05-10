// AxiosInterceptor.js
// Propósito: Componente que configura el token de Auth0 en axios UNA sola vez,
//            cuando Auth0 termina de cargar. Se monta dentro de Auth0Provider en App.js.
// Fecha: 2026-05-08

import { useEffect, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { api } from "./api";

const AUDIENCE = process.env.REACT_APP_AUTH0_AUDIENCE;

export default function AxiosInterceptor({ children }) {
  const { getAccessTokenSilently, isAuthenticated, isLoading } = useAuth0();
  const interceptorRef = useRef(null);

  useEffect(() => {
    // Esperar a que Auth0 termine de inicializar
    if (isLoading) return;

    // Limpiar interceptor anterior si existía
    if (interceptorRef.current !== null) {
      api.interceptors.request.eject(interceptorRef.current);
    }

    // Registrar interceptor solo si el usuario está autenticado
    if (isAuthenticated) {
      interceptorRef.current = api.interceptors.request.use(async (config) => {
        try {
          const tokenParams = AUDIENCE
            ? { authorizationParams: { audience: AUDIENCE } }
            : {};
          const token = await getAccessTokenSilently(tokenParams);
          config.headers.Authorization = `Bearer ${token}`;
        } catch (err) {
          console.warn("No se pudo obtener token Auth0:", err?.error || err?.message);
        }
        return config;
      });
    }

    // Cleanup al desmontar
    return () => {
      if (interceptorRef.current !== null) {
        api.interceptors.request.eject(interceptorRef.current);
      }
    };
  }, [isAuthenticated, isLoading, getAccessTokenSilently]);

  return children;
}