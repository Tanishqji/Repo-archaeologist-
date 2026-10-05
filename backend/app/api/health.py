from fastapi import APIRouter
from app.config import get_settings

router = APIRouter()

@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "service": "repo-archaeologist",
        "llm_provider": settings.llm_provider,
        "llm_configured": bool(settings.gemini_api_key or settings.anthropic_api_key or settings.openai_api_key),
        "github_token_configured": bool(settings.github_token),
    }

@router.get("/limits")
async def get_limits():
    settings = get_settings()
    return {
        "rate_limits": {
            "analyze_per_hour": settings.rate_limit_analyze_per_hour,
            "chat_per_hour": settings.rate_limit_chat_per_hour,
        },
        "budgets": {
            "max_files_read": settings.max_files_read,
            "max_file_bytes": settings.max_file_bytes,
            "context_token_budget": settings.context_token_budget,
            "analysis_timeout_seconds": settings.analysis_timeout_seconds,
        },
    }
