import os
import re
from typing import Dict, List, Set
from app.analyzer.models import KeyFileInfo

IMPORT_PATTERNS = [
    # Python: from .module import foo, import app.utils
    re.compile(r"""(?:from\s+([.\w]+)\s+import|import\s+([.\w]+))"""),
    # JS/TS: import ... from './path' or require('./path')
    re.compile(r"""(?:import.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))"""),
]

def analyze_imports_and_rank_files(
    tree_paths: Set[str],
    files: Dict[str, str],
    entry_points: List[str],
) -> List[KeyFileInfo]:
    """
    Ranks files based on import in-degree, entry point status, and architectural naming hints.
    """
    in_degrees: Dict[str, int] = {p: 0 for p in tree_paths}

    for src_path, content in files.items():
        src_dir = os.path.dirname(src_path)
        for pattern in IMPORT_PATTERNS:
            for match in pattern.finditer(content):
                target_ref = match.group(1) or match.group(2)
                if not target_ref:
                    continue

                # Relative JS/TS import: ./foo or ../bar
                if target_ref.startswith("."):
                    norm = os.path.normpath(os.path.join(src_dir, target_ref)).replace("\\", "/")
                    for ext in ("", ".ts", ".js", ".tsx", ".jsx", "/index.ts", "/index.js"):
                        cand = norm + ext
                        if cand in in_degrees:
                            in_degrees[cand] += 1
                            break

                # Python relative or package import
                elif "." in target_ref or "/" in target_ref:
                    mod_path = target_ref.replace(".", "/") + ".py"
                    if mod_path in in_degrees:
                        in_degrees[mod_path] += 1

    ranked: List[KeyFileInfo] = []
    seen = set()

    # 1. Entry points first
    for ep in entry_points:
        clean_ep = ep.split(" ")[0]
        if clean_ep in tree_paths and clean_ep not in seen:
            seen.add(clean_ep)
            ranked.append(KeyFileInfo(path=clean_ep, why_important="Primary Application Entry Point"))

    # 2. Architecturally important keywords
    arch_keywords = ("config", "server", "app", "routes", "models", "schema", "controller", "service", "database", "auth")
    for p in sorted(tree_paths):
        p_lower = p.lower()
        if p not in seen and any(kw in p_lower for kw in arch_keywords) and p.endswith((".py", ".ts", ".js", ".go", ".java", ".rs")):
            score = in_degrees.get(p, 0)
            reason = f"Core module ({'imported by other modules' if score > 0 else 'architectural component'})"
            seen.add(p)
            ranked.append(KeyFileInfo(path=p, why_important=reason))
            if len(ranked) >= 15:
                break

    # 3. Highest in-degree files
    top_by_imports = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
    for p, count in top_by_imports:
        if count > 0 and p not in seen:
            seen.add(p)
            ranked.append(KeyFileInfo(path=p, why_important=f"High internal dependency (imported {count} times)"))
            if len(ranked) >= 20:
                break

    return ranked

def detect_data_models(files: Dict[str, str], tree_paths: Set[str]) -> List[str]:
    """
    Detects defined schemas/models (Mongoose, SQLAlchemy, JPA @Entity, Prisma schema).
    """
    models: Set[str] = set()

    for p in tree_paths:
        if "schema.prisma" in p.lower():
            models.add(f"Prisma Schema ({p})")
        elif "models/" in p.lower() or "schemas/" in p.lower() or "entities/" in p.lower():
            base = os.path.splitext(os.path.basename(p))[0]
            if base not in ("index", "__init__"):
                models.add(f"{base.capitalize()} ({p})")

    # Inspect code patterns
    for path, content in files.items():
        # SQLAlchemy
        if "Base = declarative_base()" in content or "(Base)" in content:
            for line in content.splitlines():
                m = re.match(r"class\s+([A-Za-z0-9_]+)\(Base\):", line)
                if m:
                    models.add(f"SQLAlchemy: {m.group(1)} ({path})")
        # Mongoose
        if "new Schema" in content or "mongoose.model" in content:
            for line in content.splitlines():
                m = re.search(r"mongoose\.model\s*\(\s*['\"]([^'\"]+)['\"]", line)
                if m:
                    models.add(f"Mongoose: {m.group(1)} ({path})")
        # Java JPA @Entity
        if "@Entity" in content:
            for line in content.splitlines():
                m = re.match(r"(?:public\s+)?class\s+([A-Za-z0-9_]+)", line)
                if m:
                    models.add(f"JPA Entity: {m.group(1)} ({path})")

    return sorted(list(models))
