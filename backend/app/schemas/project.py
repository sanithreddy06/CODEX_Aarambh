from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    original_archive_name: str
    status: str
    error_message: str
    total_files: int
    total_lines: int
    primary_language: str
    languages: List[Dict[str, Any]]
    frameworks: List[Dict[str, Any]]
    ignored_files_count: int
    health_score: int
    created_at: datetime
    updated_at: datetime

class FileRecordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    relative_path: str
    language: str
    size_bytes: int
    line_count: int
    category: str
    layer: str
    is_entry_point: bool

class ProjectOverviewResponse(BaseModel):
    project: ProjectResponse
    files_count: int
    lines_count: int
    endpoints_count: int
    models_count: int
    entities_count: int
    components_count: int
    health_score: int
    categories_breakdown: Dict[str, int]
    layers_breakdown: Dict[str, int]
