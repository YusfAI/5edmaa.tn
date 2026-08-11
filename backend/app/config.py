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


class Settings(BaseModel):
    database_url: str = _require_env("DATABASE_URL")
    secret_key: str = _require_env("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    )
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")


settings = Settings()
