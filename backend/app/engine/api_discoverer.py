import ast
import re
from pathlib import Path
from typing import Dict, List, Any

class ApiDiscoverer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()

    def discover_endpoints(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts API routes across FastAPI, Express, Flask, Django, and Spring Boot.
        Builds endpoint catalog and OpenAPI 3.0 specification.
        """
        endpoints: List[Dict[str, Any]] = []

        for f in files:
            rel_path = f["relative_path"]
            lang = f.get("language", "")
            full_path = self.root_dir / rel_path

            if not full_path.is_file():
                continue

            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if lang == "Python":
                # FastAPI & Flask & Django
                endpoints.extend(self._discover_fastapi(rel_path, content))
                endpoints.extend(self._discover_flask(rel_path, content))
                endpoints.extend(self._discover_django(rel_path, content))
            elif lang in ("JavaScript", "TypeScript"):
                # Express.js
                endpoints.extend(self._discover_express(rel_path, content))
            elif lang == "Java":
                # Spring Boot
                endpoints.extend(self._discover_spring(rel_path, content))

        # Deduplicate endpoints by (method, path)
        unique_map: Dict[str, Dict[str, Any]] = {}
        for ep in endpoints:
            key = f"{ep['method']} {ep['path']}"
            if key not in unique_map:
                unique_map[key] = ep
            else:
                # Merge details if available
                if not unique_map[key].get("auth_middleware") and ep.get("auth_middleware"):
                    unique_map[key]["auth_middleware"] = ep["auth_middleware"]

        deduped = list(unique_map.values())
        openapi = self._build_openapi(deduped)

        methods_count: Dict[str, int] = {}
        frameworks: Set = set()
        for ep in deduped:
            methods_count[ep["method"]] = methods_count.get(ep["method"], 0) + 1
            if ep.get("framework"):
                frameworks.add(ep["framework"])

        return {
            "endpoints": deduped,
            "total_endpoints": len(deduped),
            "frameworks": list(frameworks),
            "methods": methods_count,
            "openapi_spec": openapi
        }

    def _discover_fastapi(self, rel_path: str, content: str) -> List[Dict[str, Any]]:
        endpoints = []
        try:
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            return endpoints

        # Check router prefix
        prefix = ""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and "router" in target.id.lower():
                        if isinstance(node.value, ast.Call) and "APIRouter" in ast.unparse(node.value.func):
                            for kw in node.value.keywords:
                                if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                    prefix = str(kw.value.value).rstrip("/")

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    dec_str = ast.unparse(dec)
                    # Match @app.get('/path') or @router.post('/path')
                    m = re.match(r"(?:app|router|api_router)\.(get|post|put|delete|patch|options|head)\(['\"]([^'\"]*)['\"]", dec_str, re.IGNORECASE)
                    if m:
                        method = m.group(1).upper()
                        raw_path = m.group(2)
                        full_path = f"{prefix}{raw_path}" if prefix and not raw_path.startswith(prefix) else raw_path
                        if not full_path.startswith("/"):
                            full_path = "/" + full_path

                        # Route parameters
                        path_params = re.findall(r"\{([A-Za-z0-9_]+)\}", full_path)
                        param_list = [{"name": p, "in": "path", "required": True, "type": "string"} for p in path_params]

                        # Detect query params and body from args
                        req_schema = {}
                        auth_mid = ""
                        for arg in node.args.args:
                            arg_name = arg.arg
                            if arg_name in ("self", "cls", "request"):
                                continue
                            if arg_name not in path_params:
                                # Check if type is a Pydantic model or query
                                ann = ast.unparse(arg.annotation) if arg.annotation else "Any"
                                if "Depends" in dec_str or ("auth" in arg_name or "user" in arg_name or "token" in arg_name):
                                    auth_mid = "Authentication Bearer / Token Dependency"
                                elif "Schema" in ann or "Request" in ann or "Create" in ann or "Update" in ann or method in ("POST", "PUT", "PATCH"):
                                    req_schema = {"type": ann, "description": f"Payload validated by {ann}"}
                                else:
                                    param_list.append({"name": arg_name, "in": "query", "required": False, "type": ann})

                        endpoints.append({
                            "method": method,
                            "path": full_path,
                            "framework": "FastAPI",
                            "file_path": rel_path,
                            "line_number": node.lineno,
                            "handler_name": node.name,
                            "auth_middleware": auth_mid,
                            "parameters": param_list,
                            "request_schema": req_schema,
                            "response_schema": {"type": ast.unparse(node.returns) if node.returns else "JSONResponse"},
                            "related_models": [req_schema.get("type")] if req_schema.get("type") else [],
                            "evidence": {
                                "decorator": dec_str,
                                "line": node.lineno,
                                "confirmed_via": "FastAPI AST decorator inspection"
                            }
                        })
        return endpoints

    def _discover_flask(self, rel_path: str, content: str) -> List[Dict[str, Any]]:
        endpoints = []
        try:
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            return endpoints

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    dec_str = ast.unparse(dec)
                    # @app.route('/path', methods=['GET', 'POST'])
                    m = re.match(r"(?:app|blueprint|api)\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?", dec_str)
                    if m:
                        path = m.group(1)
                        methods_raw = m.group(2) or "'GET'"
                        methods = [re.sub(r"['\"\s]", "", met).upper() for met in methods_raw.split(",")]
                        for met in methods:
                            endpoints.append({
                                "method": met,
                                "path": path,
                                "framework": "Flask",
                                "file_path": rel_path,
                                "line_number": node.lineno,
                                "handler_name": node.name,
                                "auth_middleware": "@login_required" if "@login_required" in content else "",
                                "parameters": [{"name": p, "in": "path", "required": True} for p in re.findall(r"<([^>]+)>", path)],
                                "request_schema": {},
                                "response_schema": {},
                                "related_models": [],
                                "evidence": {"decorator": dec_str, "line": node.lineno, "confirmed_via": "Flask route decorator"}
                            })
        return endpoints

    def _discover_django(self, rel_path: str, content: str) -> List[Dict[str, Any]]:
        endpoints = []
        # path('api/users/', views.UserView.as_view())
        path_matches = re.finditer(r"path\(['\"]([^'\"]+)['\"]\s*,\s*([A-Za-z0-9_\.]+)(?:\.as_view\(\))?", content)
        for m in path_matches:
            raw_path = "/" + m.group(1).lstrip("/")
            handler = m.group(2)
            endpoints.append({
                "method": "GET",
                "path": raw_path,
                "framework": "Django REST Framework",
                "file_path": rel_path,
                "line_number": 1,
                "handler_name": handler,
                "auth_middleware": "IsAuthenticated" if "IsAuthenticated" in content else "",
                "parameters": [],
                "request_schema": {},
                "response_schema": {},
                "related_models": [],
                "evidence": {"route_def": m.group(0), "confirmed_via": "Django url pattern"}
            })
        return endpoints

    def _discover_express(self, rel_path: str, content: str) -> List[Dict[str, Any]]:
        endpoints = []
        lines = content.splitlines()
        # app.get('/users', authMiddleware, handler) or router.post('/login', ...)
        express_regex = re.compile(r"(?:app|router)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"](?:\s*,\s*([A-Za-z0-9_$]+))?")
        
        for line_no, line in enumerate(lines, start=1):
            m = express_regex.search(line)
            if m:
                method = m.group(1).upper()
                path = m.group(2)
                mid_or_handler = m.group(3) or ""
                is_auth = any(a in line.lower() for a in ["auth", "jwt", "verify", "passport", "protect"])
                
                path_params = re.findall(r":([A-Za-z0-9_]+)", path)
                params = [{"name": p, "in": "path", "required": True, "type": "string"} for p in path_params]
                
                endpoints.append({
                    "method": method,
                    "path": path,
                    "framework": "Express.js",
                    "file_path": rel_path,
                    "line_number": line_no,
                    "handler_name": mid_or_handler or "anonymous_handler",
                    "auth_middleware": "AuthMiddleware (JWT/Bearer)" if is_auth else "",
                    "parameters": params,
                    "request_schema": {"type": "object", "description": "Express req.body"} if method in ("POST", "PUT", "PATCH") else {},
                    "response_schema": {"type": "json", "description": "res.json() payload"},
                    "related_models": [],
                    "evidence": {
                        "source_line": line.strip(),
                        "line_number": line_no,
                        "confirmed_via": "Express route registration regex"
                    }
                })
        return endpoints

    def _discover_spring(self, rel_path: str, content: str) -> List[Dict[str, Any]]:
        endpoints = []
        lines = content.splitlines()
        spring_mapping = re.compile(r"@(Get|Post|Put|Delete|Patch)Mapping\(['\"]([^'\"]*)['\"]\)")
        
        for line_no, line in enumerate(lines, start=1):
            m = spring_mapping.search(line)
            if m:
                method = m.group(1).upper()
                path = m.group(2) or "/"
                endpoints.append({
                    "method": method,
                    "path": path,
                    "framework": "Spring Boot",
                    "file_path": rel_path,
                    "line_number": line_no,
                    "handler_name": "SpringControllerMethod",
                    "auth_middleware": "@PreAuthorize" if "@PreAuthorize" in content else "",
                    "parameters": [{"name": p, "in": "path", "required": True} for p in re.findall(r"\{([^}]+)\}", path)],
                    "request_schema": {},
                    "response_schema": {},
                    "related_models": [],
                    "evidence": {"annotation": line.strip(), "line_number": line_no, "confirmed_via": "Spring Boot Mapping annotation"}
                })
        return endpoints

    def _build_openapi(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates standard OpenAPI 3.0.0 specification."""
        paths: Dict[str, Any] = {}
        for ep in endpoints:
            p = ep["path"]
            m = ep["method"].lower()
            if p not in paths:
                paths[p] = {}

            paths[p][m] = {
                "summary": f"{ep['method']} {ep['path']}",
                "operationId": ep.get("handler_name") or f"{m}_{p.replace('/', '_')}",
                "parameters": [
                    {"name": p_item["name"], "in": p_item["in"], "required": p_item.get("required", False), "schema": {"type": p_item.get("type", "string")}}
                    for p_item in ep.get("parameters", [])
                ],
                "responses": {
                    "200": {"description": "Successful operation"},
                    "400": {"description": "Validation error"},
                    "401": {"description": "Unauthorized"} if ep.get("auth_middleware") else {},
                    "500": {"description": "Internal server error"}
                }
            }
            if ep.get("auth_middleware"):
                paths[p][m]["security"] = [{"BearerAuth": []}]

            if ep.get("request_schema") and m in ("post", "put", "patch"):
                paths[p][m]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "title": ep["request_schema"].get("type", "RequestBody")}
                        }
                    }
                }

        return {
            "openapi": "3.0.0",
            "info": {
                "title": "CODEX Discovered API Specification",
                "version": "1.0.0",
                "description": "Autonomously reverse-engineered API specification generated by CODEX Static Analysis Engine."
            },
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }
