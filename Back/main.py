from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import create_db_and_tables
from utils.logger import logger_config
from web import api as api_routes
from error_handlers import register_exception_handlers
from utils.rate_limit import register_rate_limiter

logger = logger_config(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    logger.info("startup: triggered")

    yield

    logger.info("shutdown: triggered")


# En producción se deshabilitan los docs automáticos (/docs y /redoc)
# para no exponer la estructura de la API públicamente.
is_production = not settings.active_database_uri.startswith("sqlite")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# Solo se permiten los orígenes conocidos.
# Nunca usar "*" en producción — permite que cualquier sitio haga requests a la API.
ALLOWED_ORIGINS = [
    "https://soft-skills-front.vercel.app",  # frontend en producción
    "http://localhost:3000",                  # desarrollo local React
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Manejadores globales de excepciones — ningún error interno llega al cliente
register_exception_handlers(app)
# Rate limiting — protege endpoints costosos de abuso
register_rate_limiter(app)

app.include_router(api_routes)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)