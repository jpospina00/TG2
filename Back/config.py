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
    GROQ_API_KEYS: str = ""

    @property
    def groq_keys_list(self) -> list[str]:
        return [k.strip() for k in self.GROQ_API_KEYS.split(",") if k.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()