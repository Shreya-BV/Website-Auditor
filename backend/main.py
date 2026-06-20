import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database.mongodb import connect_db, close_db
from app.routes.api import router as api_router

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
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the Website Auditor API. The service is running."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
