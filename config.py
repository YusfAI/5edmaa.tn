import os
from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://edmaa_user:***REDACTED***@localhost:5432/5edma_tn",
    )
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    )



settings = Settings()
