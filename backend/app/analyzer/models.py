from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class TechItem(BaseModel):
    name: str
    category: str
    evidence: List[str] = Field(default_factory=list)

class LanguageStat(BaseModel):
    name: str
    percent: float
    bytes: int = 0

class EndpointInfo(BaseModel):
    method: str
    path: str
    file: str

class KeyFileInfo(BaseModel):
    path: str
    why_important: str

class RunInstructions(BaseModel):
    prerequisites: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    source: str = ""

class RepoMetrics(BaseModel):
    files: int = 0
    loc: int = 0
    has_tests: bool = False
    test_framework: Optional[str] = None
    has_ci: bool = False
    has_docker: bool = False
    readme_score: int = 0
    contributors_count: int = 0

class StaticFacts(BaseModel):
    project_type: str = "other"  # web-app | api | library | cli | mobile | ml | monorepo | other
    languages: List[LanguageStat] = Field(default_factory=list)
    tech_stack: Dict[str, List[TechItem]] = Field(
        default_factory=lambda: {
            "frontend": [],
            "backend": [],
            "database": [],
            "devops": [],
            "testing": [],
            "other": [],
        }
    )
    structure_pattern: str = "Standard"
    is_monorepo: bool = False
    monorepo_packages: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    api_endpoints: List[EndpointInfo] = Field(default_factory=list)
    data_models: List[str] = Field(default_factory=list)
    env_variables: List[str] = Field(default_factory=list)
    key_files: List[KeyFileInfo] = Field(default_factory=list)
    metrics: RepoMetrics = Field(default_factory=RepoMetrics)
    how_to_run: RunInstructions = Field(default_factory=RunInstructions)
    warnings: List[str] = Field(default_factory=list)
