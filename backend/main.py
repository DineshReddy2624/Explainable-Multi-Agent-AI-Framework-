import inspect
import starlette.routing

_orig_router_init = starlette.routing.Router.__init__
def _patched_router_init(self, *args, **kwargs):
    sig = inspect.signature(_orig_router_init)
    valid_params = sig.parameters.keys()
    if 'kwargs' not in valid_params:
        kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
    _orig_router_init(self, *args, **kwargs)

starlette.routing.Router.__init__ = _patched_router_init

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from core.config import settings
from core.database import engine, Base
import models
from core.exceptions import BaseAppException, app_exception_handler

# Create database tables automatically
Base.metadata.create_all(bind=engine)

# Auto-migrate schema for missing columns if database pre-existed
from sqlalchemy import text
with engine.connect() as conn:
    # Users table new columns
    for col, col_type in [("avatar_url", "VARCHAR"), ("google_id", "VARCHAR"), ("auth_provider", "VARCHAR")]:
        try:
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type};"))
            conn.commit()
        except Exception:
            pass
    # DatasetMetadata table new columns
    for col, col_type in [
        ("original_file_path", "VARCHAR"),
        ("saved_at", "DATETIME"),
        ("workflow_bundle", "JSON"),
    ]:
        try:
            conn.execute(text(f"ALTER TABLE dataset_metadata ADD COLUMN {col} {col_type};"))
            conn.commit()
        except Exception:
            pass



from api import (
    auth, upload, profiling, issues, anomalies, monitoring,
    correction, explainability, chatbot, chat, rules,
    history, reports, export, jobs, documents, generated_code
)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
# NOTE: allow_origins=["*"] is INCOMPATIBLE with allow_credentials=True — browsers block it.
# Always use explicit origin lists when credentials (cookies/JWT) are involved.
origins = settings.allowed_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import uuid
import time
import socket
import logging
from fastapi import Request, Response, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)

# Request Correlation ID Middleware
@app.middleware("http")
async def correlation_id_and_security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000, 2)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-MS"] = str(process_time)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Exception handlers
app.add_exception_handler(BaseAppException, app_exception_handler)

@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[RequestID: {req_id}] Unhandled Exception: {str(exc)}", exc_info=True)

    if settings.ENVIRONMENT.lower() == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"An unexpected internal error occurred. Reference ID: {req_id}"}
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal Server Error: {str(exc)}", "request_id": req_id}
    )

# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth Compatibility"])
app.include_router(auth.router, prefix="/auth", tags=["Auth Direct"])
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/upload", tags=["Upload"])
app.include_router(profiling.router, prefix=f"{settings.API_V1_STR}/profiling", tags=["Profiling"])
app.include_router(issues.router, prefix=f"{settings.API_V1_STR}/issues", tags=["Issues"])
app.include_router(anomalies.router, prefix=f"{settings.API_V1_STR}/anomalies", tags=["Anomalies"])
app.include_router(monitoring.router, prefix=f"{settings.API_V1_STR}/monitoring", tags=["Monitoring"])
app.include_router(correction.router, prefix=f"{settings.API_V1_STR}/correction", tags=["Correction"])
app.include_router(explainability.router, prefix=f"{settings.API_V1_STR}/explainability", tags=["Explainability"])
app.include_router(explainability.router, prefix=f"{settings.API_V1_STR}/explainable-ai", tags=["Explainable AI"])

app.include_router(chatbot.router, prefix=f"{settings.API_V1_STR}/chatbot", tags=["Chatbot"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(rules.router, prefix=f"{settings.API_V1_STR}/rules", tags=["Rules"])
app.include_router(history.router, prefix=f"{settings.API_V1_STR}/history", tags=["History"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])
app.include_router(export.router, prefix=f"{settings.API_V1_STR}/export", tags=["Export"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Jobs"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
app.include_router(generated_code.router, prefix=f"{settings.API_V1_STR}/code", tags=["Generated Code"])



@app.get("/")
def root():
    return {"message": "Explainable Multi-Agent AI Data Quality Platform API", "environment": settings.ENVIRONMENT}

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT, "version": "1.0.0"}

@app.get("/health/live")
def liveness_probe():
    """Lightweight liveness probe for Kubernetes / Docker container checks."""
    return {"status": "live", "timestamp": time.time()}

@app.get("/health/ready")
def readiness_probe():
    """Readiness probe checking database and Redis dependencies."""
    from core.database import SessionLocal
    db_status = "healthy"
    redis_status = "healthy"
    is_ready = True

    # 1. Check Database Ping
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        is_ready = False

    # 2. Check Redis Host Connection
    try:
        # Parse host/port from REDIS_URL or test socket connection
        redis_host = "localhost"
        redis_port = 6379
        if "redis://" in settings.REDIS_URL:
            raw_hp = settings.REDIS_URL.split("redis://")[1].split("/")[0]
            if ":" in raw_hp:
                redis_host, redis_port = raw_hp.split(":")[0], int(raw_hp.split(":")[1])
            else:
                redis_host = raw_hp
        s = socket.create_connection((redis_host, redis_port), timeout=0.5)
        s.close()
    except Exception:
        redis_status = "unavailable (local fallback active)"

    payload = {
        "status": "ready" if is_ready else "not_ready",
        "database": db_status,
        "redis": redis_status,
        "environment": settings.ENVIRONMENT
    }

    if not is_ready:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)
    return payload

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
