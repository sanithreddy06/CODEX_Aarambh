import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class CodeParser:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()

    def parse_file(self, rel_path: str, language: str) -> Dict[str, Any]:
        """
        Parses source file and extracts:
        - entities: functions, methods, classes, interfaces
        - imports: module dependencies
        - exports: symbols exported
        - calls: internal/external function calls
        - ast_tree: hierarchical tree for visual AST exploration
        """
        full_path = self.root_dir / rel_path
        if not full_path.is_file():
            return {"entities": [], "imports": [], "exports": [], "calls": [], "ast_tree": None, "status": "missing_file"}

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return {"entities": [], "imports": [], "exports": [], "calls": [], "ast_tree": None, "status": f"read_error: {str(e)}"}

        if language == "Python":
            return self._parse_python(rel_path, content)
        elif language in ("JavaScript", "TypeScript"):
            return self._parse_javascript_typescript(rel_path, content, language)
        elif language == "Java":
            return self._parse_java(rel_path, content)
        else:
            return {
                "entities": [],
                "imports": [],
                "exports": [],
                "calls": [],
                "ast_tree": {
                    "name": rel_path,
                    "type": "unsupported_language",
                    "details": f"AST parsing not fully implemented for {language}. Raw facts extracted.",
                    "children": []
                },
                "status": "partial_support"
            }

    # -------------------------------------------------------------
    # PYTHON PARSER (Native AST)
    # -------------------------------------------------------------
    def _parse_python(self, rel_path: str, content: str) -> Dict[str, Any]:
        entities = []
        imports = []
        exports = []
        calls = []

        try:
            tree = ast.parse(content, filename=rel_path)
        except SyntaxError as e:
            return {
                "entities": [],
                "imports": [],
                "exports": [],
                "calls": [],
                "ast_tree": {
                    "name": rel_path,
                    "type": "SyntaxError",
                    "details": f"Line {e.lineno}: {e.msg}",
                    "children": []
                },
                "status": f"syntax_error: {str(e)}"
            }

        # Build visual AST tree
        ast_tree = {
            "name": Path(rel_path).name,
            "type": "Module",
            "line": 1,
            "children": []
        }

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ent, ast_node = self._process_py_function(node, rel_path)
                entities.append(ent)
                ast_tree["children"].append(ast_node)
                calls.extend(ent.get("calls", []))
            elif isinstance(node, ast.ClassDef):
                cls_ent, cls_ast, cls_calls = self._process_py_class(node, rel_path)
                entities.append(cls_ent)
                ast_tree["children"].append(cls_ast)
                calls.extend(cls_calls)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "source": alias.name,
                        "imported": alias.asname or alias.name,
                        "line": node.lineno
                    })
                    ast_tree["children"].append({
                        "name": f"import {alias.name}",
                        "type": "Import",
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append({
                        "source": mod,
                        "imported": alias.name,
                        "asname": alias.asname,
                        "line": node.lineno
                    })
                    ast_tree["children"].append({
                        "name": f"from {mod} import {alias.name}",
                        "type": "ImportFrom",
                        "line": node.lineno
                    })
            elif isinstance(node, ast.Assign):
                # Identify __all__ exports
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant):
                                exports.append(str(elt.value))

        return {
            "entities": entities,
            "imports": imports,
            "exports": exports,
            "calls": list(set(calls)),
            "ast_tree": ast_tree,
            "status": "success"
        }

    def _process_py_function(self, node: Any, rel_path: str, class_name: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        is_async = isinstance(node, ast.AsyncFunctionDef)
        params = [arg.arg for arg in node.args.args]
        docstring = ast.get_docstring(node) or ""
        return_type = ""
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
            except Exception:
                return_type = "Any"

        # Find calls inside function
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)

        entity_type = "method" if class_name else "function"
        display_name = f"{class_name}.{node.name}" if class_name else node.name
        sig = f"{'async ' if is_async else ''}def {node.name}({', '.join(params)})"
        if return_type:
            sig += f" -> {return_type}"

        entity = {
            "file_path": rel_path,
            "name": display_name,
            "entity_type": entity_type,
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "language": "Python",
            "signature": sig,
            "docstring": docstring,
            "params": params,
            "return_type": return_type,
            "calls": list(set(calls)),
            "evidence": {
                "class": class_name,
                "is_async": is_async,
                "decorator_count": len(node.decorator_list)
            }
        }

        ast_node = {
            "name": sig,
            "type": "FunctionDef" if not is_async else "AsyncFunctionDef",
            "line": node.lineno,
            "children": [
                {"name": f"param: {p}", "type": "Parameter", "line": node.lineno} for p in params
            ] + [
                {"name": f"calls: {c}()", "type": "Call", "line": node.lineno} for c in list(set(calls))[:10]
            ]
        }

        return entity, ast_node

    def _process_py_class(self, node: ast.ClassDef, rel_path: str) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
        bases = []
        for b in node.bases:
            try:
                bases.append(ast.unparse(b))
            except Exception:
                pass

        docstring = ast.get_docstring(node) or ""
        methods = []
        class_calls = []
        ast_children = []

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ent, m_ast = self._process_py_function(item, rel_path, class_name=node.name)
                methods.append(ent)
                ast_children.append(m_ast)
                class_calls.extend(ent.get("calls", []))

        cls_entity = {
            "file_path": rel_path,
            "name": node.name,
            "entity_type": "class",
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "language": "Python",
            "signature": f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
            "docstring": docstring,
            "params": bases,
            "return_type": "",
            "calls": list(set(class_calls)),
            "evidence": {
                "base_classes": bases,
                "method_count": len(methods),
                "methods": [m["name"] for m in methods]
            }
        }

        cls_ast = {
            "name": f"class {node.name}",
            "type": "ClassDef",
            "line": node.lineno,
            "children": ast_children
        }

        return cls_entity, cls_ast, class_calls

    # -------------------------------------------------------------
    # JS / TS PARSER (Lexical & Grammar AST Extractor)
    # -------------------------------------------------------------
    def _parse_javascript_typescript(self, rel_path: str, content: str, language: str) -> Dict[str, Any]:
        entities = []
        imports = []
        exports = []
        calls = []

        ast_tree = {
            "name": Path(rel_path).name,
            "type": "Program",
            "line": 1,
            "children": []
        }

        lines = content.splitlines()

        # Import regexes
        # import { a, b } from 'module';
        # import Default from './path';
        # const x = require('module');
        import_es_regex = re.compile(r"import\s+(?:(?:([A-Za-z0-9_$]+)|\{([^}]+)\}|\*\s+as\s+([A-Za-z0-9_$]+))\s+from\s+)?['\"]([^'\"]+)['\"]")
        require_regex = re.compile(r"(?:const|let|var)\s+(?:([A-Za-z0-9_$]+)|\{([^}]+)\})\s*=\s*require\(['\"]([^'\"]+)['\"]")

        # Function & Method regexes
        fn_decl_regex = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s*([A-Za-z0-9_$]+)\s*\(([^)]*)\)")
        arrow_fn_regex = re.compile(r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*(?::\s*[^=]+)?=>")
        class_regex = re.compile(r"^(?:export\s+)?class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$.]+))?")
        interface_regex = re.compile(r"^(?:export\s+)?interface\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$.]+))?")
        call_regex = re.compile(r"\b([A-Za-z0-9_$]+)\s*\(")

        for line_no, line in enumerate(lines, start=1):
            clean_line = line.strip()

            # Skip comments
            if clean_line.startswith("//") or clean_line.startswith("/*") or clean_line.startswith("*"):
                continue

            # Imports
            if clean_line.startswith("import ") or "require(" in clean_line:
                es_m = import_es_regex.search(clean_line)
                if es_m:
                    def_imp, named_imp, ns_imp, src = es_m.groups()
                    imported_syms = def_imp or named_imp or ns_imp or ""
                    imports.append({"source": src, "imported": imported_syms.strip(), "line": line_no})
                    ast_tree["children"].append({"name": clean_line, "type": "ImportDeclaration", "line": line_no})
                else:
                    req_m = require_regex.search(clean_line)
                    if req_m:
                        def_v, destr_v, src = req_m.groups()
                        imports.append({"source": src, "imported": (def_v or destr_v or "").strip(), "line": line_no})
                        ast_tree["children"].append({"name": clean_line, "type": "RequireCall", "line": line_no})

            # Exports
            if clean_line.startswith("export default "):
                exp_sym = clean_line.replace("export default ", "").replace(";", "").strip()
                exports.append(exp_sym)
                ast_tree["children"].append({"name": f"export default {exp_sym}", "type": "ExportDefault", "line": line_no})
            elif clean_line.startswith("export "):
                exports.append(clean_line)

            # Class declarations
            c_m = class_regex.match(clean_line)
            if c_m:
                c_name, c_extends = c_m.groups()
                entities.append({
                    "file_path": rel_path,
                    "name": c_name,
                    "entity_type": "class",
                    "start_line": line_no,
                    "end_line": line_no + 10,
                    "language": language,
                    "signature": f"class {c_name}" + (f" extends {c_extends}" if c_extends else ""),
                    "docstring": "",
                    "params": [c_extends] if c_extends else [],
                    "return_type": "",
                    "calls": [],
                    "evidence": {"extends": c_extends}
                })
                ast_tree["children"].append({"name": f"class {c_name}", "type": "ClassDeclaration", "line": line_no})
                continue

            # Interfaces (TypeScript)
            if language == "TypeScript":
                i_m = interface_regex.match(clean_line)
                if i_m:
                    i_name, i_extends = i_m.groups()
                    entities.append({
                        "file_path": rel_path,
                        "name": i_name,
                        "entity_type": "interface",
                        "start_line": line_no,
                        "end_line": line_no + 5,
                        "language": language,
                        "signature": f"interface {i_name}",
                        "docstring": "",
                        "params": [i_extends] if i_extends else [],
                        "return_type": "",
                        "calls": [],
                        "evidence": {"extends": i_extends}
                    })
                    ast_tree["children"].append({"name": f"interface {i_name}", "type": "InterfaceDeclaration", "line": line_no})
                    continue

            # Functions
            f_m = fn_decl_regex.match(clean_line) or arrow_fn_regex.match(clean_line)
            if f_m:
                fn_name, fn_params = f_m.groups()
                p_list = [p.strip().split(":")[0].strip() for p in fn_params.split(",") if p.strip()]
                is_component = fn_name[0].isupper() and (rel_path.endswith(".tsx") or rel_path.endswith(".jsx"))
                
                entities.append({
                    "file_path": rel_path,
                    "name": fn_name,
                    "entity_type": "component" if is_component else "function",
                    "start_line": line_no,
                    "end_line": line_no + 15,
                    "language": language,
                    "signature": f"{fn_name}({', '.join(p_list)})",
                    "docstring": "",
                    "params": p_list,
                    "return_type": "",
                    "calls": [],
                    "evidence": {"is_component": is_component}
                })
                ast_tree["children"].append({
                    "name": f"{fn_name}(...)",
                    "type": "ComponentDeclaration" if is_component else "FunctionDeclaration",
                    "line": line_no
                })

            # Identify function calls
            for c_match in call_regex.findall(clean_line):
                if c_match not in ("if", "for", "while", "switch", "catch", "function", "require", "import"):
                    calls.append(c_match)

        return {
            "entities": entities,
            "imports": imports,
            "exports": exports,
            "calls": list(set(calls)),
            "ast_tree": ast_tree,
            "status": "success"
        }

    # -------------------------------------------------------------
    # JAVA PARSER
    # -------------------------------------------------------------
    def _parse_java(self, rel_path: str, content: str) -> Dict[str, Any]:
        entities = []
        imports = []
        calls = []

        ast_tree = {
            "name": Path(rel_path).name,
            "type": "CompilationUnit",
            "line": 1,
            "children": []
        }

        class_regex = re.compile(r"(?:public\s+|private\s+|protected\s+)?class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$]+))?(?:\s+implements\s+([A-Za-z0-9_$,\s]+))?")
        method_regex = re.compile(r"(?:public|protected|private|static|\s)+[\w\<\>\[\]]+\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*\{")

        lines = content.splitlines()
        current_class = None

        for line_no, line in enumerate(lines, start=1):
            clean_line = line.strip()
            if clean_line.startswith("import "):
                imp_mod = clean_line.replace("import ", "").replace(";", "").strip()
                imports.append({"source": imp_mod, "imported": imp_mod.split(".")[-1], "line": line_no})
                ast_tree["children"].append({"name": f"import {imp_mod}", "type": "Import", "line": line_no})

            c_m = class_regex.search(clean_line)
            if c_m:
                current_class = c_m.group(1)
                entities.append({
                    "file_path": rel_path,
                    "name": current_class,
                    "entity_type": "class",
                    "start_line": line_no,
                    "end_line": line_no + 30,
                    "language": "Java",
                    "signature": clean_line.replace("{", "").strip(),
                    "docstring": "",
                    "params": [c_m.group(2)] if c_m.group(2) else [],
                    "return_type": "",
                    "calls": [],
                    "evidence": {"extends": c_m.group(2), "implements": c_m.group(3)}
                })
                ast_tree["children"].append({"name": f"class {current_class}", "type": "ClassDeclaration", "line": line_no})

            m_m = method_regex.search(clean_line)
            if m_m and not any(kw in clean_line for kw in ["if", "while", "catch", "class", "new"]):
                m_name = m_m.group(1)
                m_params = [p.strip() for p in m_m.group(2).split(",") if p.strip()]
                entities.append({
                    "file_path": rel_path,
                    "name": f"{current_class}.{m_name}" if current_class else m_name,
                    "entity_type": "method",
                    "start_line": line_no,
                    "end_line": line_no + 15,
                    "language": "Java",
                    "signature": clean_line.replace("{", "").strip(),
                    "docstring": "",
                    "params": m_params,
                    "return_type": "",
                    "calls": [],
                    "evidence": {"class": current_class}
                })
                ast_tree["children"].append({"name": f"{m_name}()", "type": "MethodDeclaration", "line": line_no})

        return {
            "entities": entities,
            "imports": imports,
            "exports": [],
            "calls": list(set(calls)),
            "ast_tree": ast_tree,
            "status": "success"
        }
