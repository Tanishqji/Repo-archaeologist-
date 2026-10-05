import json
import os
import re
from typing import Dict, List, Set

CANDIDATE_FILENAMES = {
    "main.py",
    "app.py",
    "server.py",
    "wsgi.py",
    "asgi.py",
    "index.js",
    "server.js",
    "app.js",
    "main.ts",
    "index.ts",
    "server.ts",
    "app.ts",
    "main.tsx",
    "index.tsx",
    "main.go",
    "main.rs",
    "application.java",
}

def detect_entry_points(tree_paths: Set[str], files: Dict[str, str]) -> List[str]:
    entry_points: Set[str] = set()

    # 1. Filename match
    for p in tree_paths:
        base = os.path.basename(p).lower()
        if base in CANDIDATE_FILENAMES:
            entry_points.add(p)

    # 2. Check package.json main and scripts.start
    pkg_content = files.get("package.json")
    if pkg_content:
        try:
            data = json.loads(pkg_content)
            main_field = data.get("main")
            if main_field and isinstance(main_field, str):
                entry_points.add(main_field)
            scripts = data.get("scripts", {})
            start_script = scripts.get("start") or scripts.get("dev")
            if start_script and isinstance(start_script, str):
                for token in start_script.split():
                    if token.endswith((".js", ".ts", ".jsx", ".tsx", ".py")):
                        entry_points.add(token)
        except Exception:
            pass

    # 3. Check Dockerfile CMD/ENTRYPOINT
    for path, content in files.items():
        if "dockerfile" in os.path.basename(path).lower():
            for line in content.splitlines():
                line = line.strip()
                if line.startswith(("CMD", "ENTRYPOINT")):
                    entry_points.add(f"{path} ({line})")

    return sorted(list(entry_points))
