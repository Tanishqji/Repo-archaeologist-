import asyncio
import json
import logging
import sqlite3
import time
import uuid
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from app.config import get_settings
from app.core.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)

class JobStage:
    QUEUED = "queued"
    VALIDATING = "validating"
    FETCHING = "fetching"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    DIAGRAMMING = "diagramming"
    DONE = "done"
    FAILED = "failed"

STAGE_PROGRESS = {
    JobStage.QUEUED: 5,
    JobStage.VALIDATING: 15,
    JobStage.FETCHING: 35,
    JobStage.SCANNING: 60,
    JobStage.ANALYZING: 80,
    JobStage.DIAGRAMMING: 95,
    JobStage.DONE: 100,
    JobStage.FAILED: 100,
}

class JobRecord(BaseModel):
    job_id: str
    repo_key: str
    status: str = "running"  # running | completed | failed
    stage: str = JobStage.QUEUED
    progress_pct: int = 5
    report: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

class JobManager:
    def __init__(self):
        self.settings = get_settings()
        self._jobs: Dict[str, JobRecord] = {}
        self._inflight: Dict[str, str] = {}  # repo_key -> job_id
        self._semaphore = asyncio.Semaphore(3)  # Global concurrency limit
        self.db_path = self.settings.sqlite_db_path
        self._init_sqlite()

    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    repo_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    progress_pct INTEGER NOT NULL,
                    report TEXT,
                    error TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            # Reap zombie jobs on startup (mark running jobs as failed)
            conn.execute(
                "UPDATE jobs SET status = 'failed', stage = 'failed', error = ? WHERE status = 'running'",
                (json.dumps({"code": ErrorCode.INTERNAL, "message": "Server restarted during analysis. Please retry.", "retryable": True}),),
            )
            conn.commit()

    def create_or_join_job(self, repo_key: str) -> Tuple[JobRecord, bool]:
        """
        Deduplicates in-flight jobs. If a job for repo_key is already running, returns (job, is_new=False).
        Otherwise creates a new job and returns (job, is_new=True).
        """
        # Check active in-flight job
        if repo_key in self._inflight:
            existing_job_id = self._inflight[repo_key]
            if existing_job_id in self._jobs and self._jobs[existing_job_id].status == "running":
                return self._jobs[existing_job_id], False

        # Create new job
        job_id = str(uuid.uuid4())
        job = JobRecord(job_id=job_id, repo_key=repo_key)
        self._jobs[job_id] = job
        self._inflight[repo_key] = job_id
        self._persist_job(job)
        return job, True

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        if job_id in self._jobs:
            return self._jobs[job_id]
        # Query SQLite
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT repo_key, status, stage, progress_pct, report, error, created_at, updated_at FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                repo_key, status, stage, progress_pct, report_str, error_str, c_at, u_at = row
                job = JobRecord(
                    job_id=job_id,
                    repo_key=repo_key,
                    status=status,
                    stage=stage,
                    progress_pct=progress_pct,
                    report=json.loads(report_str) if report_str else None,
                    error=json.loads(error_str) if error_str else None,
                    created_at=c_at,
                    updated_at=u_at,
                )
                self._jobs[job_id] = job
                return job
        return None

    def update_stage(self, job_id: str, stage: str) -> None:
        job = self.get_job(job_id)
        if job:
            job.stage = stage
            job.progress_pct = STAGE_PROGRESS.get(stage, job.progress_pct)
            job.updated_at = time.time()
            self._jobs[job_id] = job
            self._persist_job(job)

    def complete_job(self, job_id: str, report: Dict[str, Any]) -> None:
        job = self.get_job(job_id)
        if job:
            job.status = "completed"
            job.stage = JobStage.DONE
            job.progress_pct = 100
            job.report = report
            job.updated_at = time.time()
            self._jobs[job_id] = job
            self._persist_job(job)
            if job.repo_key in self._inflight and self._inflight[job.repo_key] == job_id:
                del self._inflight[job.repo_key]

    def fail_job(self, job_id: str, error: Dict[str, Any]) -> None:
        job = self.get_job(job_id)
        if job:
            job.status = "failed"
            job.stage = JobStage.FAILED
            job.progress_pct = 100
            job.error = error
            job.updated_at = time.time()
            self._jobs[job_id] = job
            self._persist_job(job)
            if job.repo_key in self._inflight and self._inflight[job.repo_key] == job_id:
                del self._inflight[job.repo_key]

    def _persist_job(self, job: JobRecord) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO jobs 
                    (job_id, repo_key, status, stage, progress_pct, report, error, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.job_id,
                        job.repo_key,
                        job.status,
                        job.stage,
                        job.progress_pct,
                        json.dumps(job.report) if job.report else None,
                        json.dumps(job.error) if job.error else None,
                        job.created_at,
                        job.updated_at,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to persist job {job.job_id}: {e}")
