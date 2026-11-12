import pytest
import os
import io
import zipfile
from pathlib import Path

from backend.app.core.security import validate_and_extract_zip, scan_file_for_secrets
from backend.app.engine.scanner import RepositoryScanner
from backend.app.engine.parser import CodeParser
from backend.app.engine.dependency_graph import DependencyGraphAnalyzer
from backend.app.engine.api_discoverer import ApiDiscoverer
from backend.app.engine.database_analyzer import DatabaseAnalyzer
from backend.app.engine.health_analyzer import HealthAnalyzer
from backend.app.engine.test_reconstructor import TestReconstructor

def test_zip_security_path_traversal(tmp_path):
    """Verifies that malicious zip archives attempting Zip Slip are rejected."""
    bad_zip_path = tmp_path / "malicious.zip"
    with zipfile.ZipFile(bad_zip_path, "w") as zf:
        zf.writestr("../../evil.txt", "pwned")

    dest_dir = tmp_path / "extracted"
    is_safe, msg, _ = validate_and_extract_zip(str(bad_zip_path), str(dest_dir))
    assert not is_safe
    assert "Path traversal" in msg

def test_secret_scanner(tmp_path):
    """Verifies that exposed AWS keys or generic secrets are flagged."""
    sec_file = tmp_path / "creds.py"
    sec_file.write_text("AWS_SECRET = 'AKIAIOSFODNN7EXAMPLE'\nAPI_KEY = 'secret-key-1234567890abcdef'")
    findings = scan_file_for_secrets(str(sec_file), "creds.py")
    assert len(findings) >= 1
    assert any("AWS" in f["name"] or "API" in f["name"] for f in findings)

def test_repository_scanner_on_sample_project():
    """Verifies scanner accurately detects languages and frameworks."""
    scanner = RepositoryScanner("sample_project")
    results = scanner.scan()
    assert results["total_files"] >= 10
    assert results["primary_language"] == "Python"
    
    fw_names = [f["name"] for f in results["frameworks"]]
    assert "FastAPI" in fw_names
    assert "React" in fw_names

def test_python_ast_parser():
    """Verifies AST parsing extracts classes, functions, and signatures."""
    parser = CodeParser("sample_project")
    res = parser.parse_file("backend/services/order_service.py", "Python")
    assert res["status"] == "success"
    
    fn_names = [e["name"] for e in res["entities"]]
    assert "calculate_order_total" in fn_names
    assert "place_order" in fn_names

def test_api_discoverer_on_sample_project():
    """Verifies API endpoints are extracted from FastAPI decorators."""
    scanner = RepositoryScanner("sample_project")
    results = scanner.scan()
    discoverer = ApiDiscoverer("sample_project")
    api_res = discoverer.discover_endpoints(results["files"])

    assert api_res["total_endpoints"] >= 4
    paths = [ep["path"] for ep in api_res["endpoints"]]
    assert any("/auth/register" in p for p in paths)
    assert any("/products" in p for p in paths)
    assert "openapi" in api_res["openapi_spec"]

def test_database_analyzer_on_sample_project():
    """Verifies SQLAlchemy models are parsed with fields and relations."""
    scanner = RepositoryScanner("sample_project")
    results = scanner.scan()
    db_analyzer = DatabaseAnalyzer("sample_project")
    db_res = db_analyzer.analyze_repository(results["files"])

    assert len(db_res["models"]) >= 3
    model_names = [m["name"] for m in db_res["models"]]
    assert "User" in model_names
    assert "Product" in model_names
    assert "Order" in model_names

    user_model = next(m for m in db_res["models"] if m["name"] == "User")
    field_names = [f["name"] for f in user_model["fields"]]
    assert "id" in field_names
    assert "email" in field_names
    assert "hashed_password" in field_names

def test_dependency_graph_and_impact():
    """Verifies dependency graph construction and blast-radius impact analysis."""
    files_meta = [
        {"relative_path": "a.py", "language": "Python", "layer": "api", "line_count": 50},
        {"relative_path": "b.py", "language": "Python", "layer": "business_logic", "line_count": 80},
        {"relative_path": "c.py", "language": "Python", "layer": "database", "line_count": 40},
    ]
    parsed_files = {
        "a.py": {"imports": [{"source": "b", "imported": "service", "line": 2}], "entities": []},
        "b.py": {"imports": [{"source": "c", "imported": "Model", "line": 5}], "entities": []},
        "c.py": {"imports": [], "entities": []},
    }

    graph = DependencyGraphAnalyzer(".")
    graph.build_graph(files_meta, parsed_files)
    impact = graph.analyze_impact("c.py")

    assert impact["target_node"] == "c.py"
    assert "b.py" in impact["direct_dependents"]
    assert "a.py" in impact["indirect_dependents"]
    assert impact["severity"] in ("high", "critical", "medium")

def test_health_report():
    """Verifies evidence-backed health scoring."""
    analyzer = HealthAnalyzer(".")
    files = [{"relative_path": "dummy.py", "language": "Python", "line_count": 50, "category": "backend"}]
    parsed = {"dummy.py": {"entities": [{"name": "func", "entity_type": "function", "docstring": "test"}]}}
    report = analyzer.analyze(files, parsed, {}, [])
    assert 20 <= report["health_score"] <= 100
    assert report["grade"] in ("A", "B", "C", "D", "F")
