import json
import os
from typing import Any, Dict, List, Set, Tuple

def detect_structure(
    tree_paths: Set[str],
    files: Dict[str, str],
    categorized_stack: Dict[str, List[Any]],
) -> Tuple[str, bool, List[str], str]:
    """
    Analyzes tree paths and manifests to detect project structure, monorepo status, and project type.
    Returns: (structure_pattern, is_monorepo, monorepo_packages, project_type)
    """
    is_monorepo = False
    monorepo_packages: List[str] = []
    structure_pattern = "Standard Single-Module"
    project_type = "other"

    # 1. Monorepo detection
    # Check workspaces in package.json
    root_pkg_content = files.get("package.json")
    if root_pkg_content:
        try:
            pkg_data = json.loads(root_pkg_content)
            workspaces = pkg_data.get("workspaces", [])
            if workspaces:
                is_monorepo = True
        except Exception:
            pass

    # Check multiple manifests or packages/ apps/ dirs
    manifest_count = 0
    package_dirs: Set[str] = set()
    for p in tree_paths:
        parts = p.split("/")
        if len(parts) > 1 and parts[0] in ("packages", "apps", "services", "modules"):
            package_dirs.add(parts[1])
            is_monorepo = True
        if os.path.basename(p) in ("package.json", "pom.xml", "Cargo.toml", "go.mod") and "/" in p:
            manifest_count += 1

    if manifest_count >= 2:
        is_monorepo = True

    if is_monorepo:
        monorepo_packages = sorted(list(package_dirs))
        structure_pattern = f"Monorepo ({len(monorepo_packages)} packages detected)" if monorepo_packages else "Monorepo (Multi-manifest)"
        project_type = "monorepo"

    # 2. Client / Server Split
    has_client = any(p.startswith(("client/", "frontend/", "web/", "ui/")) for p in tree_paths)
    has_server = any(p.startswith(("server/", "backend/", "api/")) for p in tree_paths)
    if has_client and has_server:
        structure_pattern = "Client-Server Architecture"
        project_type = "web-app"

    # 3. Layered Patterns
    has_controllers = any("/controller" in p.lower() or "/controllers" in p.lower() for p in tree_paths)
    has_services = any("/service" in p.lower() or "/services" in p.lower() for p in tree_paths)
    has_repos = any("/repository" in p.lower() or "/repositories" in p.lower() or "/repo" in p.lower() for p in tree_paths)
    if has_controllers and has_services:
        structure_pattern = "Layered Architecture (Controller / Service / Repository)"

    # 4. Microservices
    dockerfile_count = sum(1 for p in tree_paths if "dockerfile" in os.path.basename(p).lower())
    if dockerfile_count > 2 or any(p.startswith("services/") for p in tree_paths):
        structure_pattern = "Microservices Architecture"

    # 5. Determine Project Type if not monorepo
    if project_type == "other":
        has_frontend_stack = bool(categorized_stack.get("frontend"))
        has_backend_stack = bool(categorized_stack.get("backend"))
        has_notebooks = any(p.endswith(".ipynb") for p in tree_paths)
        has_cli_hints = any(p.endswith("cli.py") or "/cli" in p or "bin/" in p for p in tree_paths)
        has_mobile = any("pubspec.yaml" in p or "androidmanifest.xml" in p.lower() for p in tree_paths)

        if has_mobile:
            project_type = "mobile"
        elif has_notebooks and not (has_frontend_stack or has_backend_stack):
            project_type = "ml"
        elif has_frontend_stack and has_backend_stack:
            project_type = "web-app"
        elif has_frontend_stack:
            project_type = "web-app"
        elif has_backend_stack:
            project_type = "api"
        elif has_cli_hints:
            project_type = "cli"
        else:
            project_type = "library"

    return structure_pattern, is_monorepo, monorepo_packages, project_type
