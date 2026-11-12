import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, JSON, ForeignKey
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now():
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    original_archive_name = Column(String(255), default="")
    archive_path = Column(String(512), default="")
    extracted_path = Column(String(512), default="")
    status = Column(String(50), default="pending")  # pending, scanning, analyzing, completed, failed
    error_message = Column(Text, default="")
    
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    primary_language = Column(String(100), default="Unknown")
    languages = Column(JSON, default=list)  # [{"language": "Python", "percentage": 85, "files": 20}]
    frameworks = Column(JSON, default=list)  # [{"name": "FastAPI", "version": "0.115"}]
    ignored_files_count = Column(Integer, default=0)
    health_score = Column(Integer, default=100)
    
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    relative_path = Column(String(512), nullable=False)
    language = Column(String(100), default="unknown")
    size_bytes = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    category = Column(String(50), default="other")  # frontend, backend, database, config, test, doc, other
    layer = Column(String(50), default="unknown")  # presentation, api, business_logic, data_access, database, config
    is_entry_point = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)


class AstEntity(Base):
    __tablename__ = "ast_entities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)  # function, method, class, interface, component, export
    start_line = Column(Integer, default=1)
    end_line = Column(Integer, default=1)
    language = Column(String(50), default="unknown")
    signature = Column(Text, default="")
    docstring = Column(Text, default="")
    params = Column(JSON, default=list)
    return_type = Column(String(100), default="")
    calls = Column(JSON, default=list)
    evidence = Column(JSON, default=dict)


class DependencyEdge(Base):
    __tablename__ = "dependency_edges"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(512), nullable=False, index=True)
    target = Column(String(512), nullable=False, index=True)
    edge_type = Column(String(50), default="import")  # import, call, inheritance, reference
    confidence = Column(String(50), default="confirmed")  # confirmed, inferred
    evidence = Column(JSON, default=dict)


class ApiEndpoint(Base):
    __tablename__ = "api_endpoints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(String(20), nullable=False)
    path = Column(String(512), nullable=False)
    framework = Column(String(50), default="unknown")
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, default=1)
    handler_name = Column(String(255), default="")
    auth_middleware = Column(String(255), default="")
    parameters = Column(JSON, default=list)
    request_schema = Column(JSON, default=dict)
    response_schema = Column(JSON, default=dict)
    related_models = Column(JSON, default=list)
    evidence = Column(JSON, default=dict)


class DatabaseModel(Base):
    __tablename__ = "database_models"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    orm_framework = Column(String(50), default="unknown")  # sqlalchemy, prisma, django, sequelize, mongoose, sql
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, default=1)
    fields = Column(JSON, default=list)  # [{"name": "id", "type": "int", "primary_key": True}]
    relationships = Column(JSON, default=list)  # [{"target": "Post", "type": "1-N", "foreign_key": "user_id"}]
    evidence = Column(JSON, default=dict)


class ArchitectureComponent(Base):
    __tablename__ = "architecture_components"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    layer = Column(String(100), nullable=False)  # Presentation, API, Business Logic, Data Access, Database, External Services
    files = Column(JSON, default=list)
    responsibilities = Column(JSON, default=list)
    incoming_connections = Column(JSON, default=list)
    outgoing_connections = Column(JSON, default=list)
    evidence = Column(JSON, default=dict)


class HealthFinding(Base):
    __tablename__ = "health_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), default="general")  # complexity, circular_dependency, isolated_module, security, deprecated_tech
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    severity = Column(String(50), default="info")  # info, low, medium, high, critical
    affected_files = Column(JSON, default=list)
    evidence = Column(JSON, default=dict)


class WorkflowSequence(Base):
    __tablename__ = "workflow_sequences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    trigger = Column(String(255), default="")
    completeness = Column(String(50), default="complete")
    missing_evidence = Column(JSON, default=list)
    steps = Column(JSON, default=list)  # [{"order": 1, "component": "AuthCtrl", "action": "verify_token", "file": "..."}]
    evidence = Column(JSON, default=dict)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list)  # [{"file": "...", "start_line": 1, "end_line": 20, "confidence": "high"}]
    confidence = Column(String(50), default="high")
    created_at = Column(DateTime, default=get_utc_now)


class GeneratedTest(Base):
    __tablename__ = "generated_tests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    target_file = Column(String(512), nullable=False)
    target_symbol = Column(String(255), default="")
    test_framework = Column(String(50), default="pytest")  # pytest, jest, vitest
    test_type = Column(String(50), default="positive")  # positive, negative, boundary, authentication
    test_name = Column(String(255), nullable=False)
    code = Column(Text, nullable=False)
    review_status = Column(String(50), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=get_utc_now)
