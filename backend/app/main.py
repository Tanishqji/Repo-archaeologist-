import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import analyze, chat, health, jobs
from app.config import get_settings
from app.core.errors import AppError, app_error_handler, generic_exception_handler

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)

logger = logging.getLogger("repo-archaeologist")

settings = get_settings()

app = FastAPI(
    title="Repo Archaeologist API",
    description="Deterministic & Grounded AI GitHub Repository Analyzer",
    version="0.1.0",
)

# CORS Configuration
origins = [
    settings.frontend_origin,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
if "," in settings.frontend_origin:
    origins.extend([o.strip() for o in settings.frontend_origin.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if settings.frontend_origin != "*" else ["*"],
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Error Handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register Routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(analyze.router, prefix="/api", tags=["Analyze"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Repo Archaeologist API. See /docs for Swagger UI.",
        "health": "/api/health",
    }
