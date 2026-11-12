from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AstEntitySchema(BaseModel):
    id: str
    project_id: str
    file_path: str
    name: str
    entity_type: str
    start_line: int
    end_line: int
    language: str
    signature: str
    docstring: str
    params: List[Any]
    return_type: str
    calls: List[str]
    evidence: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class DependencyNode(BaseModel):
    id: str
    label: str
    type: str  # file, module, class, function
    language: Optional[str] = ""
    layer: Optional[str] = ""
    line_count: Optional[int] = 0

class DependencyEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str  # import, call, inheritance, reference
    confidence: str  # confirmed, inferred
    evidence: Dict[str, Any]

class DependencyGraphResponse(BaseModel):
    nodes: List[DependencyNode]
    edges: List[DependencyEdgeSchema]
    circular_dependencies: List[List[str]]
    high_dependency_modules: List[Dict[str, Any]]
    isolated_modules: List[str]

class ImpactAnalysisRequest(BaseModel):
    node_id: str
    depth: int = 3

class ImpactAnalysisResponse(BaseModel):
    target_node: str
    direct_dependents: List[str]
    indirect_dependents: List[str]
    affected_files: List[str]
    severity: str
    evidence: List[Dict[str, Any]]

class ArchitectureComponentSchema(BaseModel):
    id: str
    name: str
    layer: str
    files: List[str]
    responsibilities: List[str]
    incoming_connections: List[str]
    outgoing_connections: List[str]
    evidence: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class ArchitectureResponse(BaseModel):
    layers: List[str]
    components: List[ArchitectureComponentSchema]
    connections: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)

class DatabaseModelSchema(BaseModel):
    id: Optional[str] = ""
    name: str
    orm_framework: str
    file_path: str
    line_number: int
    fields: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    evidence: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class DatabaseSchemaResponse(BaseModel):
    models: List[DatabaseModelSchema]
    er_nodes: List[Dict[str, Any]]
    er_edges: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)

class ApiEndpointSchema(BaseModel):
    id: str
    method: str
    path: str
    framework: str
    file_path: str
    line_number: int
    handler_name: str
    auth_middleware: str
    parameters: List[Dict[str, Any]]
    request_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    related_models: List[str]
    evidence: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class ApiExplorerResponse(BaseModel):
    endpoints: List[ApiEndpointSchema]
    total_endpoints: int
    frameworks: List[str]
    methods: Dict[str, int]
    openapi_spec: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class HealthFindingSchema(BaseModel):
    id: str
    category: str
    title: str
    description: str
    severity: str
    affected_files: List[str]
    evidence: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class HealthReportResponse(BaseModel):
    health_score: int
    grade: str
    findings: List[HealthFindingSchema]
    summary_by_severity: Dict[str, int]
    summary_by_category: Dict[str, int]

    model_config = ConfigDict(from_attributes=True)

class WorkflowStep(BaseModel):
    order: int
    component: str
    action: str
    file: str
    line: int
    end_line: Optional[int] = None
    layer: Optional[str] = ""
    evidence_type: Optional[str] = ""
    confidence: Optional[str] = "confirmed"
    status: Optional[str] = "confirmed"

    model_config = ConfigDict(from_attributes=True)

class WorkflowSchema(BaseModel):
    id: str
    name: str
    trigger: str
    completeness: Optional[str] = "complete"
    missing_evidence: Optional[List[str]] = []
    steps: List[WorkflowStep]
    evidence: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class WorkflowsResponse(BaseModel):
    workflows: List[WorkflowSchema]

    model_config = ConfigDict(from_attributes=True)

class AiChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class AiChatResponse(BaseModel):
    message: str
    sources: List[Dict[str, Any]]
    confidence: str
    provider_used: str

class TestGenerateRequest(BaseModel):
    target_file: Optional[str] = None
    framework: Optional[str] = "pytest"

class GeneratedTestSchema(BaseModel):
    id: str
    target_file: str
    target_symbol: str
    test_framework: str
    test_type: str
    test_name: str
    code: str
    review_status: str
    created_at: datetime

class SettingsResponse(BaseModel):
    provider: str
    has_gemini_key: bool
    has_groq_key: bool
    has_openai_key: bool
    openai_base_url: str
    local_model_url: str
    max_upload_size_mb: int
    max_uncompressed_size_mb: int
    is_localhost_only: bool

class SettingsUpdateRequest(BaseModel):
    provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    local_model_url: Optional[str] = None
    max_upload_size_mb: Optional[int] = None

class ProviderTestRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None

class ProviderTestResponse(BaseModel):
    success: bool
    message: str

