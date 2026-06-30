import os
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn
from dotenv import load_dotenv

load_dotenv()


from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.database.mongodb import connect_db, close_db
from app.routes.api import router as api_router
from app.routes.audit import router as audit_router
from app.routes.auth import router as auth_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== STARTUP LOGS ===")
    logger.info("Backend Version: 1.0.0")
    logger.info(f"Current Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    logger.info(f"Port Number: {os.environ.get('PORT', '8000')}")
    
    # Playwright Status
    try:
        import playwright
        logger.info("Playwright Status: Installed and ready")
    except Exception as e:
        logger.error(f"Playwright Status: Error - {e}", exc_info=True)
        
    # Startup database connection
    await connect_db()
    logger.info("MongoDB Connection: Initialization called")
    
    # SMTP Validation (Phase 2)
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    from_email = os.environ.get("FROM_EMAIL")
    jwt_secret = os.environ.get("JWT_SECRET")
    frontend_url = os.environ.get("FRONTEND_URL")
    
    missing_vars = []
    if not smtp_host: missing_vars.append("SMTP_HOST")
    if not smtp_port: missing_vars.append("SMTP_PORT")
    if not smtp_username: missing_vars.append("SMTP_USERNAME")
    if not smtp_password: missing_vars.append("SMTP_PASSWORD")
    if not from_email: missing_vars.append("FROM_EMAIL")
    if not jwt_secret: missing_vars.append("JWT_SECRET")
    if not frontend_url: missing_vars.append("FRONTEND_URL")
    
    if missing_vars:
        error_msg = f"Missing required configuration variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    logger.info("SMTP_HOST loaded")
    logger.info("SMTP_PORT loaded")
    logger.info("SMTP_USERNAME loaded")
    logger.info(f"SMTP_PASSWORD present: {bool(smtp_password)}")
    logger.info("FROM_EMAIL loaded")

    yield
    # Shutdown database connection
    close_db()

app = FastAPI(
    title="Website Auditor API",
    description="Backend service for scanning websites and logging statistics.",
    version="1.0.0",
    lifespan=lifespan
)

# Setup allowed origins dynamically
frontend_url_env = os.environ.get("FRONTEND_URL")
allowed_origins = [
    "https://website-auditor-two.vercel.app",
    "https://website-auditor-amok17kl4-shreya-bvs-projects.vercel.app",
    "http://localhost:4200",
    "http://localhost:3000"
]
if frontend_url_env and frontend_url_env not in allowed_origins:
    allowed_origins.append(frontend_url_env)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming {request.method} request to {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Completed {request.method} {request.url.path} with status {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Unhandled Exception during {request.method} {request.url.path}: {e}", exc_info=True)
        raise

# Mount API router
# Mount API routers
app.include_router(api_router, prefix="/api")
app.include_router(audit_router, prefix="/api/audit")
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Website Auditor API. The service is running.", "status": "ok"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mongodb": "connected"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
