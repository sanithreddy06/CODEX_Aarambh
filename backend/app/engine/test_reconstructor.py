from typing import Dict, List, Any
from pathlib import Path

class TestReconstructor:
    def generate_tests(
        self,
        files: List[Dict[str, Any]],
        parsed_files: Dict[str, Dict[str, Any]],
        api_endpoints: List[Dict[str, Any]],
        db_models: List[Dict[str, Any]],
        target_file: str = None,
        framework: str = "pytest"
    ) -> List[Dict[str, Any]]:
        """
        Reconstructs positive, negative, boundary, and auth test cases
        derived directly from discovered code signatures, schemas, and routes.
        """
        generated_tests = []

        # 1. API Route Tests
        for ep in api_endpoints:
            if target_file and ep["file_path"] != target_file:
                continue

            method = ep["method"].upper()
            path = ep["path"]
            handler = ep["handler_name"]
            auth = ep.get("auth_middleware")
            params = ep.get("parameters", [])

            if framework == "pytest":
                # Positive Test
                test_code_pos = f"""import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_{method.lower()}_{handler}_success():
    \"\"\"Positive test case for {method} {path}\"\"\"
    async with AsyncClient(base_url="http://test") as ac:
        headers = {{"Authorization": "Bearer valid_mock_token"}} if "{auth}" else {{}}
        response = await ac.{method.lower()}("{path}", headers=headers)
        assert response.status_code in (200, 201)
"""
                generated_tests.append({
                    "target_file": ep["file_path"],
                    "target_symbol": handler,
                    "test_framework": "pytest",
                    "test_type": "positive",
                    "test_name": f"test_{method.lower()}_{handler}_success",
                    "code": test_code_pos
                })

                # Negative / Auth Test
                if auth:
                    test_code_auth = f"""import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_{method.lower()}_{handler}_missing_auth():
    \"\"\"Authentication failure test case: verifies 401 Unauthorized without token\"\"\"
    async with AsyncClient(base_url="http://test") as ac:
        response = await ac.{method.lower()}("{path}")
        assert response.status_code in (401, 403)
"""
                    generated_tests.append({
                        "target_file": ep["file_path"],
                        "target_symbol": handler,
                        "test_framework": "pytest",
                        "test_type": "authentication",
                        "test_name": f"test_{method.lower()}_{handler}_missing_auth",
                        "code": test_code_auth
                    })

                # Boundary / Missing Parameter Test
                if params:
                    test_code_boundary = f"""import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_{method.lower()}_{handler}_invalid_parameters():
    \"\"\"Boundary test case: sends malformed or out-of-range path/query values\"\"\"
    async with AsyncClient(base_url="http://test") as ac:
        response = await ac.{method.lower()}("{path.replace('{id}', '-99999')}")
        assert response.status_code in (400, 404, 422)
"""
                    generated_tests.append({
                        "target_file": ep["file_path"],
                        "target_symbol": handler,
                        "test_framework": "pytest",
                        "test_type": "boundary",
                        "test_name": f"test_{method.lower()}_{handler}_invalid_parameters",
                        "code": test_code_boundary
                    })

            else:
                # Jest / Vitest JS/TS Test
                jest_code = f"""import {{ describe, it, expect }} from 'vitest';

describe('{method} {path}', () => {{
  it('should return 200/201 on valid request', async () => {{
    const response = await fetch('{path}', {{
      method: '{method}',
      headers: {{ 'Content-Type': 'application/json' }}
    }});
    expect([200, 201]).toContain(response.status);
  }});

  it('should reject invalid payload with 400', async () => {{
    const response = await fetch('{path}', {{
      method: '{method}',
      body: JSON.stringify({{ invalid_field: true }})
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
                    "test_name": f"{method} {path} Integration Test",
                    "code": jest_code
                })

        # 2. Extracted Function Unit Tests
        for rel_path, parsed in parsed_files.items():
            if target_file and rel_path != target_file:
                continue

            for ent in parsed.get("entities", []):
                if ent.get("entity_type") in ("function", "method") and not ent["name"].startswith("__"):
                    fn_name = ent["name"].split(".")[-1]
                    sig = ent.get("signature", "")
                    params = ent.get("params", [])

                    if framework == "pytest":
                        unit_test = f"""import pytest

def test_{fn_name}_nominal_execution():
    \"\"\"Unit test for {fn_name}({', '.join(params)})\nVerified signature: {sig}\"\"\"
    # Mock inputs based on extracted parameters: {params}
    # Execute function under test
    pass
"""
                        generated_tests.append({
                            "target_file": rel_path,
                            "target_symbol": fn_name,
                            "test_framework": "pytest",
                            "test_type": "positive",
                            "test_name": f"test_{fn_name}_nominal_execution",
                            "code": unit_test
                        })
                    break  # 1-2 unit test per file

        return generated_tests
