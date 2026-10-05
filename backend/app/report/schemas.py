from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RepoInfo(BaseModel):
    owner: str = ""
    name: str = ""
    url: str = ""
    default_branch: str = "main"
    commit_sha: str = ""
    stars: int = 0
    license: Optional[str] = None
    last_pushed: Optional[str] = None

class LanguageInfo(BaseModel):
    name: str
    percent: float

class TechStackItem(BaseModel):
    name: str
    evidence: List[str] = Field(default_factory=list)

class TechStackGroup(BaseModel):
    languages: List[LanguageInfo] = Field(default_factory=list)
    frontend: List[TechStackItem] = Field(default_factory=list)
    backend: List[TechStackItem] = Field(default_factory=list)
    database: List[TechStackItem] = Field(default_factory=list)
    devops: List[TechStackItem] = Field(default_factory=list)
    testing: List[TechStackItem] = Field(default_factory=list)
    other: List[TechStackItem] = Field(default_factory=list)

class ArchitectureComponent(BaseModel):
    name: str
    role: str
    evidence: List[str] = Field(default_factory=list)

class ArchitectureInfo(BaseModel):
    pattern: str = "Standard"
    components: List[ArchitectureComponent] = Field(default_factory=list)
    data_flow: str = ""
    mermaid: str = ""

class WorkflowStep(BaseModel):
    step: int
    description: str
    evidence: List[str] = Field(default_factory=list)

class ApiEndpoint(BaseModel):
    method: str
    path: str
    file: str

class KeyFile(BaseModel):
    path: str
    why_important: str

class HowToRun(BaseModel):
    prerequisites: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    source: str = ""

class Metrics(BaseModel):
    files: int = 0
    loc: int = 0
    has_tests: bool = False
    has_ci: bool = False
    has_docker: bool = False
    readme_score: int = 0

class Confidence(BaseModel):
    score: float = 1.0  # 0.0 to 1.0
    notes: str = ""

class AnalysisReport(BaseModel):
    repo: RepoInfo
    summary: str
    project_type: str = "other"  # web-app | api | library | cli | mobile | ml | monorepo | other
    tech_stack: TechStackGroup
    architecture: ArchitectureInfo
    workflow: List[WorkflowStep] = Field(default_factory=list)
    api_endpoints: List[ApiEndpoint] = Field(default_factory=list)
    key_files: List[KeyFile] = Field(default_factory=list)
    env_variables: List[str] = Field(default_factory=list)
    how_to_run: HowToRun
    metrics: Metrics
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    confidence: Confidence
    warnings: List[str] = Field(default_factory=list)
    llm_status: str = "ok"  # ok | degraded
