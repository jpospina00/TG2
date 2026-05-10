# utils/rate_limit.py
# Propósito: Configuración de rate limiting con slowapi.
#            Protege endpoints costosos (IA, diagnóstico) de abuso.
# Uso: importar `limiter` y usar @limiter.limit("N/period") en endpoints.
#      Registrar el handler en main.py con register_rate_limiter(app).
# Fecha: 2026-05-08

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Identifica al usuario por IP (funciona sin auth y con auth)
# En producción con Render, el IP real llega en X-Forwarded-For
def _get_identifier(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)

limiter = Limiter(key_func=_get_identifier)


def register_rate_limiter(app: FastAPI) -> None:
    """Registra el state y el handler de rate limit en la app FastAPI."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)