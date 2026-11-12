import pytest
import io
import stat
import zipfile

from backend.app.core.security import validate_and_extract_zip, scan_file_for_secrets
from backend.app.engine.parser import CodeParser
from backend.app.engine.dependency_graph import DependencyGraphAnalyzer
from backend.app.engine.workflows import WorkflowReconstructor
from backend.app.engine.test_reconstructor import TestReconstructor
from backend.app.reporting.doc_generator import DocumentationGenerator

# -------------------------------------------------------------
# 1. MULTI-LANGUAGE TREE-SITTER PARSING
# -------------------------------------------------------------
def test_javascript_treesitter_parsing(tmp_path):
    """Verifies Tree-sitter parsing on JavaScript extracting functions, exports, and calls."""
    js_content = """
    function computeTax(amount, rate) {
        const factor = getFactor(rate);
        return amount * factor;
    }

    function getFactor(rate) {
        return rate / 100;
    }

    module.exports = { computeTax };
    """
    js_file = tmp_path / "tax.js"
    js_file.write_text(js_content)

    parser = CodeParser(str(tmp_path))
    res = parser.parse_file("tax.js", "JavaScript")

    assert res["status"] == "success"
    names = [e["name"] for e in res["entities"]]
    assert "computeTax" in names
    assert "getFactor" in names

    compute_tax = next(e for e in res["entities"] if e["name"] == "computeTax")
    assert compute_tax["entity_type"] == "function"
    assert compute_tax["start_line"] == 2
    assert compute_tax["end_line"] >= 5
    assert "getFactor" in compute_tax["calls"]

def test_typescript_treesitter_parsing(tmp_path):
    """Verifies Tree-sitter parsing on TypeScript extracting interfaces, classes, and methods."""
    ts_content = """
    export interface UserRecord {
        id: string;
        username: string;
    }

    export class UserManager {
        private users: UserRecord[] = [];

        public findUser(id: string): UserRecord | undefined {
            return this.users.find(u => u.id === id);
        }
    }
    """
    ts_file = tmp_path / "users.ts"
    ts_file.write_text(ts_content)

    parser = CodeParser(str(tmp_path))
    res = parser.parse_file("users.ts", "TypeScript")

    assert res["status"] == "success"
    names = [e["name"] for e in res["entities"]]
    assert "UserRecord" in names
    assert "UserManager" in names
    assert any("findUser" in n for n in names)

    user_mgr = next(e for e in res["entities"] if e["name"] == "UserManager")
    assert user_mgr["entity_type"] == "class"
    assert user_mgr["start_line"] == 7

def test_tsx_component_treesitter_parsing(tmp_path):
    """Verifies Tree-sitter parsing on TSX React components."""
    tsx_content = """
    import React, { useState } from 'react';

    export const ProfileCard: React.FC<{ name: string }> = ({ name }) => {
        const [active, setActive] = useState(false);
        return (
            <div className="card">
                <h1>{name}</h1>
            </div>
        );
    };
    """
    tsx_file = tmp_path / "ProfileCard.tsx"
    tsx_file.write_text(tsx_content)

    parser = CodeParser(str(tmp_path))
    res = parser.parse_file("ProfileCard.tsx", "TypeScript")

    assert res["status"] == "success"
    names = [e["name"] for e in res["entities"]]
    assert "ProfileCard" in names
    card = next(e for e in res["entities"] if e["name"] == "ProfileCard")
    assert card["start_line"] == 4
    assert card["end_line"] >= 10

def test_java_treesitter_parsing(tmp_path):
    """Verifies Tree-sitter parsing on Java classes and methods."""
    java_content = """
    package com.example.service;

    public class PaymentGateway {
        private String apiKey;

        public boolean processPayment(double amount) {
            validateAmount(amount);
            return true;
        }

        private void validateAmount(double amount) {
            if (amount <= 0) throw new IllegalArgumentException();
        }
    }
    """
    java_file = tmp_path / "PaymentGateway.java"
    java_file.write_text(java_content)

    parser = CodeParser(str(tmp_path))
    res = parser.parse_file("PaymentGateway.java", "Java")

    assert res["status"] == "success"
    names = [e["name"] for e in res["entities"]]
    assert "PaymentGateway" in names
    assert any("processPayment" in n for n in names)
    assert any("validateAmount" in n for n in names)

    proc = next(e for e in res["entities"] if "processPayment" in e["name"])
    assert proc["entity_type"] == "method"
    assert proc["start_line"] == 7
    assert proc["end_line"] >= 9

# -------------------------------------------------------------
# 2. DEPENDENCY CYCLES & IMPACT
# -------------------------------------------------------------
def test_circular_dependency_detection():
    """Verifies detection of circular dependency loops."""
    files_meta = [
        {"relative_path": "a.py", "language": "Python", "layer": "service", "line_count": 30},
        {"relative_path": "b.py", "language": "Python", "layer": "service", "line_count": 30},
        {"relative_path": "c.py", "language": "Python", "layer": "service", "line_count": 30},
    ]
    parsed_files = {
        "a.py": {"imports": [{"source": "b", "imported": "func_b", "line": 1}], "entities": []},
        "b.py": {"imports": [{"source": "c", "imported": "func_c", "line": 1}], "entities": []},
        "c.py": {"imports": [{"source": "a", "imported": "func_a", "line": 1}], "entities": []},
    }

    graph = DependencyGraphAnalyzer(".")
    graph.build_graph(files_meta, parsed_files)
    cycles = graph.detect_circular_dependencies()

    assert len(cycles) > 0
    cycle_nodes = set(cycles[0])
    assert {"a.py", "b.py", "c.py"}.issubset(cycle_nodes)

# -------------------------------------------------------------
# 3. ZIP BOMB, SYMLINK, & SECURITY GUARDS
# -------------------------------------------------------------
def test_zip_duplicate_entries_rejected(tmp_path):
    """Verifies archives with duplicate colliding paths are safely rejected."""
    dup_zip = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(dup_zip, "w") as zf:
        zf.writestr("app/file.txt", "content 1")
        zf.writestr("app/file.txt", "content 2")

    dest = tmp_path / "out"
    is_safe, msg, _ = validate_and_extract_zip(str(dup_zip), str(dest))
    assert not is_safe
    assert "Duplicate" in msg

def test_zip_symlink_disallowed(tmp_path):
    """Verifies archives with symlink entries outside dependencies are rejected."""
    sym_zip = tmp_path / "symlink.zip"
    with zipfile.ZipFile(sym_zip, "w") as zf:
        zinfo = zipfile.ZipInfo("symlink_entry")
        # Set Unix symlink mode
        zinfo.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(zinfo, "/etc/passwd")

    dest = tmp_path / "out"
    is_safe, msg, _ = validate_and_extract_zip(str(sym_zip), str(dest))
    assert not is_safe
    assert "Symlinks are disallowed" in msg

def test_zip_symlink_in_node_modules_safely_ignored(tmp_path):
    """Verifies symlinks in node_modules or dependencies are safely ignored without failing upload."""
    node_zip = tmp_path / "project_with_node_modules.zip"
    with zipfile.ZipFile(node_zip, "w") as zf:
        # Regular source file
        zf.writestr("src/index.js", "console.log('hello');")
        # Symlink inside node_modules/.bin (standard npm behavior)
        zinfo = zipfile.ZipInfo("node_modules/.bin/playwright-core")
        zinfo.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(zinfo, "../playwright/cli.js")

    dest = tmp_path / "out_node"
    is_safe, msg, stats = validate_and_extract_zip(str(node_zip), str(dest))
    assert is_safe
    assert (dest / "src/index.js").is_file()
    # Ensure the symlink was NOT extracted to disk as a symlink
    assert not (dest / "node_modules/.bin/playwright-core").is_symlink()

def test_enhanced_secret_detection(tmp_path):
    """Verifies GitHub PAT, Google API keys, and JWT tokens are detected."""
    sec_file = tmp_path / "keys.env"
    sec_file.write_text("""
    GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz
    GEMINI_KEY=AIzaSyD-1234567890abcdefghijklmnopqr
    AUTH_JWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
    """)
    findings = scan_file_for_secrets(str(sec_file), "keys.env")
    assert len(findings) >= 3
    finding_types = [f["name"] for f in findings]
    assert any("GitHub" in name for name in finding_types)
    assert any("Google" in name for name in finding_types)
    assert any("JWT" in name for name in finding_types)

# -------------------------------------------------------------
# 4. WORKFLOW RECONSTRUCTION & COMPLETENESS
# -------------------------------------------------------------
def test_workflow_reconstruction_evidence_driven():
    """Verifies workflows track completeness and do not invent DB models."""
    reconstructor = WorkflowReconstructor()
    
    # Endpoint with no database access
    endpoints = [
        {
            "method": "GET",
            "path": "/api/status",
            "handler_name": "get_status",
            "file_path": "backend/api/status.py",
            "line_number": 10,
            "auth_middleware": ""
        }
    ]
    parsed_files = {
        "backend/api/status.py": {
            "entities": [{"name": "get_status", "calls": []}],
            "imports": []
        }
    }
    
    workflows = reconstructor.reconstruct_workflows(endpoints, parsed_files, [], [])
    assert len(workflows) == 1
    wf = workflows[0]
    
    # Completeness should be incomplete (no frontend trigger, no DB write)
    assert wf["completeness"] == "incomplete"
    assert len(wf["missing_evidence"]) > 0
    
    # Should NOT have invented a database model step
    steps = wf["steps"]
    db_steps = [s for s in steps if s["component"] == "Database"]
    assert len(db_steps) == 0

# -------------------------------------------------------------
# 5. TEST RECONSTRUCTION
# -------------------------------------------------------------
def test_test_reconstructor_zero_pass_placeholders():
    """Verifies reconstructed tests never contain 'pass' placeholders and synthesize parameters."""
    reconstructor = TestReconstructor()
    
    files = [{"relative_path": "backend/services/pricing.py", "language": "Python"}]
    parsed_files = {
        "backend/services/pricing.py": {
            "entities": [
                {
                    "name": "calculate_discount",
                    "entity_type": "function",
                    "file_path": "backend/services/pricing.py",
                    "params": [{"name": "price"}, {"name": "discount_percent"}],
                    "start_line": 15,
                    "end_line": 25,
                    "language": "Python"
                }
            ],
            "imports": []
        }
    }
    
    tests = reconstructor.generate_tests(files, parsed_files, [], [])
    assert len(tests) >= 1
    
    for t in tests:
        assert "    pass" not in t["code"]
        assert "def test_" in t["code"]
        assert "calculate_discount" in t["code"]
        assert "price=" in t["code"] or "100" in t["code"] or "discount" in t["code"]

# -------------------------------------------------------------
# 6. DOCUMENTATION & REPORT EXPORTS
# -------------------------------------------------------------
def test_documentation_markdown_generation():
    """Verifies documentation generator produces complete Markdown report."""
    generator = DocumentationGenerator()
    proj = {
        "id": "test-uuid",
        "name": "Sample App",
        "description": "A test repository",
        "primary_language": "Python",
        "total_files": 12,
        "total_lines": 1500,
        "health_score": 88
    }
    endpoints = [{"method": "POST", "path": "/api/v1/orders", "handler_name": "create_order", "file_path": "app.py", "line_number": 20}]
    models = [{"name": "Order", "orm_framework": "SQLAlchemy", "file_path": "models.py", "line_number": 10, "fields": [{"name": "id", "type": "int"}]}]
    components = [{"name": "Order Service", "layer": "Service Layer", "responsibilities": ["Processes orders"]}]
    
    doc = generator.generate_markdown(
        project=proj,
        overview={"files_count": 12, "lines_count": 1500, "endpoints_count": 1, "models_count": 1},
        analysis={
            "endpoints": endpoints,
            "models": models,
            "components": components,
            "dependencies": {},
            "findings": [],
            "workflows": [],
            "tests": []
        }
    )
    
    assert "# Sample App — Architectural Intelligence & Technical Specification" in doc
    assert "/api/v1/orders" in doc
    assert "Entity: `Order`" in doc
    assert "Order Service" in doc

# -------------------------------------------------------------
# 7. API ENDPOINTS & STREAMING UPLOAD TEST
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_settings_api_masked_and_update():
    """Verifies that /api/settings returns masked credentials and accepts updates."""
    from httpx import AsyncClient, ASGITransport
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # GET settings
        res = await ac.get("/api/settings")
        assert res.status_code == 200
        data = res.json()
        assert "provider" in data
        assert "has_gemini_key" in data
        assert "max_upload_size_mb" in data
        assert "GEMINI_API_KEY" not in data  # Never expose raw key!

        # POST test connection for deterministic provider
        test_res = await ac.post("/api/settings/test", json={"provider": "deterministic"})
        assert test_res.status_code == 200
        test_data = test_res.json()
        assert test_data["success"] is True

        # POST update provider
        up_res = await ac.post("/api/settings", json={"provider": "deterministic"})
        assert up_res.status_code == 200
        assert up_res.json()["provider"] == "deterministic"

@pytest.mark.asyncio
async def test_upload_streaming_rejects_oversized():
    """Verifies that uploads exceeding MAX_UPLOAD_SIZE_MB are rejected with HTTP 413."""
    from httpx import AsyncClient, ASGITransport
    from backend.app.main import app
    from backend.app.core.config import settings

    # Temporarily set max upload to 1 MB for the test
    original_max = settings.MAX_UPLOAD_SIZE_MB
    settings.MAX_UPLOAD_SIZE_MB = 1
    try:
        # Generate 1.5 MB dummy zip stream
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w") as zf:
            zf.writestr("large.txt", "0" * (1500 * 1024))
        bio.seek(0)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {"file": ("large_project.zip", bio.getvalue(), "application/zip")}
            data = {"name": "Too Big Repo", "description": "Exceeds max"}
            res = await ac.post("/api/projects/upload", data=data, files=files)
            assert res.status_code == 413
            assert "exceeds maximum allowed size" in res.json()["detail"]
    finally:
        settings.MAX_UPLOAD_SIZE_MB = original_max
