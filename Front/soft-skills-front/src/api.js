// api.js
// Propósito: Instancia global de axios. El token se inyecta desde AxiosInterceptor
//            una sola vez cuando Auth0 termina de cargar.
// En los componentes: import { api } from "../../api"  (sin hook)
// Fecha: 2026-05-08

import axios from "axios";

export const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: { "Content-Type": "application/json" },
});