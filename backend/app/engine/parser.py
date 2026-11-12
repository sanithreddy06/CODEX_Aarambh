import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Tree-sitter imports
try:
    import tree_sitter
    import tree_sitter_javascript as ts_js
    import tree_sitter_typescript as ts_ts
    import tree_sitter_java as ts_java
    import tree_sitter_python as ts_py
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class CodeParser:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self._init_tree_sitter()

    def _init_tree_sitter(self):
        self.ts_parsers: Dict[str, Any] = {}
        if not TREE_SITTER_AVAILABLE:
            return

        try:
            self.js_lang = tree_sitter.Language(ts_js.language())
            self.ts_parsers["javascript"] = tree_sitter.Parser(self.js_lang)

            self.ts_lang = tree_sitter.Language(ts_ts.language_typescript())
            self.ts_parsers["typescript"] = tree_sitter.Parser(self.ts_lang)

            self.tsx_lang = tree_sitter.Language(ts_ts.language_tsx())
            self.ts_parsers["tsx"] = tree_sitter.Parser(self.tsx_lang)

            self.java_lang = tree_sitter.Language(ts_java.language())
            self.ts_parsers["java"] = tree_sitter.Parser(self.java_lang)

            self.py_lang = tree_sitter.Language(ts_py.language())
            self.ts_parsers["python"] = tree_sitter.Parser(self.py_lang)
        except Exception:
            self.ts_parsers = {}

    def parse_file(self, rel_path: str, language: str) -> Dict[str, Any]:
        """
        Parses source file using grammar-based AST parsers.
        Extracts entities with accurate node ranges (start_line, end_line),
        signatures, parameters, imports, exports, and call hierarchies.
        """
        full_path = self.root_dir / rel_path
        if not full_path.is_file():
            return {
                "entities": [],
                "imports": [],
                "exports": [],
                "calls": [],
                "ast_tree": None,
                "status": "missing_file"
            }

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            content_bytes = content.encode("utf-8")
        except Exception as e:
            return {
                "entities": [],
                "imports": [],
                "exports": [],
                "calls": [],
                "ast_tree": None,
                "status": f"read_error: {str(e)}"
            }

        # Route by language
        if language == "Python":
            return self._parse_python(rel_path, content)
        elif language in ("JavaScript", "TypeScript") or rel_path.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
            lang_key = "tsx" if rel_path.endswith((".tsx", ".jsx")) else ("typescript" if rel_path.endswith(".ts") else "javascript")
            return self._parse_tree_sitter_js_ts(rel_path, content_bytes, lang_key, language)
        elif language == "Java" or rel_path.endswith(".java"):
            return self._parse_tree_sitter_java(rel_path, content_bytes)
        else:
            return {
                "entities": [],
                "imports": [],
                "exports": [],
                "calls": [],
                "ast_tree": {
                    "name": rel_path,
                    "type": "unsupported_language",
                    "details": f"AST grammar parsing not fully implemented for {language}. File recorded for inventory.",
                    "children": []
                },
                "status": "partial_support"
            }

    # =========================================================================
    # 1. PYTHON PARSER (Native AST + accurate node end positions)
    # =========================================================================
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
                    "name": Path(rel_path).name,
                    "type": "SyntaxError",
                    "details": f"Line {e.lineno}: {e.msg}",
                    "children": []
                },
                "status": f"syntax_error: line {e.lineno}: {e.msg}"
            }

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
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant):
                                exports.append(str(elt.value))

        return {
            "entities": entities,
            "imports": imports,
            "exports": exports,
            "calls": list(dict.fromkeys(calls)),
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

        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)

        entity = {
            "file_path": rel_path,
            "name": display_name,
            "entity_type": entity_type,
            "start_line": start_line,
            "end_line": end_line,
            "language": "Python",
            "signature": sig,
            "docstring": docstring,
            "params": params,
            "return_type": return_type,
            "calls": list(dict.fromkeys(calls)),
            "evidence": {
                "class": class_name,
                "is_async": is_async,
                "decorator_count": len(node.decorator_list),
                "exact_lines": True
            }
        }

        ast_node = {
            "name": sig,
            "type": "FunctionDef" if not is_async else "AsyncFunctionDef",
            "line": start_line,
            "children": [
                {"name": f"param: {p}", "type": "Parameter", "line": start_line} for p in params
            ] + [
                {"name": f"calls: {c}()", "type": "Call", "line": start_line} for c in list(dict.fromkeys(calls))[:10]
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

        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)

        cls_entity = {
            "file_path": rel_path,
            "name": node.name,
            "entity_type": "class",
            "start_line": start_line,
            "end_line": end_line,
            "language": "Python",
            "signature": f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
            "docstring": docstring,
            "params": bases,
            "return_type": "",
            "calls": list(dict.fromkeys(class_calls)),
            "evidence": {
                "base_classes": bases,
                "method_count": len(methods),
                "methods": [m["name"] for m in methods],
                "exact_lines": True
            }
        }

        cls_ast = {
            "name": f"class {node.name}",
            "type": "ClassDef",
            "line": start_line,
            "children": ast_children
        }

        return cls_entity, cls_ast, class_calls

    # =========================================================================
    # 2. TREE-SITTER JAVASCRIPT / TYPESCRIPT / TSX PARSER
    # =========================================================================
    def _parse_tree_sitter_js_ts(self, rel_path: str, content_bytes: bytes, parser_key: str, language: str) -> Dict[str, Any]:
        parser = self.ts_parsers.get(parser_key) or self.ts_parsers.get("javascript")
        if not parser:
            return {
                "entities": [],
                "imports": [],
                "exports": [],
                "calls": [],
                "ast_tree": None,
                "status": "tree_sitter_unavailable"
            }

        try:
            tree = parser.parse(content_bytes)
        except Exception as e:
            return {
                "entities": [],
                "imports": [],
                "exports": [],
                "calls": [],
                "ast_tree": None,
                "status": f"parse_error: {str(e)}"
            }

        entities: List[Dict[str, Any]] = []
        imports: List[Dict[str, Any]] = []
        exports: List[str] = []
        calls: List[str] = []

        ast_tree = {
            "name": Path(rel_path).name,
            "type": "Program",
            "line": 1,
            "children": []
        }

        self._traverse_js_ts_nodes(
            tree.root_node,
            rel_path,
            language,
            entities,
            imports,
            exports,
            calls,
            ast_tree["children"]
        )

        return {
            "entities": entities,
            "imports": imports,
            "exports": list(dict.fromkeys(exports)),
            "calls": list(dict.fromkeys(calls)),
            "ast_tree": ast_tree,
            "status": "success"
        }

    def _traverse_js_ts_nodes(
        self,
        node: Any,
        rel_path: str,
        language: str,
        entities: List[Dict[str, Any]],
        imports: List[Dict[str, Any]],
        exports: List[str],
        calls: List[str],
        ast_children: List[Dict[str, Any]],
        parent_class: Optional[str] = None
    ):
        for child in node.children:
            node_type = child.type

            # Imports: import ... from '...'
            if node_type == "import_statement":
                source_node = child.child_by_field_name("source")
                source = source_node.text.decode("utf-8").strip("\"'") if source_node else ""
                clause_text = child.text.decode("utf-8")
                start_line = child.start_point.row + 1

                imported_syms = ""
                for sub in child.children:
                    if sub.type in ("import_clause", "named_imports", "identifier"):
                        imported_syms = sub.text.decode("utf-8")

                imports.append({
                    "source": source,
                    "imported": imported_syms.strip(),
                    "line": start_line
                })
                ast_children.append({
                    "name": clause_text.strip(),
                    "type": "ImportStatement",
                    "line": start_line
                })

            # Exports
            elif node_type == "export_statement":
                export_text = child.text.decode("utf-8").strip()
                exports.append(export_text)
                ast_children.append({
                    "name": export_text.splitlines()[0],
                    "type": "ExportStatement",
                    "line": child.start_point.row + 1
                })
                self._traverse_js_ts_nodes(
                    child, rel_path, language, entities, imports, exports, calls, ast_children, parent_class
                )

            # Function Declarations
            elif node_type in ("function_declaration", "generator_function_declaration"):
                name_node = child.child_by_field_name("name")
                if name_node:
                    fn_name = name_node.text.decode("utf-8")
                    params_node = child.child_by_field_name("parameters")
                    params_text = params_node.text.decode("utf-8") if params_node else "()"
                    ret_node = child.child_by_field_name("return_type")
                    ret_type = ret_node.text.decode("utf-8").lstrip(": ") if ret_node else ""

                    start_line = child.start_point.row + 1
                    end_line = child.end_point.row + 1

                    is_component = fn_name[0].isupper() and (rel_path.endswith((".tsx", ".jsx")) or "Component" in fn_name)
                    entity_type = "component" if is_component else "function"

                    fn_calls = self._collect_calls_from_node(child)
                    calls.extend(fn_calls)

                    param_names = [p.strip().split(":")[0].strip() for p in params_text.strip("()").split(",") if p.strip()]

                    entities.append({
                        "file_path": rel_path,
                        "name": fn_name,
                        "entity_type": entity_type,
                        "start_line": start_line,
                        "end_line": end_line,
                        "language": language,
                        "signature": f"{fn_name}{params_text}" + (f": {ret_type}" if ret_type else ""),
                        "docstring": "",
                        "params": param_names,
                        "return_type": ret_type,
                        "calls": list(dict.fromkeys(fn_calls)),
                        "evidence": {
                            "is_component": is_component,
                            "exact_lines": True,
                            "node_type": node_type
                        }
                    })

                    ast_children.append({
                        "name": f"{fn_name}{params_text}",
                        "type": "ComponentDeclaration" if is_component else "FunctionDeclaration",
                        "line": start_line
                    })

            # Lexical Declarations: const foo = () => ... or const bar = function(...) ...
            elif node_type in ("lexical_declaration", "variable_declaration"):
                for declarator in child.children:
                    if declarator.type == "variable_declarator":
                        name_node = declarator.child_by_field_name("name")
                        val_node = declarator.child_by_field_name("value")

                        if name_node and val_node and val_node.type in ("arrow_function", "function_expression"):
                            var_name = name_node.text.decode("utf-8")
                            params_node = val_node.child_by_field_name("parameters")
                            params_text = params_node.text.decode("utf-8") if params_node else "()"
                            ret_node = val_node.child_by_field_name("return_type")
                            ret_type = ret_node.text.decode("utf-8").lstrip(": ") if ret_node else ""

                            start_line = declarator.start_point.row + 1
                            end_line = declarator.end_point.row + 1

                            is_component = var_name[0].isupper() and (rel_path.endswith((".tsx", ".jsx")) or "Component" in var_name)
                            entity_type = "component" if is_component else "function"

                            fn_calls = self._collect_calls_from_node(val_node)
                            calls.extend(fn_calls)

                            param_names = [p.strip().split(":")[0].strip() for p in params_text.strip("()").split(",") if p.strip()]

                            entities.append({
                                "file_path": rel_path,
                                "name": var_name,
                                "entity_type": entity_type,
                                "start_line": start_line,
                                "end_line": end_line,
                                "language": language,
                                "signature": f"const {var_name} = {params_text}" + (f": {ret_type}" if ret_type else "") + " =>",
                                "docstring": "",
                                "params": param_names,
                                "return_type": ret_type,
                                "calls": list(dict.fromkeys(fn_calls)),
                                "evidence": {
                                    "is_arrow_function": True,
                                    "is_component": is_component,
                                    "exact_lines": True
                                }
                            })

                            ast_children.append({
                                "name": f"const {var_name} = (...)",
                                "type": "ArrowFunctionDeclaration",
                                "line": start_line
                            })

            # Classes: class Name extends Base { ... }
            elif node_type == "class_declaration":
                name_node = child.child_by_field_name("name")
                if name_node:
                    class_name = name_node.text.decode("utf-8")
                    start_line = child.start_point.row + 1
                    end_line = child.end_point.row + 1

                    heritage = []
                    for h_child in child.children:
                        if h_child.type == "class_heritage":
                            heritage.append(h_child.text.decode("utf-8"))

                    class_ast = {
                        "name": f"class {class_name}",
                        "type": "ClassDeclaration",
                        "line": start_line,
                        "children": []
                    }

                    class_methods = []
                    class_calls = []

                    body_node = child.child_by_field_name("body")
                    if body_node:
                        for item in body_node.children:
                            if item.type == "method_definition":
                                m_name_node = item.child_by_field_name("name")
                                m_params_node = item.child_by_field_name("parameters")
                                m_ret_node = item.child_by_field_name("return_type")

                                if m_name_node:
                                    m_name = m_name_node.text.decode("utf-8")
                                    m_params = m_params_node.text.decode("utf-8") if m_params_node else "()"
                                    m_ret = m_ret_node.text.decode("utf-8").lstrip(": ") if m_ret_node else ""
                                    m_start = item.start_point.row + 1
                                    m_end = item.end_point.row + 1

                                    m_calls = self._collect_calls_from_node(item)
                                    class_calls.extend(m_calls)

                                    p_list = [p.strip().split(":")[0].strip() for p in m_params.strip("()").split(",") if p.strip()]

                                    entities.append({
                                        "file_path": rel_path,
                                        "name": f"{class_name}.{m_name}",
                                        "entity_type": "method",
                                        "start_line": m_start,
                                        "end_line": m_end,
                                        "language": language,
                                        "signature": f"{m_name}{m_params}" + (f": {m_ret}" if m_ret else ""),
                                        "docstring": "",
                                        "params": p_list,
                                        "return_type": m_ret,
                                        "calls": list(dict.fromkeys(m_calls)),
                                        "evidence": {
                                            "class": class_name,
                                            "exact_lines": True
                                        }
                                    })

                                    class_ast["children"].append({
                                        "name": f"{m_name}{m_params}",
                                        "type": "MethodDefinition",
                                        "line": m_start
                                    })
                                    class_methods.append(m_name)

                    entities.append({
                        "file_path": rel_path,
                        "name": class_name,
                        "entity_type": "class",
                        "start_line": start_line,
                        "end_line": end_line,
                        "language": language,
                        "signature": f"class {class_name} " + " ".join(heritage),
                        "docstring": "",
                        "params": heritage,
                        "return_type": "",
                        "calls": list(dict.fromkeys(class_calls)),
                        "evidence": {
                            "heritage": heritage,
                            "method_count": len(class_methods),
                            "methods": class_methods,
                            "exact_lines": True
                        }
                    })

                    ast_children.append(class_ast)
                    calls.extend(class_calls)

            # Interfaces (TypeScript)
            elif node_type == "interface_declaration":
                name_node = child.child_by_field_name("name")
                if name_node:
                    iface_name = name_node.text.decode("utf-8")
                    start_line = child.start_point.row + 1
                    end_line = child.end_point.row + 1

                    entities.append({
                        "file_path": rel_path,
                        "name": iface_name,
                        "entity_type": "interface",
                        "start_line": start_line,
                        "end_line": end_line,
                        "language": language,
                        "signature": f"interface {iface_name}",
                        "docstring": "",
                        "params": [],
                        "return_type": "",
                        "calls": [],
                        "evidence": {
                            "exact_lines": True
                        }
                    })

                    ast_children.append({
                        "name": f"interface {iface_name}",
                        "type": "InterfaceDeclaration",
                        "line": start_line
                    })

            # Top-level call expressions
            elif node_type == "call_expression":
                fn_node = child.child_by_field_name("function")
                if fn_node:
                    calls.append(fn_node.text.decode("utf-8"))

    def _collect_calls_from_node(self, node: Any) -> List[str]:
        found = []
        if node.type == "call_expression":
            fn_node = node.child_by_field_name("function")
            if fn_node:
                found.append(fn_node.text.decode("utf-8"))

        for child in node.children:
            found.extend(self._collect_calls_from_node(child))
        return found

    # =========================================================================
    # 3. TREE-SITTER JAVA PARSER
    # =========================================================================
    def _parse_tree_sitter_java(self, rel_path: str, content_bytes: bytes) -> Dict[str, Any]:
        parser = self.ts_parsers.get("java")
        if not parser:
            return {
                "entities": [],
                "imports": [],
                "exports": [],
                "calls": [],
                "ast_tree": None,
                "status": "tree_sitter_java_unavailable"
            }

        try:
            tree = parser.parse(content_bytes)
        except Exception as e:
            return {
                "entities": [],
                "imports": [],
                "exports": [],
                "calls": [],
                "ast_tree": None,
                "status": f"parse_error: {str(e)}"
            }

        entities: List[Dict[str, Any]] = []
        imports: List[Dict[str, Any]] = []
        calls: List[str] = []

        ast_tree = {
            "name": Path(rel_path).name,
            "type": "CompilationUnit",
            "line": 1,
            "children": []
        }

        for child in tree.root_node.children:
            # Imports
            if child.type == "import_declaration":
                imp_text = child.text.decode("utf-8").replace("import", "").replace(";", "").strip()
                start_line = child.start_point.row + 1
                imports.append({
                    "source": imp_text,
                    "imported": imp_text.split(".")[-1],
                    "line": start_line
                })
                ast_tree["children"].append({
                    "name": f"import {imp_text}",
                    "type": "ImportDeclaration",
                    "line": start_line
                })

            # Classes and Interfaces
            elif child.type in ("class_declaration", "interface_declaration", "record_declaration"):
                name_node = child.child_by_field_name("name")
                if not name_node:
                    continue

                class_name = name_node.text.decode("utf-8")
                start_line = child.start_point.row + 1
                end_line = child.end_point.row + 1
                is_iface = child.type == "interface_declaration"

                super_class = child.child_by_field_name("superclass")
                interfaces_node = child.child_by_field_name("interfaces")
                extends_text = super_class.text.decode("utf-8") if super_class else ""
                implements_text = interfaces_node.text.decode("utf-8") if interfaces_node else ""

                class_ast = {
                    "name": f"{'interface' if is_iface else 'class'} {class_name}",
                    "type": "InterfaceDeclaration" if is_iface else "ClassDeclaration",
                    "line": start_line,
                    "children": []
                }

                class_methods = []
                class_calls = []

                body = child.child_by_field_name("body")
                if body:
                    for item in body.children:
                        if item.type in ("method_declaration", "constructor_declaration"):
                            m_name_node = item.child_by_field_name("name")
                            m_params_node = item.child_by_field_name("parameters")
                            m_type_node = item.child_by_field_name("type")

                            if m_name_node:
                                m_name = m_name_node.text.decode("utf-8")
                                m_params = m_params_node.text.decode("utf-8") if m_params_node else "()"
                                m_ret = m_type_node.text.decode("utf-8") if m_type_node else "void"
                                m_start = item.start_point.row + 1
                                m_end = item.end_point.row + 1

                                m_calls = self._collect_java_calls(item)
                                class_calls.extend(m_calls)

                                p_list = [p.strip().split()[-1] for p in m_params.strip("()").split(",") if p.strip()]

                                entities.append({
                                    "file_path": rel_path,
                                    "name": f"{class_name}.{m_name}",
                                    "entity_type": "method",
                                    "start_line": m_start,
                                    "end_line": m_end,
                                    "language": "Java",
                                    "signature": f"{m_ret} {m_name}{m_params}",
                                    "docstring": "",
                                    "params": p_list,
                                    "return_type": m_ret,
                                    "calls": list(dict.fromkeys(m_calls)),
                                    "evidence": {
                                        "class": class_name,
                                        "exact_lines": True
                                    }
                                })

                                class_ast["children"].append({
                                    "name": f"{m_name}{m_params}",
                                    "type": "MethodDeclaration",
                                    "line": m_start
                                })
                                class_methods.append(m_name)

                entities.append({
                    "file_path": rel_path,
                    "name": class_name,
                    "entity_type": "interface" if is_iface else "class",
                    "start_line": start_line,
                    "end_line": end_line,
                    "language": "Java",
                    "signature": f"public class {class_name} {extends_text} {implements_text}".strip(),
                    "docstring": "",
                    "params": [extends_text, implements_text] if extends_text or implements_text else [],
                    "return_type": "",
                    "calls": list(dict.fromkeys(class_calls)),
                    "evidence": {
                        "extends": extends_text,
                        "implements": implements_text,
                        "method_count": len(class_methods),
                        "methods": class_methods,
                        "exact_lines": True
                    }
                })

                ast_tree["children"].append(class_ast)
                calls.extend(class_calls)

        return {
            "entities": entities,
            "imports": imports,
            "exports": [],
            "calls": list(dict.fromkeys(calls)),
            "ast_tree": ast_tree,
            "status": "success"
        }

    def _collect_java_calls(self, node: Any) -> List[str]:
        found = []
        if node.type == "method_invocation":
            name_node = node.child_by_field_name("name")
            if name_node:
                found.append(name_node.text.decode("utf-8"))

        for child in node.children:
            found.extend(self._collect_java_calls(child))
        return found
