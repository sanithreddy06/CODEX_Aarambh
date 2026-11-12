from typing import Dict, Any
from fpdf import FPDF
from fpdf.enums import XPos, YPos

def sanitize_pdf_text(text: str) -> str:
    """Replaces Unicode characters outside latin-1 to prevent FPDF encoding crashes."""
    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "✓": "[X]",
        "✔": "[X]",
        "✗": "[ ]",
        "→": "->",
        "←": "<-",
        "•": "*",
        "…": "...",
        "\u200b": "",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")

class DocumentationGenerator:
    def generate_markdown(self, project: Dict[str, Any], overview: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Constructs comprehensive 14-section markdown technical specification."""
        proj_name = project.get("name", "Project CODEX")
        desc = project.get("description", "Autonomously Analyzed Codebase")
        pri_lang = project.get("primary_language", "Unknown")
        total_files = project.get("total_files", 0)
        total_lines = project.get("total_lines", 0)
        health_score = project.get("health_score", 100)

        endpoints = analysis.get("endpoints", [])
        models = analysis.get("models", [])
        components = analysis.get("components", [])
        dependencies = analysis.get("dependencies", {})
        findings = analysis.get("findings", [])
        workflows = analysis.get("workflows", [])
        tests = analysis.get("tests", [])

        md = f"""# {proj_name} — Architectural Intelligence & Technical Specification
> Generated autonomously by **CODEX** (Autonomous Software Reverse Engineering & Code Intelligence)

---

## 1. Executive Summary
This document provides an evidence-based reverse-engineered architectural and technical evaluation of **{proj_name}**.
Using static AST analysis, dependency graph topology, route discovery, and database schema extraction, CODEX reconstructed the application's internal structure without requiring original developer documentation.

- **Primary Stack:** {pri_lang}
- **Total Source Files:** {total_files}
- **Total Lines of Code:** {total_lines:,}
- **Discovered REST Endpoints:** {len(endpoints)}
- **Discovered Database Models:** {len(models)}
- **Calculated Health Score:** {health_score}/100

---

## 2. Project Overview
- **Project Name:** {proj_name}
- **Description:** {desc}
- **Archive Source:** `{project.get("original_archive_name", "upload.zip")}`
- **Analysis Timestamp:** `{project.get("created_at", "N/A")}`

---

## 3. Technology Stack
The following languages, frameworks, and tools were identified via configuration analysis and source AST parsing:

| Technology | Category | Detection Evidence |
|------------|----------|-------------------|
"""
        for fw in project.get("frameworks", []):
            md += f"| **{fw.get('name')}** | {fw.get('type', 'Framework')} | `{fw.get('evidence', 'manifest')}` |\n"
        for lang in project.get("languages", []):
            md += f"| **{lang.get('language')}** | Language ({lang.get('percentage')}%) | `{lang.get('file_count')} files` |\n"

        md += """
---

## 4. Repository Structure & File Classification
Source code distribution categorized by architectural role:

| Category | File Count | Percentage |
|----------|------------|------------|
"""
        cat_breakdown = overview.get("categories_breakdown", {})
        for cat, cnt in cat_breakdown.items():
            pct = round((cnt / max(1, total_files)) * 100, 1)
            md += f"| {cat.capitalize()} | {cnt} | {pct}% |\n"

        md += """
---

## 5. Architecture Overview
Reconstructed multi-tier operational architecture based on static import topologies:

"""
        for c in components:
            md += f"### {c.get('name')} (`{c.get('layer')}`)\n"
            md += "- **Responsibilities:**\n"
            for r in c.get("responsibilities", []):
                md += f"  - {r}\n"
            md += f"- **Files Covered:** `{len(c.get('files', []))} files`\n"
            md += f"- **Evidence:** Discovered via {c.get('evidence', {}).get('detection_method', 'static_analysis')}\n\n"

        md += """---

## 6. Discovered API Routes & Endpoints
The following HTTP interface contracts were cataloged:

| Method | Route Path | Controller Handler | Auth Middleware | Source File |
|--------|------------|-------------------|-----------------|-------------|
"""
        for ep in endpoints:
            auth_str = ep.get("auth_middleware") or "None (Public)"
            md += f"| `{ep.get('method')}` | `{ep.get('path')}` | `{ep.get('handler_name')}()` | `{auth_str}` | `{ep.get('file_path')}:{ep.get('line_number')}` |\n"

        md += """
---

## 7. Database Entities & Schemas
Discovered persistent models, schemas, and relational links:

"""
        for m in models:
            md += f"### Entity: `{m.get('name')}` ({m.get('orm_framework', 'ORM')})\n"
            md += f"- **Source File:** `{m.get('file_path')}` (Line {m.get('line_number')})\n"
            md += "| Field Name | Data Type | Primary Key | Foreign Key |\n"
            md += "|------------|-----------|-------------|-------------|\n"
            for f in m.get("fields", []):
                is_pk = "✓" if f.get("primary_key") else ""
                fk = f.get("foreign_key") or "-"
                md += f"| `{f.get('name')}` | `{f.get('type')}` | {is_pk} | `{fk}` |\n"
            md += "\n"

        md += """---

## 8. Dependency Graph Analysis
- **Circular Dependencies:** """
        circs = dependencies.get("circular_dependencies", [])
        if circs:
            md += f"⚠️ Detected {len(circs)} circular dependency cycle(s):\n"
            for c in circs:
                md += f"  - `{' -> '.join(c)}`\n"
        else:
            md += "None detected (Clean acyclic hierarchy).\n"

        md += "\n### High Dependency Hubs:\n"
        for h in dependencies.get("high_dependency_modules", []):
            md += f"- **{h.get('label')}**: Total Degree {h.get('total_degree')} ({h.get('in_degree')} in, {h.get('out_degree')} out) — *{h.get('centrality_role')}*\n"

        md += """
---

## 9. Reconstructed Application Workflows
Operational transaction paths tracing end-to-end execution:

"""
        for wf in workflows:
            md += f"### Workflow: {wf.get('name')}\n"
            md += f"**Trigger:** `{wf.get('trigger')}`\n\n"
            for s in wf.get("steps", []):
                md += f"{s.get('order')}. **[{s.get('layer', 'Core')}] {s.get('component')}**: {s.get('action')} (`{s.get('file')}`)\n"
            md += "\n"

        md += """---

## 10. Software Health & Architectural Findings
Identified security flags, structural hazards, and complexity concerns:

"""
        for f in findings:
            md += f"- **[{f.get('severity', 'info').upper()}] {f.get('title')}**\n"
            md += f"  - {f.get('description')}\n"
            if f.get("affected_files"):
                md += f"  - *Affected Files:* `{', '.join(f.get('affected_files')[:3])}`\n"
            md += "\n"

        md += """---

## 11. Modernization & Migration Recommendations
Opportunities to reduce technical debt and upgrade legacy components:
1. **Containerization & CI/CD:** Ensure isolated build stages and automated static linting.
2. **Type Safety & Schemas:** Enforce strict type validation across route boundaries.
3. **Decouple Central Hubs:** Refactor identified high-degree modules into distinct micro-services or focused single-purpose utilities.

---

## 12. Reconstructed Test Scenarios
Automatically generated unit and integration test specifications:

"""
        for t in tests[:5]:
            md += f"### Test Case: `{t.get('test_name')}` ({t.get('test_framework')})\n"
            md += f"```python\n{t.get('code')}\n```\n\n"

        md += """---

## 13. Analysis Limitations & Verifiability Statement
- Analysis performed strictly via static AST inspection, dependency topology, and pattern extraction.
- Dynamic runtime execution and live load profiling were not performed.
- Relationships marked as 'confirmed' are directly backed by AST import or model reference declarations.
- AI answers and generated tests should be reviewed by engineering staff prior to production deployment.
"""
        return md

    def generate_pdf(self, md_content: str, output_path: str):
        """Generates clean PDF document using fpdf2."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Document Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, "CODEX Technical Intelligence Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(5)

        pdf.set_font("Helvetica", "", 10)
        for line in md_content.splitlines():
            clean = sanitize_pdf_text(line.replace("#", "").replace("*", "").replace("`", "").strip())
            if not clean:
                pdf.ln(3)
                continue
            
            if line.startswith("# "):
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 8, clean, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Helvetica", "", 10)
            elif line.startswith("## "):
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 7, clean, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Helvetica", "", 10)
            elif line.startswith("### "):
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 6, clean, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Helvetica", "", 10)
            else:
                # Regular text
                try:
                    pdf.multi_cell(0, 5, clean)
                except Exception:
                    pass

        pdf.output(output_path)
