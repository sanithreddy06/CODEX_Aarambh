import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

class DatabaseAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()

    def analyze_repository(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Discovers database models, fields, and relationships across
        SQLAlchemy, Prisma, Django, Sequelize, Mongoose, and SQL definitions.
        """
        models: List[Dict[str, Any]] = []

        for file_info in files:
            rel_path = file_info["relative_path"]
            lang = file_info.get("language", "")
            full_path = self.root_dir / rel_path

            if not full_path.is_file():
                continue

            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # 1. SQLAlchemy / Django models (Python)
            if lang == "Python":
                py_models = self._extract_python_models(rel_path, content)
                models.extend(py_models)

            # 2. Prisma Schema (.prisma)
            elif rel_path.endswith(".prisma"):
                prisma_models = self._extract_prisma_models(rel_path, content)
                models.extend(prisma_models)

            # 3. Mongoose / Sequelize (JS/TS)
            elif lang in ("JavaScript", "TypeScript"):
                js_models = self._extract_js_models(rel_path, content)
                models.extend(js_models)

            # 4. Raw SQL schema (.sql)
            elif rel_path.endswith(".sql"):
                sql_models = self._extract_sql_models(rel_path, content)
                models.extend(sql_models)

        # Build ER graph nodes & edges
        er_nodes, er_edges = self._build_er_graph(models)

        return {
            "models": models,
            "er_nodes": er_nodes,
            "er_edges": er_edges
        }

    def _extract_python_models(self, rel_path: str, content: str) -> List[Dict[str, Any]]:
        models = []
        try:
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            return models

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases]
                is_sqlalchemy = any(b in ("Base", "db.Model", "DeclarativeBase") for b in bases)
                is_django = any("models.Model" in b for b in bases)

                if is_sqlalchemy or is_django or "models" in rel_path.lower():
                    fields = []
                    relationships = []
                    table_name = node.name.lower() + "s"

                    for item in node.body:
                        # __tablename__ = "users"
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name) and target.id == "__tablename__":
                                    if isinstance(item.value, ast.Constant):
                                        table_name = str(item.value.value)

                        # Field definitions: e.g. name = Column(String(50)) or id = Column(Integer, primary_key=True)
                        if isinstance(item, (ast.Assign, ast.AnnAssign)):
                            target_name = ""
                            if isinstance(item, ast.Assign) and item.targets and isinstance(item.targets[0], ast.Name):
                                target_name = item.targets[0].id
                            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                                target_name = item.target.id

                            val = item.value if isinstance(item, ast.Assign) else item.value
                            if target_name and val and isinstance(val, ast.Call):
                                call_func = ast.unparse(val.func)
                                val_str = ast.unparse(val)

                                # Foreign key check
                                fk_target = None
                                if "ForeignKey" in val_str:
                                    fk_m = re.search(r"ForeignKey\(['\"]([^'\"]+)['\"]\)", val_str)
                                    if fk_m:
                                        fk_target = fk_m.group(1).split(".")[0]

                                # Relationship check
                                if "relationship" in call_func:
                                    rel_target = ""
                                    if val.args and isinstance(val.args[0], (ast.Constant, ast.Name)):
                                        rel_target = getattr(val.args[0], "value", getattr(val.args[0], "id", ""))
                                    relationships.append({
                                        "target": str(rel_target),
                                        "type": "1-N" if "secondary" not in val_str else "N-N",
                                        "field": target_name,
                                        "confidence": "confirmed",
                                        "evidence": f"SQLAlchemy relationship({rel_target}) on line {item.lineno}"
                                    })
                                elif "Column" in call_func or "Field" in call_func or "models." in call_func:
                                    col_type = "VARCHAR"
                                    if "Integer" in val_str or "AutoField" in val_str: col_type = "INTEGER"
                                    elif "Float" in val_str or "Decimal" in val_str: col_type = "FLOAT"
                                    elif "Boolean" in val_str: col_type = "BOOLEAN"
                                    elif "DateTime" in val_str or "Date" in val_str: col_type = "TIMESTAMP"
                                    elif "Text" in val_str: col_type = "TEXT"
                                    elif "JSON" in val_str: col_type = "JSON"

                                    is_pk = "primary_key=True" in val_str or target_name == "id"
                                    fields.append({
                                        "name": target_name,
                                        "type": col_type,
                                        "primary_key": is_pk,
                                        "foreign_key": fk_target,
                                        "nullable": "nullable=False" not in val_str
                                    })

                                    if fk_target:
                                        relationships.append({
                                            "target": fk_target,
                                            "type": "N-1",
                                            "field": target_name,
                                            "foreign_key": target_name,
                                            "confidence": "confirmed",
                                            "evidence": f"ForeignKey('{fk_target}') on line {item.lineno}"
                                        })

                    if fields:
                        models.append({
                            "name": node.name,
                            "table_name": table_name,
                            "orm_framework": "SQLAlchemy" if is_sqlalchemy else ("Django" if is_django else "Python ORM"),
                            "file_path": rel_path,
                            "line_number": node.lineno,
                            "fields": fields,
                            "relationships": relationships,
                            "evidence": {
                                "base_classes": bases,
                                "field_count": len(fields),
                                "confirmed_via": "AST inspection"
                            }
                        })
        return models

    def _extract_prisma_models(self, rel_path: str, content: str) -> List[Dict[str, Any]]:
        models = []
        model_blocks = re.findall(r"model\s+([A-Za-z0-9_]+)\s*\{([^}]+)\}", content)
        for name, body in model_blocks:
            fields = []
            relationships = []
            for line in body.strip().splitlines():
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    f_name = parts[0]
                    f_type = parts[1]
                    is_pk = "@id" in line
                    is_fk = "@relation" in line
                    
                    fields.append({
                        "name": f_name,
                        "type": f_type,
                        "primary_key": is_pk,
                        "foreign_key": None
                    })
                    if is_fk:
                        # Extract relation target
                        ref_match = re.search(r"references:\s*\[([^\]]+)\]", line)
                        relationships.append({
                            "target": f_type.rstrip("[]"),
                            "type": "1-N" if "[]" in f_type else "N-1",
                            "field": f_name,
                            "referenced_field": ref_match.group(1).strip() if ref_match else None,
                            "confidence": "confirmed",
                            "evidence": f"Prisma @relation on {line}"
                        })

            models.append({
                "name": name,
                "table_name": name.lower() + "s",
                "orm_framework": "Prisma",
                "file_path": rel_path,
                "line_number": 1,
                "fields": fields,
                "relationships": relationships,
                "evidence": {"confirmed_via": "Prisma schema parse"}
            })
        return models

    def _extract_js_models(self, rel_path: str, content: str) -> List[Dict[str, Any]]:
        models = []
        # Mongoose Schema
        mongoose_matches = re.finditer(r"(?:const|let|var)\s+([A-Za-z0-9_]+Schema)\s*=\s*new\s+mongoose\.Schema\(\{([^}]+)\}", content)
        for m in mongoose_matches:
            schema_name = m.group(1).replace("Schema", "")
            body = m.group(2)
            fields = []
            for f_line in body.split(","):
                if ":" in f_line:
                    k, v = f_line.split(":", 1)
                    fields.append({
                        "name": k.strip(),
                        "type": v.strip().replace("{", "").replace("}", "").split()[0],
                        "primary_key": k.strip() == "_id",
                        "foreign_key": None
                    })
            models.append({
                "name": schema_name or "MongooseModel",
                "table_name": (schema_name or "collection").lower() + "s",
                "orm_framework": "Mongoose",
                "file_path": rel_path,
                "line_number": 1,
                "fields": fields or [{"name": "_id", "type": "ObjectId", "primary_key": True}],
                "relationships": [],
                "evidence": {"confirmed_via": "Mongoose Schema definition"}
            })
        return models

    def _extract_sql_models(self, rel_path: str, content: str) -> List[Dict[str, Any]]:
        models = []
        table_matches = re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z0-9_`\"\[\]]+)\s*\((.*?)\);", content, re.IGNORECASE | re.DOTALL)
        for m in table_matches:
            tbl_name = re.sub(r"[`\"\[\]]", "", m.group(1))
            body = m.group(2)
            fields = []
            relationships = []
            for col_line in body.split(","):
                col_clean = col_line.strip()
                if not col_clean or col_clean.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "CONSTRAINT", "INDEX")):
                    if col_clean.upper().startswith("FOREIGN KEY"):
                        fk_m = re.search(r"REFERENCES\s+([A-Za-z0-9_]+)", col_clean, re.IGNORECASE)
                        if fk_m:
                            relationships.append({
                                "target": fk_m.group(1),
                                "type": "N-1",
                                "confidence": "confirmed",
                                "evidence": f"SQL REFERENCES {fk_m.group(1)}"
                            })
                    continue
                parts = col_clean.split()
                if len(parts) >= 2:
                    col_name = re.sub(r"[`\"\[\]]", "", parts[0])
                    col_type = parts[1].upper()
                    is_pk = "PRIMARY KEY" in col_clean.upper()
                    fields.append({
                        "name": col_name,
                        "type": col_type,
                        "primary_key": is_pk,
                        "foreign_key": None
                    })

            models.append({
                "name": tbl_name.capitalize(),
                "table_name": tbl_name,
                "orm_framework": "SQL DDL",
                "file_path": rel_path,
                "line_number": 1,
                "fields": fields,
                "relationships": relationships,
                "evidence": {"confirmed_via": "SQL DDL Table definition"}
            })
        return models

    def _build_er_graph(self, models: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        nodes = []
        edges = []
        model_names = {m["name"].lower(): m["name"] for m in models}

        # Position nodes in a 2D layout grid
        for i, m in enumerate(models):
            x = (i % 3) * 320 + 50
            y = (i // 3) * 260 + 50
            nodes.append({
                "id": m["name"],
                "type": "databaseNode",
                "position": {"x": x, "y": y},
                "data": {
                    "label": m["name"],
                    "table_name": m.get("table_name", m["name"].lower()),
                    "orm_framework": m.get("orm_framework", "ORM"),
                    "file_path": m.get("file_path", ""),
                    "fields": m.get("fields", [])
                }
            })

            # Edges
            for rel in m.get("relationships", []):
                target = rel.get("target", "")
                # Normalize target name
                resolved_target = model_names.get(target.lower()) or model_names.get(target.rstrip("s").lower())
                if resolved_target and resolved_target != m["name"]:
                    edges.append({
                        "id": f"er-{m['name']}->{resolved_target}",
                        "source": m["name"],
                        "target": resolved_target,
                        "label": rel.get("type", "relates_to"),
                        "animated": True,
                        "data": {
                            "type": rel.get("type", "1-N"),
                            "confidence": rel.get("confidence", "confirmed"),
                            "evidence": rel.get("evidence", "")
                        }
                    })

        return nodes, edges
