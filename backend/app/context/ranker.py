import os
from typing import Dict, List, Set, Tuple
from app.analyzer.models import StaticFacts
from app.github.fetcher import TreeItem

NAME_HINTS = {
    "app", "server", "main", "routes", "router", "controller",
    "service", "models", "schema", "database", "db", "auth",
    "config", "settings", "api", "index",
}

def rank_files_for_context(
    tree: List[TreeItem],
    files: Dict[str, str],
    facts: StaticFacts,
) -> List[Tuple[str, int]]:
    """
    Ranks files by structural importance for LLM context inclusion.
    Returns sorted list of (file_path, score).
    """
    entry_point_set = set(facts.entry_points)
    key_files_set = {kf.path for kf in facts.key_files}
    manifest_names = {
        "package.json", "requirements.txt", "pyproject.toml",
        "go.mod", "cargo.toml", "pom.xml", "docker-compose.yml",
        "dockerfile",
    }

    scores: Dict[str, int] = {}

    for item in tree:
        path = item.path
        base = os.path.basename(path).lower()
        score = 0

        # Always prioritize manifests and README
        if base in manifest_names or base.startswith("readme"):
            score += 100

        # Entry point bonus
        if path in entry_point_set:
            score += 50

        # Key file / in-degree bonus
        if path in key_files_set:
            score += 40

        # Name hints
        name_parts = set(re_split := [part.lower() for part in path.replace("/", " ").replace(".", " ").replace("_", " ").split()])
        if name_parts.intersection(NAME_HINTS):
            score += 25

        # Code extension bonus
        ext = os.path.splitext(path)[1].lower()
        if ext in (".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".java", ".rs", ".rb", ".php"):
            score += 15

        # Penalize test files, mocks, fixtures, minified files from heavy context
        if any(term in path.lower() for term in ("test", "spec", "mock", "fixture", ".min.", "dist/")):
            score -= 30

        # Size penalty (penalize files over 20KB to save token budget)
        if item.size:
            if item.size > 20000:
                score -= min(50, item.size // 5000)

        scores[path] = score

    # Sort descending by score
    sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_files
