from fastapi import APIRouter
from app.api.analyze import job_manager
from app.core.errors import AppError, ErrorCode

router = APIRouter()

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise AppError(
            code=ErrorCode.REPO_NOT_FOUND,
            message=f"Job '{job_id}' not found.",
            status_code=404,
            retryable=False,
        )

    return {
        "job_id": job.job_id,
        "repo_key": job.repo_key,
        "status": job.status,
        "stage": job.stage,
        "progress_pct": job.progress_pct,
        "report": job.report,
        "error": job.error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
