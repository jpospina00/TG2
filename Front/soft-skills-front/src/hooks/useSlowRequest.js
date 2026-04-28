// useSlowRequest.js
// Propósito: Detecta peticiones lentas y muestra aviso al usuario
// Fecha: 2026-04-26

import { useState, useRef, useCallback } from "react";

export function useSlowRequest(thresholdMs = 2000) {
  const [isSlow, setIsSlow] = useState(false);
  const timerRef = useRef(null);

  const start = useCallback(() => {
    setIsSlow(false);
    timerRef.current = setTimeout(() => setIsSlow(true), thresholdMs);
  }, [thresholdMs]);

  const stop = useCallback(() => {
    clearTimeout(timerRef.current);
    setIsSlow(false);
  }, []);

  return { isSlow, start, stop };
}