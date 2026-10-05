from typing import Dict, List, Set
from app.report.schemas import AnalysisReport

def post_validate_evidence(
    report: AnalysisReport,
    valid_paths: Set[str],
) -> AnalysisReport:
    """
    Guards strictly against LLM hallucinations by ensuring every cited evidence path
    exists in the actual repository tree. Non-existent paths are pruned.
    """
    # 1. Tech stack evidence
    for group_name in ("frontend", "backend", "database", "devops", "testing", "other"):
        items = getattr(report.tech_stack, group_name, [])
        for item in items:
            item.evidence = [p for p in item.evidence if p in valid_paths]

    # 2. Architecture components evidence
    for comp in report.architecture.components:
        comp.evidence = [p for p in comp.evidence if p in valid_paths]

    # 3. Workflow evidence
    for step in report.workflow:
        step.evidence = [p for p in step.evidence if p in valid_paths]

    # 4. Key files existence
    report.key_files = [kf for kf in report.key_files if kf.path in valid_paths]

    # 5. API endpoints file existence
    for ep in report.api_endpoints:
        if ep.file not in valid_paths:
            ep.file = "Detected via manifests"

    return report
