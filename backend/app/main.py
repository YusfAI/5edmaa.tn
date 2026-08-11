import logging
import time
import uuid

from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .database import engine
from .rate_limit import limiter
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

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("5edma")

app = FastAPI(
    title="5edma.tn API",
    version="1.0.0",
    # Hide interactive docs in production to reduce information disclosure —
    # set ENVIRONMENT=development (the default) to keep them available.
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Compresses JSON/text responses above 500 bytes — cheap bandwidth win for
# list endpoints (jobs, services) with no code changes required elsewhere.
app.add_middleware(GZipMiddleware, minimum_size=500)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Tags every request with an id (for log correlation), times it, and
    adds baseline security headers to every response."""
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"

    logger.info(
        "%s %s -> %s (%.1fms) [%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Keeps FastAPI's normal {"detail": ...} shape (nothing else here
    depends on this handler existing) but guarantees it even for errors
    raised outside route handlers (e.g. from middleware)."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # exc.errors() can include raw exception objects (e.g. a field_validator's
    # ValueError) in "ctx" — not JSON-serializable as-is, so run it through
    # jsonable_encoder (which knows how to stringify what json.dumps can't).
    detail = jsonable_encoder(exc.errors()) if settings.debug else "Invalid request"
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Never leak stack traces / internal details to clients. Full details
    still go to the server log via logger.exception below."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
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
        logger.error("Health check failed: %s", e)
        return JSONResponse(status_code=503, content={"status": "error"})


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
