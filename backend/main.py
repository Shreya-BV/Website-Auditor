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
    # Startup database connection
    connect_db()
    yield
    # Shutdown database connection
    close_db()

app = FastAPI(
    title="Website Auditor API",
    description="Backend service for scanning websites and logging statistics.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://website-auditor-two.vercel.app",
        "http://localhost:4200"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming {request.method} request to {request.url.path}")
    response = await call_next(request)
    logger.info(f"Completed {request.method} {request.url.path} with status {response.status_code}")
    return response

# Mount API router
# Mount API routers
app.include_router(api_router, prefix="/api")
app.include_router(audit_router, prefix="/api/audit")
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
@app.get("/")
async def root():
    return {"message": "Welcome to the Website Auditor API. The service is running."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
