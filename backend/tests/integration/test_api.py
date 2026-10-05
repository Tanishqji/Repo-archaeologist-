import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "repo-archaeologist"

@pytest.mark.asyncio
async def test_limits_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/limits")
        assert response.status_code == 200
        data = response.json()
        assert "rate_limits" in data
        assert "budgets" in data

@pytest.mark.asyncio
async def test_analyze_invalid_url():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/analyze", json={"url": "https://gitlab.com/invalid/repo"})
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_URL"

@pytest.mark.asyncio
async def test_analyze_and_get_job(monkeypatch):
    async def mock_run_analysis(*args, **kwargs):
        pass

    monkeypatch.setattr("app.api.analyze.run_analysis_pipeline", mock_run_analysis)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # POST valid repo
        post_resp = await ac.post("/api/analyze", json={"url": "fastapi/fastapi"})
        assert post_resp.status_code == 200
        data = post_resp.json()
        assert "job_id" in data
        job_id = data["job_id"]

        # GET job status
        get_resp = await ac.get(f"/api/jobs/{job_id}")
        assert get_resp.status_code == 200
        job_data = get_resp.json()
        assert job_data["job_id"] == job_id
        assert job_data["repo_key"] == "fastapi/fastapi"
