import json
import os
import re
from typing import Dict, List, Set, Tuple
from app.analyzer.models import RunInstructions

def extract_env_variables(files: Dict[str, str]) -> List[str]:
    """
    Parses .env.example / .env.sample / .env.template (never real .env)
    to list required environment variable names only.
    """
    env_vars: Set[str] = set()
    for path, content in files.items():
        base = os.path.basename(path).lower()
        if base in (".env.example", ".env.sample", ".env.template", "env.example"):
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    var_name = line.split("=")[0].strip()
                    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", var_name):
                        env_vars.add(var_name)
    return sorted(list(env_vars))

def extract_run_instructions(
    files: Dict[str, str],
    tree_paths: Set[str],
) -> RunInstructions:
    """
    Extracts run prerequisites and execution steps from README, manifests, and Dockerfiles.
    """
    prereqs: Set[str] = set()
    steps: List[str] = []
    source = "README.md"

    readme_content = ""
    for path, content in files.items():
        if os.path.basename(path).lower().startswith("readme"):
            readme_content = content
            source = path
            break

    # 1. Inspect package.json scripts
    pkg_content = files.get("package.json")
    if pkg_content:
        try:
            data = json.loads(pkg_content)
            prereqs.add("Node.js (>= 18)")
            scripts = data.get("scripts", {})
            if "install" not in steps:
                steps.append("npm install")
            if "dev" in scripts:
                steps.append("npm run dev")
            elif "start" in scripts:
                steps.append("npm start")
            source = "package.json scripts"
        except Exception:
            pass

    # 2. Inspect Python requirements / pyproject
    if any(p.startswith("requirements") for p in files):
        prereqs.add("Python (>= 3.10)")
        if "pip install -r requirements.txt" not in steps:
            steps.append("pip install -r requirements.txt")
        if "main.py" in tree_paths:
            steps.append("python main.py")
        elif "app.py" in tree_paths:
            steps.append("python app.py")
        source = "Python manifest"

    # 3. Inspect Docker / Docker Compose
    if any("docker-compose" in p for p in tree_paths):
        prereqs.add("Docker & Docker Compose")
        if not steps or len(steps) <= 1:
            steps = ["docker compose up --build"]
            source = "docker-compose.yml"

    # 4. Extract bash/sh code blocks from README if present
    if readme_content:
        code_blocks = re.findall(r"```(?:bash|sh|shell)?\s*\n(.*?)\n```", readme_content, re.DOTALL)
        candidate_commands: List[str] = []
        for block in code_blocks:
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("$"):
                    line = line[1:].strip()
                if line and not line.startswith("#"):
                    if any(cmd in line for cmd in ("install", "run", "start", "build", "serve", "clone")):
                        candidate_commands.append(line)

        if candidate_commands and len(candidate_commands) >= 2:
            steps = candidate_commands[:5]
            source = "README.md code blocks"

    return RunInstructions(
        prerequisites=sorted(list(prereqs)),
        steps=steps,
        source=source,
    )
