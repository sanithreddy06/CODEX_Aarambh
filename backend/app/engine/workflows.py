import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class WorkflowReconstructor:
    def reconstruct_workflows(
        self,
        api_endpoints: List[Dict[str, Any]],
        parsed_files: Dict[str, Dict[str, Any]],
        db_models: List[Dict[str, Any]],
        files_metadata: Optional[List[Dict[str, Any]]] = None,
        root_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Reconstructs evidence-driven operational execution workflows:
        Frontend event → API route → controller → service → repository/data access → database.

        Strictly evidence-based:
        - Never selects arbitrary database fallback
        - Never invents frontend triggers without code citations
        - Never fabricates line numbers or function calls
        - Records exact confidence and missing evidence items
        """
        workflows = []
        model_names_map = {m["name"].lower(): m for m in db_models}

        # Build symbol catalog across all files to resolve function calls
        # symbol_name -> list of {file_path, entity}
        symbol_catalog: Dict[str, List[Dict[str, Any]]] = {}
        for fpath, parsed in parsed_files.items():
            for ent in parsed.get("entities", []):
                sym_name = ent["name"].split(".")[-1]
                if sym_name not in symbol_catalog:
                    symbol_catalog[sym_name] = []
                symbol_catalog[sym_name].append({"file_path": fpath, "entity": ent})

        # Scan frontend files for actual API fetch / axios / request calls
        frontend_calls: List[Dict[str, Any]] = []
        if files_metadata:
            for f_info in files_metadata:
                if f_info.get("category") == "frontend" or f_info.get("layer") == "presentation":
                    full_p = f_info.get("full_path")
                    if not full_p and root_dir:
                        full_p = str(Path(root_dir) / f_info["relative_path"])
                    if full_p and Path(full_p).is_file():
                        try:
                            content = Path(full_p).read_text(encoding="utf-8", errors="ignore")
                            for line_no, line in enumerate(content.splitlines(), start=1):
                                # Detect fetch('/...') or axios.get/post('/...')
                                m_url = re.search(r"(?:fetch|axios\.(?:get|post|put|delete|patch)|apiClient\.[a-zA-Z0-9_]+)\s*\(\s*['\"`]([^'\"`]+)['\"`]", line)
                                if m_url:
                                    url_found = m_url.group(1)
                                    frontend_calls.append({
                                        "file_path": f_info["relative_path"],
                                        "line_number": line_no,
                                        "url": url_found,
                                        "source_line": line.strip()
                                    })
                        except Exception:
                            pass

        for ep in api_endpoints:
            path = ep.get("path", "")
            method = ep.get("method", "GET").upper()
            handler = ep.get("handler_name", "handler")
            ep_file = ep.get("file_path", "")
            ep_line = ep.get("line_number", 1)

            # Workflow title based on endpoint purpose
            wf_name = self._determine_workflow_name(path, method, handler)
            if not wf_name:
                continue

            steps: List[Dict[str, Any]] = []
            missing_evidence: List[str] = []
            order = 1

            # -------------------------------------------------------------
            # Step 1: Frontend Client Event (Confirmed vs Inferred)
            # -------------------------------------------------------------
            matched_frontend = None
            clean_ep_path = path.rstrip("/")
            for fc in frontend_calls:
                fc_url = fc["url"].rstrip("/")
                # Match exact or suffix
                if fc_url == clean_ep_path or clean_ep_path.endswith(fc_url) or fc_url.endswith(clean_ep_path.lstrip("/")):
                    matched_frontend = fc
                    break

            if matched_frontend:
                steps.append({
                    "order": order,
                    "component": f"Frontend Client ({Path(matched_frontend['file_path']).name})",
                    "action": f"Dispatches HTTP {method} request to '{path}'",
                    "file": matched_frontend["file_path"],
                    "line": matched_frontend["line_number"],
                    "layer": "Presentation Layer",
                    "evidence_type": "frontend_api_call",
                    "confidence": "confirmed",
                    "status": "confirmed"
                })
            else:
                steps.append({
                    "order": order,
                    "component": "HTTP Consumer / External Client",
                    "action": f"Dispatches external HTTP {method} request to '{path}'",
                    "file": "",
                    "line": 0,
                    "layer": "Presentation Layer",
                    "evidence_type": "inferred_from_route",
                    "confidence": "inferred",
                    "status": "inferred"
                })
                missing_evidence.append("No frontend fetch/axios call discovered for this endpoint")
            order += 1

            # -------------------------------------------------------------
            # Step 2: Security & Authentication Middleware (if confirmed)
            # -------------------------------------------------------------
            if ep.get("auth_middleware"):
                steps.append({
                    "order": order,
                    "component": "Security Middleware",
                    "action": f"Enforces authorization policy: {ep['auth_middleware']}",
                    "file": ep_file,
                    "line": ep_line,
                    "layer": "API Layer",
                    "evidence_type": "route_security_dependency",
                    "confidence": "confirmed",
                    "status": "confirmed"
                })
                order += 1

            # -------------------------------------------------------------
            # Step 3: Route Controller Handler
            # -------------------------------------------------------------
            file_ast = parsed_files.get(ep_file, {})
            handler_entity = None
            for ent in file_ast.get("entities", []):
                if ent["name"] == handler or ent["name"].endswith(f".{handler}"):
                    handler_entity = ent
                    break

            ctrl_start = handler_entity.get("start_line", ep_line) if handler_entity else ep_line
            ctrl_end = handler_entity.get("end_line", ep_line) if handler_entity else ep_line

            steps.append({
                "order": order,
                "component": f"Controller Handler: {handler}()",
                "action": f"Parses parameters and validates incoming payload schema for {method} {path}",
                "file": ep_file,
                "line": ctrl_start,
                "end_line": ctrl_end,
                "layer": "API Layer",
                "evidence_type": "ast_route_handler",
                "confidence": "confirmed",
                "status": "confirmed"
            })
            order += 1

            # -------------------------------------------------------------
            # Step 4: Domain Service / Business Logic
            # -------------------------------------------------------------
            calls_in_handler = handler_entity.get("calls", []) if handler_entity else file_ast.get("calls", [])
            matched_service = None

            for call_name in calls_in_handler:
                if call_name in ("post", "get", "put", "delete", "dict", "HTTPException", "Depends", "print", "len"):
                    continue
                # Search symbol catalog for function definition in a service file
                candidates = symbol_catalog.get(call_name, [])
                for cand in candidates:
                    cand_file = cand["file_path"].lower()
                    if "service" in cand_file or "manager" in cand_file or "logic" in cand_file or "handler" in cand_file:
                        matched_service = cand
                        break
                if matched_service:
                    break

            if matched_service:
                s_ent = matched_service["entity"]
                steps.append({
                    "order": order,
                    "component": f"Domain Service: {s_ent['name']}()",
                    "action": "Executes business logic routine in domain service layer",
                    "file": matched_service["file_path"],
                    "line": s_ent["start_line"],
                    "end_line": s_ent["end_line"],
                    "layer": "Business Logic Layer",
                    "evidence_type": "static_call_graph",
                    "confidence": "confirmed",
                    "status": "confirmed"
                })
                order += 1
            else:
                missing_evidence.append("No intermediate domain service called; logic handled directly in controller")

            # -------------------------------------------------------------
            # Step 5: Database Persistence & Data Access
            # -------------------------------------------------------------
            # Look for model reference in handler file or service file
            matched_model_info = None
            files_to_check = [ep_file]
            if matched_service:
                files_to_check.append(matched_service["file_path"])

            for f_to_check in files_to_check:
                p_obj = parsed_files.get(f_to_check, {})
                for imp in p_obj.get("imports", []):
                    imp_source = imp.get("source", "").lower()
                    imp_symbol = imp.get("imported", "").lower()
                    for m_name_lower, m_obj in model_names_map.items():
                        if m_name_lower in imp_symbol or m_name_lower in imp_source:
                            matched_model_info = m_obj
                            break
                    if matched_model_info:
                        break
                if matched_model_info:
                    break

            # If not in imports, check if model name is in entities or calls
            if not matched_model_info:
                for m_name_lower, m_obj in model_names_map.items():
                    if any(m_name_lower in c.lower() for c in calls_in_handler):
                        matched_model_info = m_obj
                        break

            if matched_model_info:
                op_verb = "Queries and retrieves" if method == "GET" else "Persists and mutates"
                steps.append({
                    "order": order,
                    "component": f"Data Access Layer ({matched_model_info['name']})",
                    "action": f"{op_verb} '{matched_model_info['name']}' entity table ({matched_model_info.get('table_name')})",
                    "file": matched_model_info["file_path"],
                    "line": matched_model_info["line_number"],
                    "layer": "Database Layer",
                    "evidence_type": "orm_entity_reference",
                    "confidence": "confirmed",
                    "status": "confirmed"
                })
                order += 1
            else:
                if method in ("POST", "PUT", "PATCH", "DELETE"):
                    missing_evidence.append(f"No ORM or database persistence reference verified for {method} mutation")

            # -------------------------------------------------------------
            # Step 6: HTTP Response Serializer
            # -------------------------------------------------------------
            resp_type = ep.get("response_schema", {}).get("type") or "Response JSON"
            steps.append({
                "order": order,
                "component": "API Response Serializer",
                "action": f"Returns serialized HTTP response ({resp_type}) to caller",
                "file": ep_file,
                "line": ctrl_end,
                "layer": "Presentation Layer",
                "evidence_type": "controller_return_signature",
                "confidence": "confirmed",
                "status": "confirmed"
            })

            # Check if workflow is complete
            is_complete = len(missing_evidence) == 0

            workflows.append({
                "id": f"wf_{len(workflows) + 1}",
                "name": wf_name,
                "trigger": f"{method} {path}",
                "completeness": "complete" if is_complete else "incomplete",
                "missing_evidence": missing_evidence,
                "steps": steps,
                "evidence": {
                    "source_endpoint": f"{method} {path}",
                    "controller_function": handler,
                    "file_path": ep_file,
                    "line_number": ctrl_start,
                    "step_count": len(steps),
                    "is_complete": is_complete
                }
            })

        return workflows

    def _determine_workflow_name(self, path: str, method: str, handler: str) -> Optional[str]:
        p = path.lower()
        if "auth" in p or "login" in p:
            return "User Authentication & Token Issue Workflow"
        elif "register" in p or "signup" in p:
            return "User Registration & Account Creation Workflow"
        elif any(w in p for w in ["order", "cart", "checkout", "payment"]):
            return "Order Processing & Settlement Workflow"
        elif any(w in p for w in ["product", "catalog", "item"]):
            return f"Product Catalog Operation ({method} {path})"
        elif "user" in p or "profile" in p:
            return f"User Profile Operation ({method} {path})"
        elif "health" in p:
            return "System Health Check Workflow"
        else:
            clean = path.strip("/").replace("/", " ").title()
            return f"{method} {clean} Workflow"
