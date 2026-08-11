from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .database import engine
from .auth import router as auth_router, get_current_admin
from .user import User
from .admin import router as admin_router
from .jobs import router as jobs_router
from .service import router as services_router
from .bookings import router as bookings_router
from .reviews import router as reviews_router
from .wallet import router as wallet_router
from .chat import router as chat_router
from .ai import router as ai_router
from .subscriptions import router as subscriptions_router

app = FastAPI(
    title="5edma.tn API",
    version="0.1.0",
)



origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # includes OPTIONS, GET, POST, etc.
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router)
app.include_router(jobs_router)
app.include_router(services_router)
app.include_router(bookings_router) 
app.include_router(reviews_router) 
app.include_router(wallet_router) 
app.include_router(chat_router) 
app.include_router(ai_router)
app.include_router(subscriptions_router) 

@app.get("/health")
async def health_check():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/admin/me")
async def read_admin_me(current_admin: User = Depends(get_current_admin)):
    return {
        "id": current_admin.id,
        "email": current_admin.email,
        "role": current_admin.role.value,
    }


# Worker/client verification endpoints (pending/verify/reject) live in admin.py
# (app.include_router(admin_router) above) — they use WorkerProfile/ClientProfile.status
# instead of the plain `verified` boolean, so don't redefine simpler versions here.
