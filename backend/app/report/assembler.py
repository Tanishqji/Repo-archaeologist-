from typing import Any, Dict, List, Optional, Set
from app.analyzer.models import StaticFacts
from app.github.fetcher import FetchedRepo
from app.llm.validate import post_validate_evidence
from app.report.diagram import build_validated_diagram, generate_fallback_diagram
from app.report.schemas import (
    AnalysisReport,
    ApiEndpoint,
    ArchitectureComponent,
    ArchitectureInfo,
    Confidence,
    HowToRun,
    KeyFile,
    LanguageInfo,
    Metrics,
    RepoInfo,
    TechStackGroup,
    TechStackItem,
    WorkflowStep,
)

def build_degraded_report(
    repo: FetchedRepo,
    facts: StaticFacts,
    warnings: List[str],
) -> AnalysisReport:
    """
    Builds a deterministic, facts-only AnalysisReport when the LLM is unavailable or failed.
    """
    # Build components from static facts
    components: List[ArchitectureComponent] = []
    for backend_item in facts.tech_stack.get("backend", []):
        components.append(
            ArchitectureComponent(
                name=backend_item.name,
                role="Backend Framework / Server",
                evidence=backend_item.evidence,
            )
        )
    for frontend_item in facts.tech_stack.get("frontend", []):
        components.append(
            ArchitectureComponent(
                name=frontend_item.name,
                role="Frontend UI Layer",
                evidence=frontend_item.evidence,
            )
        )
    for db_item in facts.tech_stack.get("database", []):
        components.append(
            ArchitectureComponent(
                name=db_item.name,
                role="Database / Persistence Layer",
                evidence=db_item.evidence,
            )
        )

    # Workflow steps from entry points
    workflow: List[WorkflowStep] = []
    for idx, ep in enumerate(facts.entry_points[:4]):
        workflow.append(
            WorkflowStep(
                step=idx + 1,
                description=f"System initializes execution via entry point '{ep}'",
                evidence=[ep.split(" ")[0]],
            )
        )

    fallback_mermaid = generate_fallback_diagram(components, facts.structure_pattern)

    # Tech stack group
    tech_stack = TechStackGroup(
        languages=[LanguageInfo(name=l.name, percent=l.percent) for l in facts.languages],
        frontend=[TechStackItem(name=i.name, evidence=i.evidence) for i in facts.tech_stack.get("frontend", [])],
        backend=[TechStackItem(name=i.name, evidence=i.evidence) for i in facts.tech_stack.get("backend", [])],
        database=[TechStackItem(name=i.name, evidence=i.evidence) for i in facts.tech_stack.get("database", [])],
        devops=[TechStackItem(name=i.name, evidence=i.evidence) for i in facts.tech_stack.get("devops", [])],
        testing=[TechStackItem(name=i.name, evidence=i.evidence) for i in facts.tech_stack.get("testing", [])],
        other=[TechStackItem(name=i.name, evidence=i.evidence) for i in facts.tech_stack.get("other", [])],
    )

    primary_lang = facts.languages[0].name if facts.languages else "code"
    summary = f"A {primary_lang}-based {facts.project_type} utilizing {facts.structure_pattern}. (Static analysis facts only; AI synthesis degraded)."

    return AnalysisReport(
        repo=RepoInfo(
            owner=repo.metadata.owner,
            name=repo.metadata.name,
            url=repo.metadata.url,
            default_branch=repo.metadata.default_branch,
            commit_sha=repo.metadata.commit_sha,
            stars=repo.metadata.stars,
            license=repo.metadata.license,
            last_pushed=repo.metadata.last_pushed,
        ),
        summary=summary,
        project_type=facts.project_type,
        tech_stack=tech_stack,
        architecture=ArchitectureInfo(
            pattern=facts.structure_pattern,
            components=components,
            data_flow="Standard request/response data flow.",
            mermaid=fallback_mermaid,
        ),
        workflow=workflow,
        api_endpoints=[ApiEndpoint(method=e.method, path=e.path, file=e.file) for e in facts.api_endpoints],
        key_files=[KeyFile(path=k.path, why_important=k.why_important) for k in facts.key_files],
        env_variables=facts.env_variables,
        how_to_run=HowToRun(
            prerequisites=facts.how_to_run.prerequisites,
            steps=facts.how_to_run.steps,
            source=facts.how_to_run.source,
        ),
        metrics=Metrics(
            files=facts.metrics.files,
            loc=facts.metrics.loc,
            has_tests=facts.metrics.has_tests,
            has_ci=facts.metrics.has_ci,
            has_docker=facts.metrics.has_docker,
            readme_score=facts.metrics.readme_score,
        ),
        strengths=["Deterministic static structure verified", "Manifests accurately parsed"],
        weaknesses=["AI narrative generation was unavailable"],
        risks=["Static-only analysis may miss subtle runtime nuances"],
        confidence=Confidence(score=0.75, notes="High-confidence static facts; degraded AI narrative."),
        warnings=warnings + facts.warnings,
        llm_status="degraded",
    )

def assemble_final_report(
    repo: FetchedRepo,
    facts: StaticFacts,
    llm_output: Optional[Dict[str, Any]],
    warnings: List[str],
) -> AnalysisReport:
    """
    Merges deterministic facts and LLM interpretation into a validated AnalysisReport.
    """
    if not llm_output:
        return build_degraded_report(repo, facts, warnings)

    valid_paths: Set[str] = {item.path for item in repo.tree}

    try:
        report = AnalysisReport.model_validate(llm_output)

        # Ensure repo metadata and metrics match deterministic truth
        report.repo.owner = repo.metadata.owner
        report.repo.name = repo.metadata.name
        report.repo.url = repo.metadata.url
        report.repo.default_branch = repo.metadata.default_branch
        report.repo.commit_sha = repo.metadata.commit_sha
        report.repo.stars = repo.metadata.stars
        report.repo.license = repo.metadata.license
        report.repo.last_pushed = repo.metadata.last_pushed

        report.metrics.files = facts.metrics.files
        report.metrics.loc = facts.metrics.loc
        report.metrics.has_tests = facts.metrics.has_tests
        report.metrics.has_ci = facts.metrics.has_ci
        report.metrics.has_docker = facts.metrics.has_docker
        report.metrics.readme_score = facts.metrics.readme_score

        # Diagram validation & fallback
        report.architecture.mermaid = build_validated_diagram(
            report.architecture.mermaid,
            report.architecture.components,
            report.architecture.pattern,
        )

        # Merge warnings
        combined_warnings = list(set(warnings + facts.warnings + report.warnings))
        report.warnings = combined_warnings

        # Evidence post-validation against hallucination
        report = post_validate_evidence(report, valid_paths)

        return report
    except Exception:
        return build_degraded_report(repo, facts, warnings)
