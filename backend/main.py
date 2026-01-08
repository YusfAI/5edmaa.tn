from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.database import get_db
from models.user import User

app = FastAPI(
    title="5edmaa.tn API",
    description="Service Marketplace Platform - Tunisia",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to 5edmaa.tn API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/api/users/count")
def get_users_count(db: Session = Depends(get_db)):
    count = db.query(User).count()
    return {
        "total_users": count
    }
