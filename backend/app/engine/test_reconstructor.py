from typing import Dict, List, Any, Optional

class TestReconstructor:
    def generate_tests(
        self,
        files: List[Dict[str, Any]],
        parsed_files: Dict[str, Dict[str, Any]],
        api_endpoints: List[Dict[str, Any]],
        db_models: List[Dict[str, Any]],
        target_file: Optional[str] = None,
        framework: str = "pytest"
    ) -> List[Dict[str, Any]]:
        """
        Reconstructs verifiable test suites covering:
        - Positive nominal execution
        - Negative input validation & error rejection
        - Boundary conditions
        - Authentication enforcement (strictly when auth is present)
        - Executable unit tests with generated arguments (no 'pass' placeholders)
        - Clearly labelled test specifications when harness inputs are external
        """
        generated_tests: List[Dict[str, Any]] = []

        # 1. API Route Tests
        for ep in api_endpoints:
            if target_file and ep["file_path"] != target_file:
                continue

            method = ep["method"].upper()
            path = ep["path"]
            handler = ep["handler_name"] or "handler"
            auth = ep.get("auth_middleware")
            params = ep.get("parameters", [])
            req_schema = ep.get("request_schema", {})
            sample_payload = self._generate_sample_payload(path, req_schema)

            if framework == "pytest":
                # --- Positive Test ---
                payload_code = f"payload = {sample_payload}\n        response = await ac.{method.lower()}('{path}', json=payload)" if method in ("POST", "PUT", "PATCH") else f"response = await ac.{method.lower()}('{path}')"
                auth_header = 'headers = {"Authorization": "Bearer test-jwt-token"}' if auth else 'headers = {}'

                test_code_pos = f"""import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_{method.lower()}_{handler}_positive():
    \"\"\"Positive test case for {method} {path}
    Verified handler: {handler}()
    \"\"\"
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        {auth_header}
        {payload_code}
        assert response.status_code in (200, 201), f"Unexpected status: {{response.status_code}} - {{response.text}}"
        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            assert data is not None
"""
                generated_tests.append({
                    "target_file": ep["file_path"],
                    "target_symbol": handler,
                    "test_framework": "pytest",
                    "test_type": "positive",
                    "test_name": f"test_{method.lower()}_{handler}_positive",
                    "code": test_code_pos
                })

                # --- Negative / Validation Test ---
                if method in ("POST", "PUT", "PATCH"):
                    test_code_neg = f"""import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_{method.lower()}_{handler}_invalid_schema_rejection():
    \"\"\"Negative test: verifies server rejects malformed payload with 400 or 422 Unprocessable Entity\"\"\"
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        # Deliberately malformed payload
        response = await ac.{method.lower()}('{path}', json={{"__invalid_field__": True}})
        assert response.status_code in (400, 422), f"Expected validation rejection, got {{response.status_code}}"
"""
                    generated_tests.append({
                        "target_file": ep["file_path"],
                        "target_symbol": handler,
                        "test_framework": "pytest",
                        "test_type": "negative",
                        "test_name": f"test_{method.lower()}_{handler}_invalid_schema",
                        "code": test_code_neg
                    })

                # --- Authentication Enforcement Test (STRICTLY when auth discovered) ---
                if auth:
                    test_code_auth = f"""import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_{method.lower()}_{handler}_unauthorized_without_token():
    \"\"\"Security test: verifies endpoint enforces {auth}\"\"\"
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        # Request with no credentials supplied
        response = await ac.{method.lower()}('{path}')
        assert response.status_code in (401, 403), f"Security bypass detected: route returned {{response.status_code}} without token"
"""
                    generated_tests.append({
                        "target_file": ep["file_path"],
                        "target_symbol": handler,
                        "test_framework": "pytest",
                        "test_type": "authentication",
                        "test_name": f"test_{method.lower()}_{handler}_unauthorized",
                        "code": test_code_auth
                    })

                # --- Boundary Condition Test ---
                if "{" in path or params:
                    test_path = path.replace("{id}", "-1").replace("{product_id}", "0").replace("{user_id}", "999999")
                    test_code_bound = f"""import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_{method.lower()}_{handler}_boundary_nonexistent_id():
    \"\"\"Boundary test: checks out-of-range identifier response handling\"\"\"
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        response = await ac.{method.lower()}('{test_path}')
        assert response.status_code in (400, 404, 422), f"Expected 404/422 for boundary id, got {{response.status_code}}"
"""
                    generated_tests.append({
                        "target_file": ep["file_path"],
                        "target_symbol": handler,
                        "test_framework": "pytest",
                        "test_type": "boundary",
                        "test_name": f"test_{method.lower()}_{handler}_boundary",
                        "code": test_code_bound
                    })

            else:
                # Vitest / Jest (JS/TS)
                test_code_ts = f"""import {{ describe, it, expect }} from 'vitest';

describe('{method} {path}', () => {{
  it('should process nominal request successfully', async () => {{
    const response = await fetch('{path}', {{
      method: '{method}',
      headers: {{ 'Content-Type': 'application/json' }},
      {f"body: JSON.stringify({sample_payload})" if method in ('POST', 'PUT') else ""}
    }});
    expect([200, 201]).toContain(response.status);
  }});

  it('should reject malformed payload', async () => {{
    const response = await fetch('{path}', {{
      method: '{method}',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ malformed: true }})
    }});
    expect([400, 422]).toContain(response.status);
  }});
}});
"""
                generated_tests.append({
                    "target_file": ep["file_path"],
                    "target_symbol": handler,
                    "test_framework": "vitest",
                    "test_type": "positive",
                    "test_name": f"{method}_{handler}_suite",
                    "code": test_code_ts
                })

        # 2. Extracted Function Unit Tests
        for rel_path, parsed in parsed_files.items():
            if target_file and rel_path != target_file:
                continue

            # Only generate unit tests for business logic / services / utilities
            if not any(k in rel_path.lower() for k in ("service", "util", "helper", "logic", "calculator", "lib")):
                continue

            for ent in parsed.get("entities", []):
                if ent.get("entity_type") in ("function", "method") and not ent["name"].startswith("_"):
                    fn_name = ent["name"].split(".")[-1]
                    params = ent.get("params", [])
                    sig = ent.get("signature", "")

                    # Check if routine requires database session or HTTP request
                    requires_external = any(p in ("db", "session", "request", "conn", "cursor") for p in params)

                    if requires_external:
                        spec_code = f"""# =========================================================================
# TEST SPECIFICATION — REQUIRES ISOLATED DATABASE/MOCK FIXTURE
# Target: {rel_path}::{fn_name}
# Verified Signature: {sig}
# Parameters: {', '.join(params)}
# =========================================================================
\"\"\"
Test Scenario:
1. Provide mock database transaction fixture (e.g. SQLite in-memory).
2. Invoke `{fn_name}({', '.join(params)})`.
3. Verify return contract and database mutation state.
\"\"\"
"""
                        generated_tests.append({
                            "target_file": rel_path,
                            "target_symbol": fn_name,
                            "test_framework": "pytest",
                            "test_type": "specification",
                            "test_name": f"spec_{fn_name}_harness",
                            "code": spec_code
                        })
                    else:
                        arg_values = self._synthesize_arguments(params)
                        args_str = ", ".join(f"{k}={repr(v)}" for k, v in arg_values.items())
                        mod_import = rel_path.replace("/", ".").replace(".py", "")

                        unit_code = f"""import pytest
from {mod_import} import {fn_name}

def test_{fn_name}_executable_nominal():
    \"\"\"Unit test for {fn_name}() in {rel_path}
    Signature: {sig}
    \"\"\"
    result = {fn_name}({args_str})
    assert result is not None, f"Expected non-null return from {fn_name}"
"""
                        generated_tests.append({
                            "target_file": rel_path,
                            "target_symbol": fn_name,
                            "test_framework": "pytest",
                            "test_type": "positive",
                            "test_name": f"test_{fn_name}_executable_nominal",
                            "code": unit_code
                        })
                    break

        return generated_tests

    def _generate_sample_payload(self, path: str, req_schema: Dict[str, Any]) -> Dict[str, Any]:
        p_lower = path.lower()
        if "auth" in p_lower or "register" in p_lower:
            return {"email": "audit.test@example.com", "password": "SecurePassword123!", "full_name": "Audit Test User"}
        elif "login" in p_lower:
            return {"email": "audit.test@example.com", "password": "SecurePassword123!"}
        elif "order" in p_lower:
            return {
                "user_id": 1,
                "items": [{"product_id": 1, "quantity": 2, "unit_price": 29.99}],
                "shipping_address": "456 Market St, Suite 100"
            }
        elif "product" in p_lower:
            return {"title": "Reconstructed Test Product", "price": 49.99, "stock": 25, "category": "Electronics"}
        elif "user" in p_lower:
            return {"name": "Test User", "email": "user@example.com"}
        return {"title": "Sample Record", "value": 100}

    def _synthesize_arguments(self, params: Any) -> Dict[str, Any]:
        args = {}
        for p in params:
            param_name = p.get("name", str(p)) if isinstance(p, dict) else str(p)
            p_low = param_name.lower()
            if "password" in p_low:
                args[param_name] = "SecureTestPassword123!"
            elif "email" in p_low:
                args[param_name] = "test.engineer@example.com"
            elif any(k in p_low for k in ["price", "amount", "total", "cost", "rate", "percent"]):
                args[param_name] = 49.95
            elif any(k in p_low for k in ["quantity", "count", "num", "id", "user_id"]):
                args[param_name] = 1
            elif any(k in p_low for k in ["items", "list", "array"]):
                args[param_name] = [{"quantity": 2, "unit_price": 10.0}]
            elif any(k in p_low for k in ["address", "street"]):
                args[param_name] = "100 Innovation Way"
            elif any(k in p_low for k in ["name", "title"]):
                args[param_name] = "Nominal Sample"
            elif any(k in p_low for k in ["is_", "flag", "active", "enabled"]):
                args[param_name] = True
            else:
                args[param_name] = "sample_value"
        return args
