import re
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.config import settings, save_persisted_settings
from backend.app.core.database import get_db
from backend.app.core.security import validate_and_extract_zip, sanitize_filename
from backend.app.models.entities import (
    Project, FileRecord, AstEntity, DependencyEdge, ApiEndpoint,
    DatabaseModel, ArchitectureComponent, HealthFinding, WorkflowSequence,
    ConversationMessage, GeneratedTest
)
from backend.app.schemas.project import ProjectResponse, ProjectOverviewResponse, FileRecordSchema
from backend.app.schemas.analysis import (
    DependencyGraphResponse, ImpactAnalysisRequest, ImpactAnalysisResponse,
    ArchitectureResponse, DatabaseSchemaResponse, ApiExplorerResponse,
    WorkflowsResponse, HealthReportResponse, AiChatRequest, AiChatResponse,
    TestGenerateRequest, GeneratedTestSchema,
    SettingsResponse, SettingsUpdateRequest, ProviderTestRequest, ProviderTestResponse
)
from backend.app.engine.scanner import RepositoryScanner
from backend.app.engine.parser import CodeParser
from backend.app.engine.dependency_graph import DependencyGraphAnalyzer
from backend.app.engine.architecture import ArchitectureReconstructor
from backend.app.engine.database_analyzer import DatabaseAnalyzer
from backend.app.engine.api_discoverer import ApiDiscoverer
from backend.app.engine.workflows import WorkflowReconstructor
from backend.app.engine.health_analyzer import HealthAnalyzer
from backend.app.engine.test_reconstructor import TestReconstructor
from backend.app.ai.llm_client import AIIntelligenceClient
from backend.app.reporting.doc_generator import DocumentationGenerator

router = APIRouter()
ai_client = AIIntelligenceClient()
doc_gen = DocumentationGenerator()

# -------------------------------------------------------------
# SYSTEM HEALTH & SETTINGS
# -------------------------------------------------------------
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "ai_provider": settings.AI_PROVIDER,
        "single_user_mode": settings.LOCAL_ONLY
    }

@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Returns current configuration without revealing sensitive API keys."""
    return SettingsResponse(
        provider=settings.AI_PROVIDER,
        has_gemini_key=bool(settings.GEMINI_API_KEY),
        has_groq_key=bool(settings.GROQ_API_KEY),
        has_openai_key=bool(settings.OPENAI_API_KEY),
        openai_base_url=settings.OPENAI_BASE_URL,
        local_model_url=settings.LOCAL_MODEL_URL,
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        max_uncompressed_size_mb=settings.MAX_UNCOMPRESSED_SIZE_MB,
        is_localhost_only=settings.LOCAL_ONLY
    )

@router.post("/settings", response_model=SettingsResponse)
async def update_settings(payload: SettingsUpdateRequest):
    """Updates and securely persists runtime engine settings."""
    updates = {}
    if payload.provider:
        p_val = payload.provider.lower().strip()
        if p_val not in ("deterministic", "gemini", "groq", "openai", "local"):
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {p_val}")
        settings.AI_PROVIDER = p_val
        updates["AI_PROVIDER"] = p_val

    if payload.gemini_api_key is not None:
        val = payload.gemini_api_key.strip()
        if val and not val.startswith("****"):
            settings.GEMINI_API_KEY = val
            updates["GEMINI_API_KEY"] = val

    if payload.groq_api_key is not None:
        val = payload.groq_api_key.strip()
        if val and not val.startswith("****"):
            settings.GROQ_API_KEY = val
            updates["GROQ_API_KEY"] = val

    if payload.openai_api_key is not None:
        val = payload.openai_api_key.strip()
        if val and not val.startswith("****"):
            settings.OPENAI_API_KEY = val
            updates["OPENAI_API_KEY"] = val

    if payload.openai_base_url:
        settings.OPENAI_BASE_URL = payload.openai_base_url.strip()
        updates["OPENAI_BASE_URL"] = settings.OPENAI_BASE_URL

    if payload.local_model_url:
        settings.LOCAL_MODEL_URL = payload.local_model_url.strip()
        updates["LOCAL_MODEL_URL"] = settings.LOCAL_MODEL_URL

    if payload.max_upload_size_mb and payload.max_upload_size_mb > 0:
        settings.MAX_UPLOAD_SIZE_MB = payload.max_upload_size_mb
        updates["MAX_UPLOAD_SIZE_MB"] = settings.MAX_UPLOAD_SIZE_MB

    if updates:
        save_persisted_settings(updates)
        ai_client.reload_config()

    return SettingsResponse(
        provider=settings.AI_PROVIDER,
        has_gemini_key=bool(settings.GEMINI_API_KEY),
        has_groq_key=bool(settings.GROQ_API_KEY),
        has_openai_key=bool(settings.OPENAI_API_KEY),
        openai_base_url=settings.OPENAI_BASE_URL,
        local_model_url=settings.LOCAL_MODEL_URL,
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        max_uncompressed_size_mb=settings.MAX_UNCOMPRESSED_SIZE_MB,
        is_localhost_only=settings.LOCAL_ONLY
    )

@router.post("/settings/test", response_model=ProviderTestResponse)
async def test_provider(payload: ProviderTestRequest):
    """Tests connectivity to the designated AI reasoning provider."""
    success, message = await ai_client.test_connection(
        provider=payload.provider,
        api_key=payload.api_key,
        base_url=payload.base_url
    )
    return ProviderTestResponse(success=success, message=message)

# -------------------------------------------------------------
# PROJECT MANAGEMENT & UPLOAD
# -------------------------------------------------------------
@router.post("/projects/upload", response_model=ProjectResponse)
async def upload_project(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Safely accepts ZIP upload via streaming chunk writes, validates against zip bombs and path traversal, and extracts."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP archives are supported.")

    # Create project record
    project = Project(
        name=name.strip(),
        description=description.strip(),
        original_archive_name=file.filename,
        status="scanning"
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Save uploaded file via streaming chunk writes with size enforcement
    proj_storage_dir = Path(settings.STORAGE_DIR) / project.id
    proj_storage_dir.mkdir(parents=True, exist_ok=True)
    archive_dest = proj_storage_dir / sanitize_filename(file.filename)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB streaming buffer

    try:
        with open(archive_dest, "wb") as f_dst:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    f_dst.close()
                    if archive_dest.exists():
                        archive_dest.unlink()
                    project.status = "failed"
                    project.error_message = f"Uploaded archive exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE_MB} MB)."
                    await db.commit()
                    raise HTTPException(
                        status_code=413,
                        detail=f"Uploaded archive exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE_MB} MB)."
                    )
                f_dst.write(chunk)
    except HTTPException:
        raise
    except Exception:
        if archive_dest.exists():
            archive_dest.unlink()
        project.status = "failed"
        project.error_message = "File upload failed during streaming write."
        await db.commit()
        raise HTTPException(status_code=500, detail="Failed to stream archive to storage.")

    project.archive_path = str(archive_dest)

    # Safe extraction
    extract_target = Path(settings.PROJECTS_DIR) / project.id
    is_safe, msg, stats = validate_and_extract_zip(
        str(archive_dest),
        str(extract_target),
        max_total_size=settings.MAX_UNCOMPRESSED_SIZE_MB * 1024 * 1024
    )

    if not is_safe:
        if archive_dest.exists():
            archive_dest.unlink()
        if extract_target.exists():
            shutil.rmtree(extract_target, ignore_errors=True)
        project.status = "failed"
        project.error_message = f"Security check failed: {msg}"
        await db.commit()
        raise HTTPException(status_code=400, detail=project.error_message)

    project.extracted_path = str(extract_target)

    # Immediate repository scan
    scanner = RepositoryScanner(str(extract_target))
    scan_results = scanner.scan()

    project.total_files = scan_results["total_files"]
    project.total_lines = scan_results["total_lines"]
    project.ignored_files_count = scan_results["ignored_files"]
    project.primary_language = scan_results["primary_language"]
    project.languages = scan_results["languages"]
    project.frameworks = scan_results["frameworks"]
    project.status = "analyzing"
    await db.commit()

    # Save file records
    for f_info in scan_results["files"]:
        f_rec = FileRecord(
            project_id=project.id,
            relative_path=f_info["relative_path"],
            language=f_info["language"],
            size_bytes=f_info["size_bytes"],
            line_count=f_info["line_count"],
            category=f_info["category"],
            layer=f_info["layer"],
            is_entry_point=f_info["is_entry_point"]
        )
        db.add(f_rec)
    await db.commit()

    # Launch complete static analysis in background
    background_tasks.add_task(run_full_analysis, project.id)

    await db.refresh(project)
    return project

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    return p

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    if not re.match(r"^[a-zA-Z0-9_-]+$", project_id):
        raise HTTPException(status_code=400, detail="Invalid project identifier format.")

    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Guard disk directory cleanup to prevent escaping storage roots
    if p.extracted_path:
        target = Path(p.extracted_path).resolve()
        base_proj = Path(settings.PROJECTS_DIR).resolve()
        try:
            target.relative_to(base_proj)
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
        except ValueError:
            pass

    if p.archive_path:
        archive_parent = Path(p.archive_path).parent.resolve()
        base_storage = Path(settings.STORAGE_DIR).resolve()
        try:
            archive_parent.relative_to(base_storage)
            if archive_parent.exists():
                shutil.rmtree(archive_parent, ignore_errors=True)
        except ValueError:
            pass

    await db.delete(p)
    await db.commit()
    return {"message": f"Project '{p.name}' deleted successfully."}


# -------------------------------------------------------------
# ANALYSIS EXECUTION & STATUS
# -------------------------------------------------------------
async def run_full_analysis(project_id: str):
    """Executes the full static analysis pipeline autonomously."""
    from backend.app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        proj = result.scalar_one_or_none()
        if not proj or not proj.extracted_path:
            return

        try:
            # 1. Fetch file records
            f_res = await session.execute(select(FileRecord).where(FileRecord.project_id == project_id))
            file_records = f_res.scalars().all()
            files_meta = [{"relative_path": fr.relative_path, "language": fr.language, "layer": fr.layer, "line_count": fr.line_count, "category": fr.category} for fr in file_records]

            # 2. Parse AST across files
            parser = CodeParser(proj.extracted_path)
            parsed_files = {}
            for f in files_meta:
                p_res = parser.parse_file(f["relative_path"], f["language"])
                parsed_files[f["relative_path"]] = p_res

                # Store AST entities in DB
                for ent in p_res.get("entities", []):
                    ast_ent = AstEntity(
                        project_id=project_id,
                        file_path=ent["file_path"],
                        name=ent["name"],
                        entity_type=ent["entity_type"],
                        start_line=ent["start_line"],
                        end_line=ent["end_line"],
                        language=ent["language"],
                        signature=ent["signature"],
                        docstring=ent.get("docstring", ""),
                        params=ent.get("params", []),
                        return_type=ent.get("return_type", ""),
                        calls=ent.get("calls", []),
                        evidence=ent.get("evidence", {})
                    )
                    session.add(ast_ent)

            await session.commit()

            # 3. Dependency Graph Construction
            dep_analyzer = DependencyGraphAnalyzer(proj.extracted_path)
            dep_analyzer.build_graph(files_meta, parsed_files)
            dep_data = dep_analyzer.to_dict()

            for edge in dep_data.get("edges", []):
                dep_edge = DependencyEdge(
                    project_id=project_id,
                    source=edge["source"],
                    target=edge["target"],
                    edge_type=edge.get("edge_type", "import"),
                    confidence=edge.get("confidence", "confirmed"),
                    evidence=edge.get("evidence", {})
                )
                session.add(dep_edge)

            await session.commit()

            # 4. API Discovery
            api_discoverer = ApiDiscoverer(proj.extracted_path)
            api_data = api_discoverer.discover_endpoints(files_meta)
            for ep in api_data.get("endpoints", []):
                api_ep = ApiEndpoint(
                    project_id=project_id,
                    method=ep["method"],
                    path=ep["path"],
                    framework=ep.get("framework", "FastAPI"),
                    file_path=ep["file_path"],
                    line_number=ep["line_number"],
                    handler_name=ep.get("handler_name", ""),
                    auth_middleware=ep.get("auth_middleware", ""),
                    parameters=ep.get("parameters", []),
                    request_schema=ep.get("request_schema", {}),
                    response_schema=ep.get("response_schema", {}),
                    related_models=ep.get("related_models", []),
                    evidence=ep.get("evidence", {})
                )
                session.add(api_ep)

            await session.commit()

            # 5. Database Schema Reverse Engineering
            db_analyzer = DatabaseAnalyzer(proj.extracted_path)
            db_data = db_analyzer.analyze_repository(files_meta)
            for m in db_data.get("models", []):
                db_m = DatabaseModel(
                    project_id=project_id,
                    name=m["name"],
                    orm_framework=m.get("orm_framework", "ORM"),
                    file_path=m["file_path"],
                    line_number=m["line_number"],
                    fields=m.get("fields", []),
                    relationships=m.get("relationships", []),
                    evidence=m.get("evidence", {})
                )
                session.add(db_m)

            await session.commit()

            # 6. Architecture Reconstruction
            arch_recon = ArchitectureReconstructor(proj.extracted_path)
            arch_data = arch_recon.reconstruct(
                files=files_meta,
                parsed_files=parsed_files,
                dependencies=dep_data,
                api_endpoints=api_data.get("endpoints", []),
                db_models=db_data.get("models", [])
            )
            for c in arch_data.get("components", []):
                arch_comp = ArchitectureComponent(
                    project_id=project_id,
                    name=c["name"],
                    layer=c["layer"],
                    files=c.get("files", []),
                    responsibilities=c.get("responsibilities", []),
                    incoming_connections=c.get("incoming_connections", []),
                    outgoing_connections=c.get("outgoing_connections", []),
                    evidence=c.get("evidence", {})
                )
                session.add(arch_comp)

            await session.commit()

            # 7. Workflow Reconstruction
            wf_recon = WorkflowReconstructor()
            workflows = wf_recon.reconstruct_workflows(
                api_endpoints=api_data.get("endpoints", []),
                parsed_files=parsed_files,
                db_models=db_data.get("models", []),
                files_metadata=files_meta,
                root_dir=proj.extracted_path
            )
            for wf in workflows:
                wf_seq = WorkflowSequence(
                    project_id=project_id,
                    name=wf["name"],
                    trigger=wf["trigger"],
                    completeness=wf.get("completeness", "complete"),
                    missing_evidence=wf.get("missing_evidence", []),
                    steps=wf["steps"],
                    evidence=wf["evidence"]
                )
                session.add(wf_seq)

            await session.commit()

            # 8. Health Analyzer
            health_analyzer = HealthAnalyzer(proj.extracted_path)
            health_report = health_analyzer.analyze(
                files=files_meta,
                parsed_files=parsed_files,
                dependencies=dep_data,
                frameworks=proj.frameworks or []
            )
            proj.health_score = health_report["health_score"]
            for h in health_report.get("findings", []):
                h_finding = HealthFinding(
                    project_id=project_id,
                    category=h["category"],
                    title=h["title"],
                    description=h["description"],
                    severity=h["severity"],
                    affected_files=h.get("affected_files", []),
                    evidence=h.get("evidence", {})
                )
                session.add(h_finding)

            await session.commit()

            # 9. Test Reconstruction
            test_recon = TestReconstructor()
            generated_tests = test_recon.generate_tests(
                files=files_meta,
                parsed_files=parsed_files,
                api_endpoints=api_data.get("endpoints", []),
                db_models=db_data.get("models", []),
                framework="pytest" if proj.primary_language == "Python" else "vitest"
            )
            for t in generated_tests:
                g_test = GeneratedTest(
                    project_id=project_id,
                    target_file=t["target_file"],
                    target_symbol=t["target_symbol"],
                    test_framework=t["test_framework"],
                    test_type=t["test_type"],
                    test_name=t["test_name"],
                    code=t["code"]
                )
                session.add(g_test)

            proj.status = "completed"
            await session.commit()

        except Exception as e:
            proj.status = "failed"
            proj.error_message = f"Analysis error: {str(e)}"
            await session.commit()

@router.post("/projects/{project_id}/analyze")
async def trigger_analysis(project_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    p.status = "analyzing"
    p.error_message = ""
    await db.commit()

    background_tasks.add_task(run_full_analysis, project_id)
    return {"status": "analyzing", "message": "Analysis pipeline queued."}

@router.get("/projects/{project_id}/analysis/status")
async def get_analysis_status(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {
        "status": p.status,
        "error_message": p.error_message,
        "health_score": p.health_score,
        "total_files": p.total_files,
        "total_lines": p.total_lines
    }

# -------------------------------------------------------------
# OVERVIEW & FILE EXPLORER
# -------------------------------------------------------------
@router.get("/projects/{project_id}/overview", response_model=ProjectOverviewResponse)
async def get_overview(project_id: str, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    files = (await db.execute(select(FileRecord).where(FileRecord.project_id == project_id))).scalars().all()
    endpoints_cnt = len((await db.execute(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id))).scalars().all())
    models_cnt = len((await db.execute(select(DatabaseModel).where(DatabaseModel.project_id == project_id))).scalars().all())
    entities_cnt = len((await db.execute(select(AstEntity).where(AstEntity.project_id == project_id))).scalars().all())
    components_cnt = len((await db.execute(select(ArchitectureComponent).where(ArchitectureComponent.project_id == project_id))).scalars().all())

    cat_counts = {}
    layer_counts = {}
    for f in files:
        cat_counts[f.category] = cat_counts.get(f.category, 0) + 1
        layer_counts[f.layer] = layer_counts.get(f.layer, 0) + 1

    return ProjectOverviewResponse(
        project=ProjectResponse.model_validate(p),
        files_count=len(files),
        lines_count=p.total_lines,
        endpoints_count=endpoints_cnt,
        models_count=models_cnt,
        entities_count=entities_cnt,
        components_count=components_cnt,
        health_score=p.health_score,
        categories_breakdown=cat_counts,
        layers_breakdown=layer_counts
    )

@router.get("/projects/{project_id}/files", response_model=List[FileRecordSchema])
async def list_project_files(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FileRecord).where(FileRecord.project_id == project_id))
    return result.scalars().all()

@router.get("/projects/{project_id}/file-content")
async def get_file_content(project_id: str, file_path: str, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p or not p.extracted_path:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Guard against path traversal
    full_path = (Path(p.extracted_path) / file_path).resolve()
    try:
        full_path.relative_to(Path(p.extracted_path).resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="File does not exist.")

    if full_path.is_symlink():
        raise HTTPException(status_code=400, detail="Access to symlinks is prohibited.")

    if full_path.stat().st_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds maximum viewable size (5 MB).")

    try:
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        return {"content": content, "file_path": file_path}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read file content.")

# -------------------------------------------------------------
# AST EXPLORER
# -------------------------------------------------------------
@router.get("/projects/{project_id}/ast")
async def get_project_ast(project_id: str, file_path: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    query = select(AstEntity).where(AstEntity.project_id == project_id)
    if file_path:
        query = query.where(AstEntity.file_path == file_path)

    entities = (await db.execute(query)).scalars().all()

    # If specific file requested, generate hierarchical AST tree node
    ast_tree = None
    if file_path and p.extracted_path:
        parser = CodeParser(p.extracted_path)
        f_rec = (await db.execute(select(FileRecord).where(FileRecord.project_id == project_id, FileRecord.relative_path == file_path))).scalar_one_or_none()
        lang = f_rec.language if f_rec else "Python"
        p_res = parser.parse_file(file_path, lang)
        ast_tree = p_res.get("ast_tree")

    return {
        "entities": entities,
        "ast_tree": ast_tree
    }

# -------------------------------------------------------------
# DEPENDENCY GRAPH & IMPACT ANALYSIS
# -------------------------------------------------------------
@router.get("/projects/{project_id}/dependencies", response_model=DependencyGraphResponse)
async def get_dependencies(project_id: str, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p or not p.extracted_path:
        raise HTTPException(status_code=404, detail="Project not found.")

    files = (await db.execute(select(FileRecord).where(FileRecord.project_id == project_id))).scalars().all()
    files_meta = [{"relative_path": fr.relative_path, "language": fr.language, "layer": fr.layer, "line_count": fr.line_count} for fr in files]

    parser = CodeParser(p.extracted_path)
    parsed_files = {f["relative_path"]: parser.parse_file(f["relative_path"], f["language"]) for f in files_meta}

    analyzer = DependencyGraphAnalyzer(p.extracted_path)
    analyzer.build_graph(files_meta, parsed_files)
    data = analyzer.to_dict()

    return DependencyGraphResponse(
        nodes=data["nodes"],
        edges=data["edges"],
        circular_dependencies=data["circular_dependencies"],
        high_dependency_modules=data["high_dependency_modules"],
        isolated_modules=data["isolated_modules"]
    )

@router.post("/projects/{project_id}/dependencies/impact", response_model=ImpactAnalysisResponse)
async def analyze_impact(project_id: str, req: ImpactAnalysisRequest, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p or not p.extracted_path:
        raise HTTPException(status_code=404, detail="Project not found.")

    files = (await db.execute(select(FileRecord).where(FileRecord.project_id == project_id))).scalars().all()
    files_meta = [{"relative_path": fr.relative_path, "language": fr.language, "layer": fr.layer, "line_count": fr.line_count} for fr in files]

    parser = CodeParser(p.extracted_path)
    parsed_files = {f["relative_path"]: parser.parse_file(f["relative_path"], f["language"]) for f in files_meta}

    analyzer = DependencyGraphAnalyzer(p.extracted_path)
    analyzer.build_graph(files_meta, parsed_files)
    impact = analyzer.analyze_impact(req.node_id, req.depth)

    return ImpactAnalysisResponse(**impact)

# -------------------------------------------------------------
# ARCHITECTURE RECONSTRUCTION
# -------------------------------------------------------------
@router.get("/projects/{project_id}/architecture", response_model=ArchitectureResponse)
async def get_architecture(project_id: str, db: AsyncSession = Depends(get_db)):
    components = (await db.execute(select(ArchitectureComponent).where(ArchitectureComponent.project_id == project_id))).scalars().all()
    layers = list(dict.fromkeys([c.layer for c in components]))
    
    connections = []
    for i in range(len(layers) - 1):
        connections.append({
            "source_layer": layers[i],
            "target_layer": layers[i + 1],
            "description": f"Requests flow from {layers[i]} to {layers[i + 1]}"
        })

    return ArchitectureResponse(
        layers=layers,
        components=components,
        connections=connections
    )

# -------------------------------------------------------------
# DATABASE REVERSE ENGINEERING
# -------------------------------------------------------------
@router.get("/projects/{project_id}/database", response_model=DatabaseSchemaResponse)
async def get_database_schema(project_id: str, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    models = (await db.execute(select(DatabaseModel).where(DatabaseModel.project_id == project_id))).scalars().all()

    # Build ER graph
    analyzer = DatabaseAnalyzer(p.extracted_path if p else ".")
    models_dict = [
        {
            "id": m.id,
            "name": m.name,
            "table_name": m.name.lower() + "s",
            "orm_framework": m.orm_framework,
            "file_path": m.file_path,
            "line_number": m.line_number,
            "fields": m.fields,
            "relationships": m.relationships,
            "evidence": m.evidence
        }
        for m in models
    ]
    er_nodes, er_edges = analyzer._build_er_graph(models_dict)

    return DatabaseSchemaResponse(
        models=models_dict,
        er_nodes=er_nodes,
        er_edges=er_edges
    )

# -------------------------------------------------------------
# API EXPLORER
# -------------------------------------------------------------
@router.get("/projects/{project_id}/apis", response_model=ApiExplorerResponse)
async def get_apis(project_id: str, db: AsyncSession = Depends(get_db)):
    endpoints = (await db.execute(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id))).scalars().all()

    methods_count: Dict[str, int] = {}
    frameworks: set = set()
    ep_list = []
    for ep in endpoints:
        ep_dict = {
            "id": ep.id,
            "method": ep.method,
            "path": ep.path,
            "framework": ep.framework,
            "file_path": ep.file_path,
            "line_number": ep.line_number,
            "handler_name": ep.handler_name,
            "auth_middleware": ep.auth_middleware,
            "parameters": ep.parameters,
            "request_schema": ep.request_schema,
            "response_schema": ep.response_schema,
            "related_models": ep.related_models,
            "evidence": ep.evidence
        }
        ep_list.append(ep_dict)
        methods_count[ep.method] = methods_count.get(ep.method, 0) + 1
        if ep.framework:
            frameworks.add(ep.framework)

    discoverer = ApiDiscoverer(".")
    openapi = discoverer._build_openapi(ep_list)

    return ApiExplorerResponse(
        endpoints=ep_list,
        total_endpoints=len(ep_list),
        frameworks=list(frameworks),
        methods=methods_count,
        openapi_spec=openapi
    )

# -------------------------------------------------------------
# WORKFLOWS
# -------------------------------------------------------------
@router.get("/projects/{project_id}/workflows", response_model=WorkflowsResponse)
async def get_workflows(project_id: str, db: AsyncSession = Depends(get_db)):
    workflows = (await db.execute(select(WorkflowSequence).where(WorkflowSequence.project_id == project_id))).scalars().all()
    return WorkflowsResponse(workflows=workflows)

# -------------------------------------------------------------
# SOFTWARE HEALTH REPORT
# -------------------------------------------------------------
@router.get("/projects/{project_id}/health", response_model=HealthReportResponse)
async def get_health_report(project_id: str, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    findings = (await db.execute(select(HealthFinding).where(HealthFinding.project_id == project_id))).scalars().all()
    
    score = p.health_score
    if score >= 90: grade = "A"
    elif score >= 80: grade = "B"
    elif score >= 70: grade = "C"
    elif score >= 60: grade = "D"
    else: grade = "F"

    sev_counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    cat_counts: Dict[str, int] = {}
    for f in findings:
        sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
        cat_counts[f.category] = cat_counts.get(f.category, 0) + 1

    return HealthReportResponse(
        health_score=score,
        grade=grade,
        findings=findings,
        summary_by_severity=sev_counts,
        summary_by_category=cat_counts
    )

# -------------------------------------------------------------
# AI ASSISTANT CHAT
# -------------------------------------------------------------
@router.post("/projects/{project_id}/assistant/chat", response_model=AiChatResponse)
async def assistant_chat(project_id: str, req: AiChatRequest, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Gather repository context
    endpoints = (await db.execute(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id))).scalars().all()
    models = (await db.execute(select(DatabaseModel).where(DatabaseModel.project_id == project_id))).scalars().all()
    components = (await db.execute(select(ArchitectureComponent).where(ArchitectureComponent.project_id == project_id))).scalars().all()
    entities = (await db.execute(select(AstEntity).where(AstEntity.project_id == project_id))).scalars().all()

    ctx = {
        "total_files": p.total_files,
        "endpoints": [{"method": e.method, "path": e.path, "handler_name": e.handler_name, "file_path": e.file_path, "line_number": e.line_number, "auth_middleware": e.auth_middleware} for e in endpoints],
        "models": [{"name": m.name, "orm_framework": m.orm_framework, "file_path": m.file_path, "line_number": m.line_number, "fields": m.fields, "relationships": m.relationships} for m in models],
        "components": [{"name": c.name, "layer": c.layer, "files": c.files, "responsibilities": c.responsibilities} for c in components],
        "entities": [{"name": ent.name, "entity_type": ent.entity_type, "file_path": ent.file_path, "start_line": ent.start_line, "calls": ent.calls} for ent in entities[:100]]
    }

    ans = await ai_client.answer_question(req.message, ctx, req.history)

    # Persist message
    user_msg = ConversationMessage(project_id=project_id, role="user", content=req.message, sources=[])
    ai_msg = ConversationMessage(project_id=project_id, role="assistant", content=ans["message"], sources=ans["sources"], confidence=ans["confidence"])
    db.add(user_msg)
    db.add(ai_msg)
    await db.commit()

    return AiChatResponse(**ans)

# -------------------------------------------------------------
# DOCUMENTATION & EXPORT
# -------------------------------------------------------------
@router.get("/projects/{project_id}/documentation")
async def get_documentation(project_id: str, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    overview_res = await get_overview(project_id, db)
    endpoints = (await db.execute(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id))).scalars().all()
    models = (await db.execute(select(DatabaseModel).where(DatabaseModel.project_id == project_id))).scalars().all()
    components = (await db.execute(select(ArchitectureComponent).where(ArchitectureComponent.project_id == project_id))).scalars().all()
    findings = (await db.execute(select(HealthFinding).where(HealthFinding.project_id == project_id))).scalars().all()
    workflows = (await db.execute(select(WorkflowSequence).where(WorkflowSequence.project_id == project_id))).scalars().all()
    tests = (await db.execute(select(GeneratedTest).where(GeneratedTest.project_id == project_id))).scalars().all()

    dep_res = await get_dependencies(project_id, db)

    analysis_ctx = {
        "endpoints": [e.__dict__ for e in endpoints],
        "models": [m.__dict__ for m in models],
        "components": [c.__dict__ for c in components],
        "dependencies": dep_res.model_dump(),
        "findings": [f.__dict__ for f in findings],
        "workflows": [w.__dict__ for w in workflows],
        "tests": [t.__dict__ for t in tests]
    }

    markdown_doc = doc_gen.generate_markdown(p.__dict__, overview_res.model_dump(), analysis_ctx)
    return {"markdown": markdown_doc, "project_id": project_id}

@router.api_route("/projects/{project_id}/documentation/export", methods=["GET", "POST"])
async def export_documentation(project_id: str, export_format: str = "markdown", db: AsyncSession = Depends(get_db)):
    doc_res = await get_documentation(project_id, db)
    markdown_doc = doc_res["markdown"]

    export_dir = Path(settings.STORAGE_DIR) / project_id / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    if export_format == "pdf":
        pdf_path = export_dir / f"codex_report_{project_id[:8]}.pdf"
        doc_gen.generate_pdf(markdown_doc, str(pdf_path))
        return FileResponse(str(pdf_path), media_type="application/pdf", filename=f"codex_report_{project_id[:8]}.pdf")
    elif export_format == "json":
        json_path = export_dir / f"codex_report_{project_id[:8]}.json"
        json_path.write_text(json.dumps(doc_res, indent=2), encoding="utf-8")
        return FileResponse(str(json_path), media_type="application/json", filename=f"codex_report_{project_id[:8]}.json")
    else:
        md_path = export_dir / f"codex_report_{project_id[:8]}.md"
        md_path.write_text(markdown_doc, encoding="utf-8")
        return FileResponse(str(md_path), media_type="text/markdown", filename=f"codex_report_{project_id[:8]}.md")

# -------------------------------------------------------------
# TEST RECONSTRUCTION & EXPORT
# -------------------------------------------------------------
@router.get("/projects/{project_id}/tests", response_model=List[GeneratedTestSchema])
async def get_generated_tests(project_id: str, db: AsyncSession = Depends(get_db)):
    tests = (await db.execute(select(GeneratedTest).where(GeneratedTest.project_id == project_id))).scalars().all()
    return tests

@router.post("/projects/{project_id}/tests/generate", response_model=List[GeneratedTestSchema])
async def generate_project_tests(project_id: str, req: TestGenerateRequest, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    files = (await db.execute(select(FileRecord).where(FileRecord.project_id == project_id))).scalars().all()
    files_meta = [{"relative_path": fr.relative_path, "language": fr.language, "layer": fr.layer, "line_count": fr.line_count} for fr in files]

    parser = CodeParser(p.extracted_path)
    parsed_files = {f["relative_path"]: parser.parse_file(f["relative_path"], f["language"]) for f in files_meta}

    endpoints = (await db.execute(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id))).scalars().all()
    models = (await db.execute(select(DatabaseModel).where(DatabaseModel.project_id == project_id))).scalars().all()

    test_recon = TestReconstructor()
    tests = test_recon.generate_tests(
        files=files_meta,
        parsed_files=parsed_files,
        api_endpoints=[ep.__dict__ for ep in endpoints],
        db_models=[m.__dict__ for m in models],
        target_file=req.target_file,
        framework=req.framework or "pytest"
    )

    created_tests = []
    for t in tests:
        g = GeneratedTest(
            project_id=project_id,
            target_file=t["target_file"],
            target_symbol=t["target_symbol"],
            test_framework=t["test_framework"],
            test_type=t["test_type"],
            test_name=t["test_name"],
            code=t["code"]
        )
        db.add(g)
        created_tests.append(g)

    await db.commit()
    for g in created_tests:
        await db.refresh(g)

    return created_tests
