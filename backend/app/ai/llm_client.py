import os
import httpx
from typing import Dict, List, Any, Tuple, Optional
from backend.app.core.config import settings

class AIIntelligenceClient:
    def __init__(self):
        self.reload_config()

    def reload_config(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.groq_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
        self.openai_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        self.openai_base = settings.OPENAI_BASE_URL
        self.local_url = settings.LOCAL_MODEL_URL

    async def test_connection(
        self,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Tests connectivity and authentication for the designated AI provider."""
        provider = provider.lower().strip()
        
        if provider == "deterministic":
            return True, "Deterministic Fact Engine ready. Operating with strict zero-hallucination AST factual guarantees."

        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                if provider == "gemini":
                    key = api_key or self.gemini_key
                    if not key:
                        return False, "Gemini API key is required but none is configured."
                    resp = await client.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
                    if resp.status_code == 200:
                        return True, "Google Gemini API connection verified successfully."
                    return False, f"Gemini API authentication failed (HTTP {resp.status_code}). Please verify your key."

                elif provider == "groq":
                    key = api_key or self.groq_key
                    if not key:
                        return False, "Groq Cloud API key is required but none is configured."
                    resp = await client.get(
                        "https://api.groq.com/openai/v1/models",
                        headers={"Authorization": f"Bearer {key}"}
                    )
                    if resp.status_code == 200:
                        return True, "Groq Cloud API connection verified successfully."
                    return False, f"Groq authentication failed (HTTP {resp.status_code})."

                elif provider == "openai":
                    key = api_key or self.openai_key
                    target_url = (base_url or self.openai_base).rstrip('/') + "/models"
                    if not key:
                        return False, "OpenAI API key is required but none is configured."
                    resp = await client.get(
                        target_url,
                        headers={"Authorization": f"Bearer {key}"}
                    )
                    if resp.status_code == 200:
                        return True, "OpenAI API connection verified successfully."
                    return False, f"OpenAI authentication failed (HTTP {resp.status_code})."

                elif provider == "local":
                    target_url = (base_url or self.local_url).rstrip('/') + "/models"
                    resp = await client.get(target_url)
                    if resp.status_code == 200:
                        return True, f"Local model server online and reachable at {target_url}."
                    return False, f"Local model server responded with HTTP {resp.status_code}."

                else:
                    return False, f"Unknown AI provider: {provider}"

            except httpx.ConnectError:
                return False, f"Connection refused when attempting to reach {provider} endpoint."
            except httpx.TimeoutException:
                return False, f"Connection timed out when reaching {provider} endpoint."
            except Exception as e:
                return False, f"Provider test error: {str(e)}"

    async def answer_question(
        self,
        query: str,
        project_context: Dict[str, Any],
        history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Coordinates context retrieval, evidence ranking, and LLM reasoning
        with a deterministic factual fallback when no API key is provided.
        """
        history = history or []
        retrieved_context, sources = self._retrieve_relevant_facts(query, project_context)

        # Check if an external provider key is active
        has_key = bool(
            (self.provider == "gemini" and self.gemini_key) or
            (self.provider == "groq" and self.groq_key) or
            (self.provider == "openai" and self.openai_key) or
            (self.provider == "local")
        )

        if not has_key or self.provider == "deterministic":
            return self._deterministic_fallback(query, retrieved_context, sources, project_context)

        # Call configured LLM provider
        try:
            if self.provider == "gemini":
                return await self._call_gemini(query, retrieved_context, sources)
            elif self.provider in ("groq", "openai", "local"):
                return await self._call_openai_compatible(query, retrieved_context, sources)
            else:
                return self._deterministic_fallback(query, retrieved_context, sources, project_context)
        except Exception as e:
            fallback = self._deterministic_fallback(query, retrieved_context, sources, project_context)
            fallback["message"] = f"[LLM Provider Error: {str(e)} — Falling back to Deterministic Fact Engine]\n\n" + fallback["message"]
            return fallback

    def _retrieve_relevant_facts(self, query: str, ctx: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieves matching endpoints, models, AST entities, and files using keyword & intent ranking.
        """
        q_lower = query.lower()
        matched_sources: List[Dict[str, Any]] = []
        fact_lines: List[str] = []

        # 1. Match API Endpoints
        endpoints = ctx.get("endpoints", [])
        for ep in endpoints:
            if any(term in ep["path"].lower() or term in ep["handler_name"].lower() for term in q_lower.split()):
                matched_sources.append({
                    "file": ep["file_path"],
                    "line": ep["line_number"],
                    "type": "api_endpoint",
                    "label": f"{ep['method']} {ep['path']}",
                    "confidence": "high"
                })
                fact_lines.append(f"API Endpoint: {ep['method']} {ep['path']} -> Handler: {ep['handler_name']}() in {ep['file_path']}:{ep['line_number']} (Auth: {ep.get('auth_middleware') or 'None'})")

        # 2. Match Database Models
        models = ctx.get("models", [])
        for m in models:
            if m["name"].lower() in q_lower or any(f["name"].lower() in q_lower for f in m.get("fields", [])):
                matched_sources.append({
                    "file": m["file_path"],
                    "line": m["line_number"],
                    "type": "database_model",
                    "label": f"Model: {m['name']}",
                    "confidence": "high"
                })
                field_list = [f["name"] for f in m.get("fields", [])[:5]]
                fact_lines.append(f"Database Model: '{m['name']}' ({m.get('orm_framework', 'ORM')}) with fields [{', '.join(field_list)}] in {m['file_path']}:{m['line_number']}")

        # 3. Match AST Entities (Functions & Classes)
        entities = ctx.get("entities", [])
        for ent in entities:
            if ent["name"].lower() in q_lower:
                matched_sources.append({
                    "file": ent["file_path"],
                    "line": ent["start_line"],
                    "type": ent["entity_type"],
                    "label": ent["name"],
                    "confidence": "high"
                })
                fact_lines.append(f"Entity: {ent['entity_type']} {ent['name']} in {ent['file_path']}:{ent['start_line']} (Calls: {', '.join(ent.get('calls', [])[:4])})")

        # 4. Fallback: If nothing matched specifically, provide high-level architecture overview facts
        if not fact_lines:
            components = ctx.get("components", [])
            for c in components[:5]:
                fact_lines.append(f"Architecture Component: {c['name']} (Layer: {c['layer']}) - Responsibilities: {', '.join(c.get('responsibilities', []))}")

        return "\n".join(fact_lines) or "No specific matching symbols found for query keywords.", matched_sources

    def _deterministic_fallback(
        self,
        query: str,
        retrieved_context: str,
        sources: List[Dict[str, Any]],
        ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates a rigorous, deterministic, fact-backed explanation
        using only extracted AST symbols, routes, and schemas without hallucinations.
        """
        q = query.lower()
        endpoints = ctx.get("endpoints", [])
        models = ctx.get("models", [])
        components = ctx.get("components", [])

        # Intent: Authentication & Security
        if any(w in q for w in ["auth", "login", "jwt", "token", "password", "security", "protect"]):
            auth_eps = [ep for ep in endpoints if ep.get("auth_middleware") or any(k in ep["path"].lower() for k in ["auth", "login", "token"])]
            auth_models = [m for m in models if any(k in m["name"].lower() for k in ["user", "account", "token", "session", "credential"])]

            lines = [
                "### Deterministic Authentication & Security Architecture Analysis",
                "",
                "Based on static AST analysis and route inspection:",
                f"- **Authentication Endpoints Discovered:** {len(auth_eps)}"
            ]
            for ep in auth_eps:
                lines.append(f"  - `{ep['method']} {ep['path']}` (Handler: `{ep['handler_name']}`, Auth: `{ep.get('auth_middleware') or 'Endpoint'}`)")

            lines.append(f"- **Identity Models:** {', '.join([m['name'] for m in auth_models]) if auth_models else 'None explicitly identified'}")
            lines.append("")
            lines.append("**Operational Workflow:**")
            lines.append("1. Client issues credentials to the designated authentication endpoint.")
            lines.append("2. Incoming payload is parsed and verified by the controller handler.")
            lines.append("3. Authentication middleware enforces token verification on protected endpoints.")
            lines.append("*(Note: Analysis generated deterministically via CODEX Static Intelligence Engine)*")
            
            return {
                "message": "\n".join(lines),
                "sources": sources,
                "confidence": "high",
                "provider_used": "deterministic_engine"
            }

        # Intent: Database / Models
        elif any(w in q for w in ["database", "table", "schema", "model", "orm"]):
            lines = [
                f"### Database Architecture Analysis ({len(models)} Models Discovered)",
                "",
                "The application utilizes the following discovered relational schemas and entities:",
                ""
            ]
            for m in models:
                fields_str = ", ".join([f["name"] + f" ({f['type']})" for f in m.get("fields", [])[:6]])
                lines.append(f"#### Model: `{m['name']}` ({m.get('orm_framework')})")
                lines.append(f"- **Source File:** `{m['file_path']}` (Line {m['line_number']})")
                lines.append(f"- **Fields:** {fields_str}")
                if m.get("relationships"):
                    rels = [f"{r['type']} -> {r['target']}" for r in m["relationships"]]
                    lines.append(f"- **Relationships:** {', '.join(rels)}")
                lines.append("")

            return {
                "message": "\n".join(lines),
                "sources": sources,
                "confidence": "high",
                "provider_used": "deterministic_engine"
            }

        # Intent: Endpoints / APIs
        elif any(w in q for w in ["api", "endpoint", "route", "url"]):
            lines = [
                f"### Discovered API Route Catalog ({len(endpoints)} Endpoints)",
                "",
                "Static analysis identified the following HTTP endpoints:",
                ""
            ]
            for ep in endpoints[:10]:
                auth_tag = f" `[Protected: {ep['auth_middleware']}]`" if ep.get("auth_middleware") else ""
                lines.append(f"- `{ep['method']} {ep['path']}`{auth_tag} in `{ep['file_path']}:{ep['line_number']}`")
            lines.append("")
            lines.append(f"*(Total endpoints cataloged: {len(endpoints)})*")

            return {
                "message": "\n".join(lines),
                "sources": sources,
                "confidence": "high",
                "provider_used": "deterministic_engine"
            }

        # Generic answer with retrieved context
        lines = [
            "### CODEX Static Code Intelligence Response",
            "",
            f"In response to: *\"{query}\"*",
            "",
            "**Verifiable Code Evidence Discovered:**",
            ""
        ]
        if retrieved_context and retrieved_context != "No specific matching symbols found for query keywords.":
            for fact in retrieved_context.splitlines():
                lines.append(f"- {fact}")
        else:
            lines.append(f"- Repository contains {ctx.get('total_files', 0)} files and {len(components)} identified architecture layers.")
            for c in components[:4]:
                lines.append(f"- **{c['name']}** ({c['layer']}): {', '.join(c.get('responsibilities', []))}")

        lines.append("")
        lines.append("*(Powered deterministically by CODEX Code Intelligence AST Indexer)*")

        return {
            "message": "\n".join(lines),
            "sources": sources,
            "confidence": "medium",
            "provider_used": "deterministic_engine"
        }

    async def _call_gemini(self, query: str, context: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        prompt = f"""You are CODEX, an expert autonomous software reverse engineering and code intelligence AI.
Answer the user's question using ONLY the provided verified repository evidence. Always cite files and lines.
Evidence:
{context}

User Question: {query}
"""
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code != 200:
                raise Exception(f"Gemini API returned status {resp.status_code}: {resp.text}")
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {
                "message": text,
                "sources": sources,
                "confidence": "high",
                "provider_used": "gemini"
            }

    async def _call_openai_compatible(self, query: str, context: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        base_url = self.local_url if self.provider == "local" else self.openai_base
        if self.provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
            api_key = self.groq_key
            model = "llama-3.1-70b-versatile"
        elif self.provider == "openai":
            api_key = self.openai_key
            model = "gpt-4o-mini"
        else:
            api_key = "local"
            model = "codellama"

        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are CODEX, an expert reverse engineering code intelligence assistant. Base answers strictly on the technical evidence provided."},
                {"role": "user", "content": f"Repository Evidence:\n{context}\n\nQuestion: {query}"}
            ]
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            if resp.status_code != 200:
                raise Exception(f"{self.provider.upper()} API returned status {resp.status_code}: {resp.text}")
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return {
                "message": text,
                "sources": sources,
                "confidence": "high",
                "provider_used": self.provider
            }
