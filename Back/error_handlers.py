# error_handlers.py
# Propósito: Manejadores globales de excepciones — ningún error interno llega al cliente.
# Se registran en main.py con app.add_exception_handler(...)
# Fecha: 2026-05-08

import traceback
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# ── Mensajes genéricos por código de estado ───────────────────────────────────
# El cliente recibe esto; el detalle real va solo al log del servidor.
_STATUS_MESSAGES: dict[int, str] = {
    400: "Solicitud inválida.",
    401: "No autorizado.",
    403: "No tenés permiso para realizar esta acción.",
    404: "El recurso solicitado no existe.",
    405: "Método no permitido.",
    409: "Conflicto con el estado actual del recurso.",
    422: "Los datos enviados no tienen el formato esperado.",
    429: "Demasiadas solicitudes. Intentá más tarde.",
    500: "Ocurrió un error interno. Por favor intentá de nuevo.",
    502: "Error de comunicación con un servicio externo.",
    503: "Servicio no disponible temporalmente.",
}


def _safe_message(status_code: int, fallback: str | None = None) -> str:
    return _STATUS_MESSAGES.get(status_code, fallback or "Error inesperado.")


# ── 1. HTTPException (404, 401, 403, etc.) ────────────────────────────────────
# FastAPI las lanza internamente (ej: ruta no encontrada) o desde los endpoints.
# Dejamos pasar los mensajes explícitos de 4xx porque son intencionales
# (ej: "Conversation not found"), pero nunca exponemos errores 5xx con detalle.
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code >= 500:
        logger.error(
            "HTTPException 5xx | %s %s | status=%s | detail=%s",
            request.method, request.url.path, exc.status_code, exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": _safe_message(exc.status_code)},
        )

    # 4xx: el mensaje puede ser útil para el cliente (404, 409, etc.)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail or _safe_message(exc.status_code)},
    )


# ── 2. ValidationError (422) — body/query params mal formados ─────────────────
# Por defecto FastAPI devuelve el detalle completo de Pydantic, que puede incluir
# valores del request. Solo dejamos pasar la ubicación y el tipo del error.
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    safe_errors = [
        {"field": " → ".join(str(loc) for loc in err["loc"]), "issue": err["type"]}
        for err in exc.errors()
    ]
    logger.warning(
        "ValidationError | %s %s | errors=%s",
        request.method, request.url.path, safe_errors,
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Los datos enviados no tienen el formato esperado.",
            "errors": safe_errors,
        },
    )


# ── 3. Cualquier excepción no capturada (500) ─────────────────────────────────
# Captura todo lo que no fue manejado explícitamente: errores de BD,
# excepciones de librerías externas, bugs, etc.
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception | %s %s\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),   # stack trace completo al log, nunca al cliente
    )
    return JSONResponse(
        status_code=500,
        content={"detail": _safe_message(500)},
    )


# ── Función de registro — se llama desde main.py ─────────────────────────────
def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los manejadores de excepciones en la app FastAPI."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)