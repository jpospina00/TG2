import os
from pathlib import Path
from pydantic_settings import BaseSettings

top_dir = Path(__file__).resolve().parents[0]
db_dir = top_dir / "db"
db_name = "tesis.db"
db_path = str(db_dir / db_name)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Soft Skills Trainer"
    DESCRIPTION: str = "AI-powered soft skills training backend"
    VERSION: str = "0.1"
    DATABASE_URI: str = f"sqlite:///{db_path}"
    DATABASE_URL: str = ""
    GROQ_API_KEYS: str = ""
    AUTH0_DOMAIN: str = "dev-dc5eye6w4usbnja8.us.auth0.com"
    AUTH0_AUDIENCE: str = ""  # se setea en .env — ej: https://tesis-backend-b7ww.onrender.com
    GEMINI_API_KEY: str = ""  # para LLM-as-a-Judge en tests — gratis en aistudio.google.com
    OPENROUTER_API_KEY: str = ""  # para LLM-as-a-Judge en tests — gratis en openrouter.com
    @property
    def groq_keys_list(self) -> list[str]:
        return [k.strip() for k in self.GROQ_API_KEYS.split(",") if k.strip()]

    @property
    def active_database_uri(self) -> str:
        return self.DATABASE_URL if self.DATABASE_URL else self.DATABASE_URI

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()