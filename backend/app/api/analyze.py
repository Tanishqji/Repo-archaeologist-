import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel, Field
from app.analyzer.scanner import run_static_analysis
from app.chat.chunker import chunk_repository
from app.chat.store import VectorStore
from app.config import get_settings
from app.context.builder import build_llm_context
from app.core.cache import CacheBackend, get_cache_key
from app.core.errors import AppError, ErrorCode
from app.core.jobs import JobManager, JobStage
from app.core.rate_limit import RateLimiter
from app.core.validators import validate_github_url
from app.github.fetcher import RepoFetcher
from app.llm.gemini import GeminiProvider
from app.llm.prompts import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT_TEMPLATE
from app.report.assembler import assemble_final_report
from app.report.schemas import AnalysisReport

logger = logging.getLogger(__name__)

router = APIRouter()

# Global singletons
cache = CacheBackend()
job_manager = JobManager()
rate_limiter = RateLimiter()
vector_store = VectorStore()
repo_fetcher = RepoFetcher()

class AnalyzeRequest(BaseModel):
    url: str
    force_refresh: bool = False

async def run_analysis_pipeline(
    job_id: str,
    target,
    force_refresh: bool,
):
    settings = get_settings()
    try:
        # Stage 1: Validating
        job_manager.update_stage(job_id, JobStage.VALIDATING)

        # Stage 2: Fetching
        job_manager.update_stage(job_id, JobStage.FETCHING)
        repo = await repo_fetcher.fetch(target)

        cache_key = get_cache_key(
            owner=repo.metadata.owner,
            repo=repo.metadata.name,
            sha=repo.metadata.commit_sha,
            prompt_version=settings.prompt_version,
        )

        # Check cache if not forcing refresh
        if not force_refresh:
            cached_report = await cache.get(cache_key)
            if cached_report:
                job_manager.complete_job(job_id, cached_report)
                return

        # Fetch key files content for static analysis
        # Always fetch manifests, README, entry points
        key_manifests = [
            "package.json", "requirements.txt", "pyproject.toml",
            "go.mod", "Cargo.toml", "pom.xml", "Dockerfile",
            "docker-compose.yml", "README.md", "readme.md",
            ".env.example", ".env.sample",
        ]
        files_to_read = []
        for item in repo.tree:
            item_path = item.path
            for m in key_manifests:
                if item_path.lower().endswith(m.lower()) or item_path.lower() == m.lower():
                    files_to_read.append(item_path)
            if item_path in ("main.py", "app.py", "server.js", "index.js", "src/index.js", "src/main.tsx"):
                files_to_read.append(item_path)

        # Dedup files to read up to limit
        files_to_read = list(dict.fromkeys(files_to_read))[: settings.max_files_read]
        for path in files_to_read:
            content = await repo_fetcher.fetch_file_content(target, repo.metadata.commit_sha, path)
            if content is not None:
                repo.files[path] = content

        # Stage 3: Scanning (deterministic static analysis)
        job_manager.update_stage(job_id, JobStage.SCANNING)
        facts = run_static_analysis(repo)

        # Fetch additional files identified by imports/key files if not loaded yet
        for kf in facts.key_files[:20]:
            if kf.path not in repo.files and len(repo.files) < settings.max_files_read:
                c = await repo_fetcher.fetch_file_content(target, repo.metadata.commit_sha, kf.path)
                if c is not None:
                    repo.files[kf.path] = c

        # Re-run static analysis with fully populated key files
        facts = run_static_analysis(repo)

        # Stage 4: Analyzing (context build + LLM)
        job_manager.update_stage(job_id, JobStage.ANALYZING)
        context_bundle = build_llm_context(repo, facts)

        llm_output = None
        if settings.gemini_api_key:
            try:
                llm = GeminiProvider()
                user_prompt = ANALYSIS_USER_PROMPT_TEMPLATE.format(
                    repo_full_name=target.full_name,
                    context=context_bundle.prompt_context,
                )
                llm_output = await llm.generate_json(
                    system_prompt=ANALYSIS_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    schema=AnalysisReport,
                )
            except Exception as e:
                logger.warning(f"LLM analysis failed, falling back to degraded facts-only mode: {e}")

        # Stage 5: Diagramming + Assembly
        job_manager.update_stage(job_id, JobStage.DIAGRAMMING)
        report = assemble_final_report(
            repo=repo,
            facts=facts,
            llm_output=llm_output,
            warnings=context_bundle.secrets_detected_files,
        )

        report_dict = report.model_dump()

        # Save to cache
        await cache.set(cache_key, report_dict)

        # Index chunks in vector store for chat
        try:
            chunks = chunk_repository(repo.files)
            await vector_store.index_chunks(
                owner=repo.metadata.owner,
                repo=repo.metadata.name,
                sha=repo.metadata.commit_sha,
                chunks=chunks,
            )
        except Exception as e:
            logger.warning(f"Vector indexing failed: {e}")

        # Complete job
        job_manager.complete_job(job_id, report_dict)

    except AppError as ae:
        job_manager.fail_job(job_id, ae.to_dict()["error"])
    except Exception as e:
        logger.exception("Unexpected error in analysis pipeline")
        job_manager.fail_job(
            job_id,
            {"code": ErrorCode.INTERNAL, "message": str(e), "retryable": True},
        )

@router.post("/analyze")
async def analyze_repo(
    request_data: AnalyzeRequest,
    req: Request,
    background_tasks: BackgroundTasks,
):
    client_ip = req.client.host if req.client else "127.0.0.1"
    rate_limiter.check(client_ip, action="analyze")

    target = validate_github_url(request_data.url)
    repo_key = target.full_name.lower()

    # Deduplicate in-flight or start new job
    job, is_new = job_manager.create_or_join_job(repo_key)

    if is_new:
        background_tasks.add_task(
            run_analysis_pipeline,
            job.job_id,
            target,
            request_data.force_refresh,
        )

    return {
        "job_id": job.job_id,
        "status": job.status,
        "stage": job.stage,
        "progress_pct": job.progress_pct,
    }

@router.get("/report/{owner}/{repo}")
async def get_cached_report(owner: str, repo: str):
    settings = get_settings()
    # Check latest cached report key with wildcard or default
    prefix = f"{owner.lower()}/{repo.lower()}@"
    # Fallback to direct cache fetch
    cached = await cache.get(f"{owner.lower()}/{repo.lower()}@latest:{settings.prompt_version}")
    if cached:
        return cached
    raise AppError(
        code=ErrorCode.REPO_NOT_FOUND,
        message="No cached analysis found for this repository. Please run an analysis first.",
        status_code=404,
    )
