import os
from typing import Dict, List, Set
from app.analyzer.entrypoints import detect_entry_points
from app.analyzer.imports import analyze_imports_and_rank_files, detect_data_models
from app.analyzer.languages import analyze_languages
from app.analyzer.manifests import parse_manifests
from app.analyzer.metrics import calculate_metrics
from app.analyzer.models import StaticFacts
from app.analyzer.routes_detect import detect_routes
from app.analyzer.run_instructions import extract_env_variables, extract_run_instructions
from app.analyzer.structure import detect_structure
from app.github.fetcher import FetchedRepo

def run_static_analysis(repo: FetchedRepo) -> StaticFacts:
    """
    Executes 100% deterministic static analysis over fetched repository artifacts.
    Produces a verified StaticFacts record grounded in evidence.
    """
    warnings: List[str] = list(repo.warnings)
    tree_paths: Set[str] = {item.path for item in repo.tree}

    # 1. Language stats
    languages = analyze_languages(repo.languages, repo.tree)

    # 2. Manifest analysis (table-driven via signatures.yaml)
    categorized_stack = parse_manifests(repo.files, tree_paths, warnings)

    # 3. Structure detection (Monorepo, Client/Server, Microservices, Project Type)
    structure_pattern, is_monorepo, monorepo_packages, project_type = detect_structure(
        tree_paths, repo.files, categorized_stack
    )

    # 4. Entry points
    entry_points = detect_entry_points(tree_paths, repo.files)

    # 5. API Routes
    api_endpoints = detect_routes(repo.files)

    # 6. Data models & Key files ranking
    data_models = detect_data_models(repo.files, tree_paths)
    key_files = analyze_imports_and_rank_files(tree_paths, repo.files, entry_points)

    # 7. Metrics & health
    metrics = calculate_metrics(repo.tree, repo.files)

    # 8. Run instructions and Environment variables
    how_to_run = extract_run_instructions(repo.files, tree_paths)
    env_vars = extract_env_variables(repo.files)

    return StaticFacts(
        project_type=project_type,
        languages=languages,
        tech_stack=categorized_stack,
        structure_pattern=structure_pattern,
        is_monorepo=is_monorepo,
        monorepo_packages=monorepo_packages,
        entry_points=entry_points,
        api_endpoints=api_endpoints,
        data_models=data_models,
        env_variables=env_vars,
        key_files=key_files,
        metrics=metrics,
        how_to_run=how_to_run,
        warnings=warnings,
    )
