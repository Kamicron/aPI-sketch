from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

BACK_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Lu depuis les variables d'environnement, puis back/.env s'il existe."""

    model_config = SettingsConfigDict(env_file=BACK_DIR / ".env", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "apisketch"
    db_username: str = "apisketch"
    db_password: str = ""
    database_url: str = ""

    jwt_secret: str = "dev-secret-change-me"
    jwt_ttl_days: int = 30
    invite_ttl_days: int = 14

    cors_allowed_origins: str = "http://localhost:5173"
    media_dir: str = "./media"

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        # Identifiants encodés : un @ : / # dans le mot de passe casserait l'URL.
        user = quote(self.db_username, safe="")
        password = quote(self.db_password, safe="")
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{quote(self.db_name, safe='')}?charset=utf8mb4"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
