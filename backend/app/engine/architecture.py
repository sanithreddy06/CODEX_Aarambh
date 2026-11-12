from typing import Dict, List, Any
from pathlib import Path
from collections import defaultdict

LAYER_ORDER = [
    "Presentation Layer",
    "API Layer",
    "Business Logic Layer",
    "Data Access Layer",
    "Database Layer",
    "External Services"
]

class ArchitectureReconstructor:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()

    def reconstruct(
        self,
        files: List[Dict[str, Any]],
        parsed_files: Dict[str, Dict[str, Any]],
        dependencies: Dict[str, Any],
        api_endpoints: List[Dict[str, Any]],
        db_models: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesizes files, dependencies, endpoints, and models to reconstruct
        the application's multi-tier architecture with verifiable evidence.
        """
        layer_components: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        active_layers = set()
        components = []

        # 1. Presentation Layer (Frontend / UI / Templates)
        frontend_files = [f["relative_path"] for f in files if f.get("category") == "frontend" or f.get("layer") == "presentation"]
        if frontend_files:
            active_layers.add("Presentation Layer")
            components.append({
                "id": "comp_presentation",
                "name": "User Interface & Client Views",
                "layer": "Presentation Layer",
                "files": frontend_files,
                "responsibilities": [
                    "Renders user interface and views",
                    "Handles client-side routing and state",
                    "Dispatches requests to backend API Layer"
                ],
                "incoming_connections": ["User Actions / Browser Events"],
                "outgoing_connections": ["API Gateway / Route Controllers"],
                "evidence": {
                    "detection_method": "static_analysis",
                    "file_count": len(frontend_files),
                    "confidence": "high",
                    "sample_files": frontend_files[:5]
                }
            })

        # 2. API Layer (Routers, Controllers, Gateways)
        api_files = [f["relative_path"] for f in files if f.get("layer") == "api"] or [ep["file_path"] for ep in api_endpoints]
        api_files = list(set(api_files))
        if api_files or api_endpoints:
            active_layers.add("API Layer")
            methods = list(set(ep.get("method", "GET") for ep in api_endpoints))
            frameworks = list(set(ep.get("framework", "FastAPI") for ep in api_endpoints))
            components.append({
                "id": "comp_api",
                "name": f"API Gateway & Controllers ({', '.join(frameworks) or 'HTTP'})",
                "layer": "API Layer",
                "files": api_files,
                "responsibilities": [
                    f"Exposes {len(api_endpoints)} REST/HTTP endpoints ({', '.join(methods)})",
                    "Performs input validation and schema serialization",
                    "Dispatches verified payloads to Business Logic Services"
                ],
                "incoming_connections": ["Presentation Layer"],
                "outgoing_connections": ["Business Logic Services"],
                "evidence": {
                    "detection_method": "ast_routing_extraction",
                    "endpoint_count": len(api_endpoints),
                    "confidence": "high",
                    "frameworks": frameworks
                }
            })

        # 3. Business Logic Layer (Services, Domain Handlers)
        service_files = [f["relative_path"] for f in files if f.get("layer") == "business_logic"]
        if service_files:
            active_layers.add("Business Logic Layer")
            components.append({
                "id": "comp_business_logic",
                "name": "Domain Services & Core Business Engine",
                "layer": "Business Logic Layer",
                "files": service_files,
                "responsibilities": [
                    "Executes core application logic and algorithms",
                    "Enforces domain rules, authorization and workflows",
                    "Orchestrates transactions with Data Access & External Integrations"
                ],
                "incoming_connections": ["API Gateway & Controllers"],
                "outgoing_connections": ["Data Access Layer / ORM Models", "External Services"],
                "evidence": {
                    "detection_method": "ast_service_pattern",
                    "file_count": len(service_files),
                    "confidence": "high",
                    "sample_files": service_files[:5]
                }
            })

        # 4. Data Access Layer (Repositories, Queries, ORM wrappers)
        repo_files = [f["relative_path"] for f in files if "repo" in f["relative_path"].lower() or "dao" in f["relative_path"].lower() or "database" in f["relative_path"].lower()]
        if repo_files:
            active_layers.add("Data Access Layer")
            components.append({
                "id": "comp_data_access",
                "name": "Repository & Data Access Layer",
                "layer": "Data Access Layer",
                "files": repo_files,
                "responsibilities": [
                    "Abstracts persistence operations",
                    "Executes database queries and mutations",
                    "Manages connection sessions and pooling"
                ],
                "incoming_connections": ["Domain Services & Core Business Engine"],
                "outgoing_connections": ["Database Models & Tables"],
                "evidence": {
                    "detection_method": "static_analysis",
                    "file_count": len(repo_files),
                    "confidence": "high"
                }
            })

        # 5. Database Layer (Entities, ORM Schemas, Tables)
        db_files = [f["relative_path"] for f in files if f.get("category") == "database"] or [m["file_path"] for m in db_models]
        db_files = list(set(db_files))
        if db_files or db_models:
            active_layers.add("Database Layer")
            model_names = [m.get("name") for m in db_models]
            orms = list(set(m.get("orm_framework", "SQLAlchemy") for m in db_models))
            components.append({
                "id": "comp_database",
                "name": f"Database Entities & Schema ({', '.join(orms) or 'ORM'})",
                "layer": "Database Layer",
                "files": db_files,
                "responsibilities": [
                    f"Defines {len(db_models)} persistent entities: {', '.join(model_names[:6])}",
                    "Maintains referential integrity and relational constraints",
                    "Handles migrations and schema evolution"
                ],
                "incoming_connections": ["Repository & Data Access Layer" if repo_files else "Domain Services & Core Business Engine"],
                "outgoing_connections": [],
                "evidence": {
                    "detection_method": "ast_orm_model_discovery",
                    "model_count": len(db_models),
                    "confidence": "confirmed",
                    "discovered_models": model_names
                }
            })

        # 6. External Services & Config
        ext_files = [f["relative_path"] for f in files if any(w in f["relative_path"].lower() for w in ["external", "client", "stripe", "mail", "aws", "s3", "auth0", "oauth"])]
        if ext_files:
            active_layers.add("External Services")
            components.append({
                "id": "comp_external",
                "name": "External Service Integrations",
                "layer": "External Services",
                "files": ext_files,
                "responsibilities": [
                    "Manages external HTTP APIs and webhooks",
                    "Handles third-party authentication and payments"
                ],
                "incoming_connections": ["Domain Services & Core Business Engine"],
                "outgoing_connections": ["Third-party Cloud APIs"],
                "evidence": {
                    "detection_method": "static_analysis",
                    "file_count": len(ext_files),
                    "confidence": "medium"
                }
            })

        # Calculate architecture connections
        connections = []
        ordered_active = [l for l in LAYER_ORDER if l in active_layers]
        for i in range(len(ordered_active) - 1):
            src_l = ordered_active[i]
            tgt_l = ordered_active[i + 1]
            connections.append({
                "source_layer": src_l,
                "target_layer": tgt_l,
                "description": f"Requests flow from {src_l} to {tgt_l}",
                "confidence": "confirmed"
            })

        return {
            "layers": ordered_active,
            "components": components,
            "connections": connections
        }
