// AxiosInterceptor.js
// Propósito: Configura el token de Auth0 en axios y dispara el modal de sesión
//            expirada cuando el backend responde con 401 o 403 Not authenticated.
// Fecha: 2026-05-08

import { useEffect, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { api } from "./api";
import { useSessionExpired } from "./SessionExpiredModal";

const AUDIENCE = process.env.REACT_APP_AUTH0_AUDIENCE;

export default function AxiosInterceptor({ children }) {
  const { getAccessTokenSilently, isAuthenticated, isLoading } = useAuth0();
  const { trigger } = useSessionExpired();
  const requestInterceptorRef  = useRef(null);
  const responseInterceptorRef = useRef(null);

  useEffect(() => {
    if (isLoading) return;

    // Limpiar interceptores anteriores
    if (requestInterceptorRef.current !== null) {
      api.interceptors.request.eject(requestInterceptorRef.current);
      requestInterceptorRef.current = null;
    }
    if (responseInterceptorRef.current !== null) {
      api.interceptors.response.eject(responseInterceptorRef.current);
      responseInterceptorRef.current = null;
    }

    // Request — adjuntar token si está autenticado
    if (isAuthenticated) {
      requestInterceptorRef.current = api.interceptors.request.use(async (config) => {
        try {
          const tokenParams = AUDIENCE
            ? { authorizationParams: { audience: AUDIENCE } }
            : {};
          const token = await getAccessTokenSilently(tokenParams);
          config.headers.Authorization = `Bearer ${token}`;
        } catch (err) {
          console.warn("No se pudo obtener token Auth0:", err?.error || err?.message);
          // Si falla obtener el token, disparar modal directamente
          trigger();
        }
        return config;
      });
    }

    // Response — mostrar modal en 401 o 403 "Not authenticated"
    responseInterceptorRef.current = api.interceptors.response.use(
      (response) => response,
      (error) => {
        const status = error.response?.status;
        const detail = error.response?.data?.detail || "";

        const isAuthError =
          status === 401 ||
          (status === 403 && detail.toLowerCase().includes("not authenticated"));

        if (isAuthError) {
          trigger();
        }

        return Promise.reject(error);
      }
    );

    return () => {
      if (requestInterceptorRef.current !== null) {
        api.interceptors.request.eject(requestInterceptorRef.current);
      }
      if (responseInterceptorRef.current !== null) {
        api.interceptors.response.eject(responseInterceptorRef.current);
      }
    };
  }, [isAuthenticated, isLoading, getAccessTokenSilently, trigger]);

  return children;
}