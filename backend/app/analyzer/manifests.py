import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import yaml
from app.analyzer.models import TechItem

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib

logger = logging.getLogger(__name__)

def load_signatures() -> Dict[str, Dict[str, str]]:
    sig_path = Path(__file__).parent / "signatures.yaml"
    if sig_path.exists():
        with open(sig_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("signatures", {})
    return {}

SIGNATURES = load_signatures()

def match_dependency(
    dep_name: str,
    evidence_path: str,
    signatures: Dict[str, Dict[str, str]],
) -> Optional[TechItem]:
    clean_name = dep_name.strip().lower()
    stripped_domain = clean_name
    if "/" in stripped_domain and (stripped_domain.startswith("github.com/") or stripped_domain.startswith("gitlab.com/")):
        stripped_domain = stripped_domain.split("/", 1)[1]

    for sig_key, sig_info in signatures.items():
        sk_lower = sig_key.lower()
        if (
            sk_lower == clean_name
            or sk_lower == stripped_domain
            or clean_name.startswith(sk_lower + "@")
            or clean_name.startswith(sk_lower + "/")
            or stripped_domain.startswith(sk_lower + "/")
        ):
            return TechItem(
                name=sig_info.get("name", dep_name),
                category=sig_info.get("category", "other"),
                evidence=[evidence_path],
            )
    return None

def parse_package_json(
    content: str,
    path: str,
    signatures: Dict[str, Dict[str, str]],
    warnings: List[str],
) -> List[TechItem]:
    items: List[TechItem] = []
    try:
        data = json.loads(content)
        deps = {}
        deps.update(data.get("dependencies", {}))
        deps.update(data.get("devDependencies", {}))
        deps.update(data.get("peerDependencies", {}))

        for dep_name in deps:
            matched = match_dependency(dep_name, path, signatures)
            if matched:
                items.append(matched)
    except Exception as e:
        warnings.append(f"Failed to parse manifest {path}: {str(e)}")
    return items

def parse_requirements_txt(
    content: str,
    path: str,
    signatures: Dict[str, Dict[str, str]],
    warnings: List[str],
) -> List[TechItem]:
    items: List[TechItem] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Split version constraints
        match = re.split(r"[=<>~!;\[]", line)[0].strip()
        if match:
            matched = match_dependency(match, path, signatures)
            if matched:
                items.append(matched)
    return items

def parse_pyproject_toml(
    content: str,
    path: str,
    signatures: Dict[str, Dict[str, str]],
    warnings: List[str],
) -> List[TechItem]:
    items: List[TechItem] = []
    try:
        data = tomllib.loads(content)
        # Standard PEP 621 dependencies
        project_deps = data.get("project", {}).get("dependencies", [])
        for dep in project_deps:
            name = re.split(r"[=<>~!;\[]", dep)[0].strip()
            matched = match_dependency(name, path, signatures)
            if matched:
                items.append(matched)

        # Poetry dependencies
        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        for name in poetry_deps:
            matched = match_dependency(name, path, signatures)
            if matched:
                items.append(matched)
    except Exception as e:
        warnings.append(f"Failed to parse {path}: {str(e)}")
    return items

def parse_go_mod(
    content: str,
    path: str,
    signatures: Dict[str, Dict[str, str]],
) -> List[TechItem]:
    items: List[TechItem] = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("require (") or line.startswith(")") or line.startswith("module") or line.startswith("go "):
            continue
        parts = line.split()
        if len(parts) >= 2:
            pkg = parts[0] if parts[0] != "require" else parts[1]
            matched = match_dependency(pkg, path, signatures)
            if matched:
                items.append(matched)
    return items

def parse_cargo_toml(
    content: str,
    path: str,
    signatures: Dict[str, Dict[str, str]],
    warnings: List[str],
) -> List[TechItem]:
    items: List[TechItem] = []
    try:
        data = tomllib.loads(content)
        deps = data.get("dependencies", {})
        for name in deps:
            matched = match_dependency(name, path, signatures)
            if matched:
                items.append(matched)
    except Exception as e:
        warnings.append(f"Failed to parse {path}: {str(e)}")
    return items

def parse_manifests(
    files: Dict[str, str],
    tree_paths: Set[str],
    warnings: List[str],
) -> Dict[str, List[TechItem]]:
    """
    Parses all discovered manifests and returns categorized tech items with evidence.
    """
    signatures = SIGNATURES
    found_items: List[TechItem] = []

    # Check for docker / devops in tree
    for p in tree_paths:
        p_lower = p.lower()
        if "dockerfile" in p_lower:
            found_items.append(TechItem(name="Docker", category="devops", evidence=[p]))
        elif "docker-compose" in p_lower:
            found_items.append(TechItem(name="Docker Compose", category="devops", evidence=[p]))
        elif p_lower.startswith(".github/workflows/"):
            found_items.append(TechItem(name="GitHub Actions", category="devops", evidence=[p]))
        elif p_lower.endswith(".tf"):
            found_items.append(TechItem(name="Terraform", category="devops", evidence=[p]))
        elif "k8s/" in p_lower or "kubernetes/" in p_lower:
            found_items.append(TechItem(name="Kubernetes", category="devops", evidence=[p]))

    for path, content in files.items():
        base = os.path.basename(path).lower()
        if base == "package.json":
            found_items.extend(parse_package_json(content, path, signatures, warnings))
        elif base.startswith("requirements") and base.endswith(".txt"):
            found_items.extend(parse_requirements_txt(content, path, signatures, warnings))
        elif base == "pyproject.toml":
            found_items.extend(parse_pyproject_toml(content, path, signatures, warnings))
        elif base == "go.mod":
            found_items.extend(parse_go_mod(content, path, signatures))
        elif base == "cargo.toml":
            found_items.extend(parse_cargo_toml(content, path, signatures, warnings))

    # Deduplicate and group by category
    categorized: Dict[str, List[TechItem]] = {
        "frontend": [],
        "backend": [],
        "database": [],
        "devops": [],
        "testing": [],
        "other": [],
    }

    seen: Dict[Tuple[str, str], TechItem] = {}
    for item in found_items:
        key = (item.name, item.category)
        if key in seen:
            for ev in item.evidence:
                if ev not in seen[key].evidence:
                    seen[key].evidence.append(ev)
        else:
            seen[key] = item
            if item.category in categorized:
                categorized[item.category].append(item)
            else:
                categorized["other"].append(item)

    return categorized
