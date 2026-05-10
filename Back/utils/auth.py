# utils/auth.py
# Propósito: Verificación de JWT de Auth0 como dependencia de FastAPI.
#            Cualquier endpoint que use Depends(get_current_user) queda protegido.
# Fecha: 2026-05-08

import httpx
import logging
from functools import lru_cache
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from database import get_session
from config import settings

logger = logging.getLogger(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────
# Estos valores deben estar en el .env del backend
AUTH0_DOMAIN   = settings.AUTH0_DOMAIN    # ej: dev-dc5eye6w4usbnja8.us.auth0.com
AUTH0_AUDIENCE = settings.AUTH0_AUDIENCE  # ej: https://tesis-backend-b7ww.onrender.com
ALGORITHMS     = ["RS256"]

bearer_scheme = HTTPBearer()


# ── JWKS: claves públicas de Auth0 (cacheadas para no pedirlas en cada request) ─
@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _get_rsa_key(token: str) -> dict | None:
    """Extrae la clave pública RSA correspondiente al kid del token."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        return None

    jwks = _get_jwks()
    for key in jwks.get("keys", []):
        if key["kid"] == header.get("kid"):
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n":   key["n"],
                "e":   key["e"],
            }
    return None


# ── Dependencia principal ──────────────────────────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Verifica el JWT de Auth0 y retorna el payload decodificado.
    Uso: añadir `current_user: dict = Depends(get_current_user)` a cualquier endpoint.
    El payload contiene: sub (auth0_id), email, nombre, etc.
    """
    token = credentials.credentials
    rsa_key = _get_rsa_key(token)

    if not rsa_key:
        logger.warning("JWT rechazado: kid no encontrado en JWKS")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT rechazado: token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.warning("JWT rechazado: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_auth0_id(current_user: dict = Depends(get_current_user)) -> str:
    """Shortcut que retorna solo el auth0_id (campo 'sub') del token verificado."""
    return current_user["sub"]


def get_db_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Resuelve el usuario de la BD a partir del JWT.
    Usar como dependencia en cualquier endpoint que necesite el user_id real.
    Elimina la necesidad de que el cliente mande user_id en el body.

    Uso:
        @router.post("/something")
        def my_endpoint(db_user: User = Depends(get_db_user)):
            # db_user.id es el user_id real, verificado desde el token
    """
    from sqlmodel import select
    from model.user import User

    auth0_id = current_user["sub"]
    user = db.exec(select(User).where(User.auth0_id == auth0_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )
    return user