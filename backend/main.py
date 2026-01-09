# COMPLETE main.py with bookings!

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.database import get_db, engine, Base
from models.user import User
from routes.auth import router as auth_router
from routes.services import router as services_router
from routes.bookings import router as bookings_router  # NEW: ADD THIS
from routes import services

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="5edmaa.tn API",
    description="Service Marketplace Platform - Tunisia",
    version="1.0.0"
)

# Include ALL routers
app.include_router(auth_router)
app.include_router(services_router)
app.include_router(bookings_router)  # NEW: ADD THIS

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
