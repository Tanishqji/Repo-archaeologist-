import pytest
from app.core.cache import CacheBackend, get_cache_key
from app.core.errors import AppError, ErrorCode
from app.core.jobs import JobManager, JobStage
from app.core.rate_limit import RateLimiter

@pytest.mark.asyncio
async def test_cache_set_and_get(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_cache.db")
    monkeypatch.setenv("SQLITE_DB_PATH", test_db)
    cache = CacheBackend()

    key = get_cache_key("testowner", "testrepo", "sha123")
    data = {"summary": "Cached report", "stars": 99}

    await cache.set(key, data, ttl_hours=1)
    retrieved = await cache.get(key)
    assert retrieved is not None
    assert retrieved["summary"] == "Cached report"
    assert retrieved["stars"] == 99

def test_job_deduplication_and_lifecycle(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_jobs.db")
    monkeypatch.setenv("SQLITE_DB_PATH", test_db)
    jm = JobManager()

    repo_key = "owner/repo@sha123"
    job1, is_new1 = jm.create_or_join_job(repo_key)
    assert is_new1 is True

    # Duplicate request for same repo in flight
    job2, is_new2 = jm.create_or_join_job(repo_key)
    assert is_new2 is False
    assert job1.job_id == job2.job_id

    # Advance stage
    jm.update_stage(job1.job_id, JobStage.SCANNING)
    updated = jm.get_job(job1.job_id)
    assert updated.stage == JobStage.SCANNING
    assert updated.progress_pct == 60

    # Complete job
    jm.complete_job(job1.job_id, {"summary": "Done"})
    completed = jm.get_job(job1.job_id)
    assert completed.status == "completed"
    assert completed.stage == JobStage.DONE

def test_rate_limiter(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ANALYZE_PER_HOUR", "2")
    from app.config import get_settings
    get_settings.cache_clear()
    limiter = RateLimiter()

    # Request 1 & 2 succeed
    limiter.check("1.2.3.4", action="analyze")
    limiter.check("1.2.3.4", action="analyze")

    # Request 3 fails with RATE_LIMITED
    with pytest.raises(AppError) as exc_info:
        limiter.check("1.2.3.4", action="analyze")
    assert exc_info.value.code == ErrorCode.RATE_LIMITED
    assert "retry_after_seconds" in exc_info.value.details
    get_settings.cache_clear()
