import os
import re
from typing import Dict, List, Optional, Set
from app.analyzer.models import RepoMetrics
from app.github.fetcher import TreeItem

def calculate_metrics(
    tree: List[TreeItem],
    files: Dict[str, str],
    contributors_count: int = 1,
) -> RepoMetrics:
    total_files = len(tree)
    total_loc = 0

    # Calculate LOC from known text files
    for path, content in files.items():
        total_loc += len(content.splitlines())

    # Add estimated LOC for remaining code files based on average ~30 bytes/line
    loaded_paths = set(files.keys())
    for item in tree:
        if item.path not in loaded_paths and item.size:
            ext = os.path.splitext(item.path)[1].lower()
            if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rs", ".rb", ".php", ".cs", ".c", ".cpp"):
                total_loc += max(1, item.size // 35)

    tree_paths = {item.path.lower() for item in tree}

    # Test presence & framework detection
    has_tests = False
    test_framework: Optional[str] = None

    for p in tree_paths:
        if "test" in p or "spec" in p:
            has_tests = True
            break

    # Identify test framework from files
    for path, content in files.items():
        p_lower = path.lower()
        if "pytest" in content or "test_" in p_lower:
            test_framework = test_framework or "pytest"
        if "describe(" in content or "it(" in content:
            if "jest" in content:
                test_framework = "Jest"
            elif "vitest" in content:
                test_framework = "Vitest"
        if "@Test" in content:
            test_framework = "JUnit"
        if "testing.T" in content:
            test_framework = "Go test"

    if test_framework:
        has_tests = True

    # CI presence
    has_ci = any(
        p.startswith(".github/workflows/")
        or p in (".gitlab-ci.yml", "jenkinsfile", ".travis.yml", ".circleci/config.yml")
        for p in tree_paths
    )

    # Docker presence
    has_docker = any("dockerfile" in p or "docker-compose" in p for p in tree_paths)

    # README score (0-100)
    readme_score = 0
    readme_content = ""
    for path, content in files.items():
        if os.path.basename(path).lower().startswith("readme"):
            readme_content = content
            break

    if readme_content:
        readme_score += 20  # Base presence
        length = len(readme_content)
        if length > 300:
            readme_score += 20
        if length > 1200:
            readme_score += 15

        readme_lower = readme_content.lower()
        if any(w in readme_lower for w in ("install", "setup", "getting started", "quick start")):
            readme_score += 15
        if any(w in readme_lower for w in ("usage", "example", "run", "how to")):
            readme_score += 15
        if any(w in readme_lower for w in ("license", "contributing", "badge", "shields.io", "[![")):
            readme_score += 15

    readme_score = min(100, readme_score)

    return RepoMetrics(
        files=total_files,
        loc=total_loc,
        has_tests=has_tests,
        test_framework=test_framework,
        has_ci=has_ci,
        has_docker=has_docker,
        readme_score=readme_score,
        contributors_count=contributors_count,
    )
