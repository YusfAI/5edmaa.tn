import os

from dotenv import load_dotenv
from pydantic import BaseModel

# Load backend/.env (never committed — see .env.example for the required keys)
load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy backend/.env.example to backend/.env and fill it in."
        )
    return value


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    database_url: str = _require_env("DATABASE_URL")
    secret_key: str = _require_env("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    )
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")

    # environment: "development" (default) or "production" — gates interactive
    # API docs, SQL echo logging, and other dev-only conveniences.
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true" if environment != "production" else "false").lower() == "true"

    # Comma-separated list of allowed CORS origins, e.g.
    # "https://5edmaa.tn,https://www.5edmaa.tn". Falls back to local dev ports.
    allowed_origins: list[str] = _split_csv(
        os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
        )
    )

    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
