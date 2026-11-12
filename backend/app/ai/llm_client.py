import os
import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Tuple
from backend.app.core.config import settings

class AIIntelligenceClient:
    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.groq_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
        self.openai_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        self.openai_base = settings.OPENAI_BASE_URL
        self.local_url = settings.LOCAL_MODEL_URL

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

        # 4. If few matches, include high-level project summary
        if len(fact_lines) < 3:
            for comp in ctx.get("components", []):
                fact_lines.append(f"Architecture Component '{comp['name']}' ({comp['layer']}) covering files: {', '.join(comp.get('files', [])[:3])}")

        context_text = "\n".join(fact_lines) if fact_lines else "No specific matching symbols found for query keywords."
        return context_text, matched_sources[:8]

    def _deterministic_fallback(
        self,
        query: str,
        retrieved_context: str,
        sources: List[Dict[str, Any]],
        ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Produces factual, grounded analysis strictly from extracted technical facts without requiring an LLM API key.
        """
        q = query.lower()
        endpoints = ctx.get("endpoints", [])
        models = ctx.get("models", [])
        components = ctx.get("components", [])
        health = ctx.get("health", {})

        # Intent: Authentication
        if any(w in q for w in ["auth", "login", "jwt", "token", "password", "register"]):
            auth_eps = [ep for ep in endpoints if any(k in ep["path"].lower() for k in ["auth", "login", "token", "register"])]
            auth_models = [m for m in models if any(k in m["name"].lower() for k in ["user", "account", "token", "session"])]
            
            lines = [
                "### Authentication & Authorization Architecture Analysis",
                "",
                "Based on static AST and route extraction of this codebase:",
                ""
            ]
            if auth_eps:
                lines.append("**Discovered Authentication Endpoints:**")
                for ep in auth_eps:
                    lines.append(f"- `{ep['method']} {ep['path']}` -> Handled by `{ep['handler_name']}` in `{ep['file_path']}` (Line {ep['line_number']})")
                lines.append("")

            if auth_models:
                lines.append("**Identified Identity Models:**")
                for m in auth_models:
                    fields = [f["name"] for f in m.get("fields", [])]
                    lines.append(f"- Model `{m['name']}` ({m.get('orm_framework')}) defined in `{m['file_path']}` with fields: {', '.join(fields)}")
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
            f"### CODEX Static Code Intelligence Response",
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
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "message": text,
                    "sources": sources,
                    "confidence": "high",
                    "provider_used": "gemini"
                }
        except Exception as e:
            raise Exception(f"Gemini API Error: {str(e)}")

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
        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "You are CODEX, an expert reverse engineering code intelligence assistant. Base answers strictly on the technical evidence provided."},
                {"role": "user", "content": f"Repository Evidence:\n{context}\n\nQuestion: {query}"}
            ]
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            return {
                "message": text,
                "sources": sources,
                "confidence": "high",
                "provider_used": self.provider
            }
