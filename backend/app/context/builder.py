import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from app.analyzer.models import StaticFacts
from app.config import get_settings
from app.context.ranker import rank_files_for_context
from app.context.redactor import is_sensitive_file, redact_secrets
from app.github.fetcher import FetchedRepo, TreeItem

logger = logging.getLogger(__name__)

# Rough approximation: 1 token ~= 4 characters of code/text
APPROX_CHARS_PER_TOKEN = 4

def truncate_content(content: str, max_lines: int = 150) -> str:
    lines = content.splitlines()
    if len(lines) <= max_lines:
        return content
    head_count = max_lines // 2
    tail_count = max_lines - head_count
    head = lines[:head_count]
    tail = lines[-tail_count:]
    return "\n".join(head) + f"\n\n[... truncated {len(lines) - max_lines} lines ...]\n\n" + "\n".join(tail)

def build_tree_summary(tree: List[TreeItem], max_entries: int = 100) -> str:
    paths = [item.path for item in tree]
    if len(paths) <= max_entries:
        return "\n".join(paths)
    head = paths[: max_entries - 10]
    tail = paths[-10:]
    return "\n".join(head) + f"\n... [{len(paths) - max_entries} more files] ...\n" + "\n".join(tail)

class ContextBundle:
    def __init__(
        self,
        prompt_context: str,
        included_files: List[str],
        secrets_detected_files: List[str],
        estimated_tokens: int,
    ):
        self.prompt_context = prompt_context
        self.included_files = included_files
        self.secrets_detected_files = secrets_detected_files
        self.estimated_tokens = estimated_tokens

def build_llm_context(
    repo: FetchedRepo,
    facts: StaticFacts,
    token_budget: Optional[int] = None,
) -> ContextBundle:
    settings = get_settings()
    budget_tokens = token_budget or settings.context_token_budget
    budget_chars = budget_tokens * APPROX_CHARS_PER_TOKEN

    included_files: List[str] = []
    secrets_detected_files: List[str] = []

    # 1. Base facts JSON
    facts_json_str = facts.model_dump_json(indent=2)
    facts_block = f"""
=== STATIC ANALYSIS FACTS (TRUTH GROUNDING) ===
{facts_json_str}
================================================
"""

    # 2. File tree
    tree_str = build_tree_summary(repo.tree)
    tree_block = f"""
=== REPOSITORY FILE TREE ===
{tree_str}
============================
"""

    current_chars = len(facts_block) + len(tree_block)
    files_blocks: List[str] = []

    # 3. Rank files
    ranked_files = rank_files_for_context(repo.tree, repo.files, facts)

    for path, _score in ranked_files:
        if path not in repo.files:
            continue

        # Skip sensitive files completely
        if is_sensitive_file(path):
            secrets_detected_files.append(path)
            continue

        raw_content = repo.files[path]
        redacted_content, has_secret = redact_secrets(raw_content)
        if has_secret:
            secrets_detected_files.append(path)

        trimmed = truncate_content(redacted_content, max_lines=180)
        file_block = f"""
<<<FILE path="{path}">>>
{trimmed}
<<</FILE>>>
"""
        if current_chars + len(file_block) > budget_chars:
            break

        files_blocks.append(file_block)
        included_files.append(path)
        current_chars += len(file_block)

    full_context = f"{facts_block}\n{tree_block}\n\n=== REPOSITORY SOURCE FILES (UNTRUSTED REPO DATA) ===\n" + "\n".join(files_blocks)
    estimated_tokens = len(full_context) // APPROX_CHARS_PER_TOKEN

    return ContextBundle(
        prompt_context=full_context,
        included_files=included_files,
        secrets_detected_files=secrets_detected_files,
        estimated_tokens=estimated_tokens,
    )
