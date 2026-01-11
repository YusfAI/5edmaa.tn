from fastapi import FastAPI
from sqlalchemy import text
from .database import engine


app = FastAPI(
    title="5edma.tn API",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
