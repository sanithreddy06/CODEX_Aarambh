from typing import Dict, List, Any
from backend.app.core.security import scan_file_for_secrets
from pathlib import Path

class HealthAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()

    def analyze(
        self,
        files: List[Dict[str, Any]],
        parsed_files: Dict[str, Dict[str, Any]],
        dependencies: Dict[str, Any],
        frameworks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates an evidence-backed software health score and compiles
        prioritized architectural findings.
        """
        findings: List[Dict[str, Any]] = []
        base_score = 100

        # 1. Secret Scanner (Security findings)
        secret_findings = []
        for f in files:
            full_path = self.root_dir / f["relative_path"]
            sec_hits = scan_file_for_secrets(str(full_path), f["relative_path"])
            for h in sec_hits:
                secret_findings.append(h)
                findings.append({
                    "id": f"sec_{len(findings)+1}",
                    "category": "security",
                    "title": f"Hardcoded Secret: {h['name']}",
                    "description": f"Potential credential or API secret exposed directly in source code at {h['file']}:{h['line']}",
                    "severity": "critical",
                    "affected_files": [h["file"]],
                    "evidence": {"line": h["line"], "detection_method": "regex_entropy_scan"}
                })
                base_score -= 15

        # 2. Circular Dependencies
        cycles = dependencies.get("circular_dependencies", [])
        if cycles:
            for cycle in cycles:
                findings.append({
                    "id": f"circ_{len(findings)+1}",
                    "category": "circular_dependency",
                    "title": "Circular Dependency Cycle Detected",
                    "description": f"Cyclic dependency chain identified: {' -> '.join(cycle)}",
                    "severity": "high",
                    "affected_files": cycle,
                    "evidence": {"cycle_path": cycle, "detection_method": "dfs_cycle_detection"}
                })
                base_score -= 8

        # 3. High Dependency Concentration (Hubs)
        high_deps = dependencies.get("high_dependency_modules", [])
        for hub in high_deps:
            if hub.get("total_degree", 0) > 10:
                findings.append({
                    "id": f"hub_{len(findings)+1}",
                    "category": "complexity",
                    "title": f"High Dependency Concentration: {hub['label']}",
                    "description": f"Module '{hub['label']}' has {hub['total_degree']} connections ({hub['in_degree']} incoming, {hub['out_degree']} outgoing). Changes pose broad blast-radius risk.",
                    "severity": "medium",
                    "affected_files": [hub["node_id"]],
                    "evidence": {"metrics": hub, "detection_method": "degree_centrality"}
                })
                base_score -= 4

        # 4. Large Files / Complexity
        large_files = [f for f in files if f.get("line_count", 0) > 400]
        for lf in large_files:
            findings.append({
                "id": f"cpx_{len(findings)+1}",
                "category": "complexity",
                "title": f"High File Complexity: {Path(lf['relative_path']).name}",
                "description": f"Source file has {lf['line_count']} lines. Files over 400 lines violate Single Responsibility and increase maintenance burden.",
                "severity": "low",
                "affected_files": [lf["relative_path"]],
                "evidence": {"line_count": lf["line_count"], "threshold": 400}
            })
            base_score -= 2

        # 5. Isolated / Dead Code Modules
        isolated = dependencies.get("isolated_modules", [])
        # Filter out entry points or configs
        dead_candidates = [
            m for m in isolated 
            if not any(k in m.lower() for k in ["main", "app", "index", "server", "config", "test", "docker", "setup", "readme"])
        ]
        if dead_candidates:
            findings.append({
                "id": f"iso_{len(findings)+1}",
                "category": "isolated_module",
                "title": f"Potentially Unused / Isolated Modules ({len(dead_candidates)} files)",
                "description": f"Found {len(dead_candidates)} source files with zero internal imports or references.",
                "severity": "info",
                "affected_files": dead_candidates[:10],
                "evidence": {"files": dead_candidates}
            })
            base_score -= 2

        # 6. Documentation Coverage
        total_functions = 0
        documented_functions = 0
        for rel, parsed in parsed_files.items():
            for ent in parsed.get("entities", []):
                if ent.get("entity_type") in ("function", "method"):
                    total_functions += 1
                    if ent.get("docstring"):
                        documented_functions += 1

        if total_functions > 0:
            doc_ratio = documented_functions / total_functions
            if doc_ratio < 0.25:
                findings.append({
                    "id": f"doc_{len(findings)+1}",
                    "category": "documentation",
                    "title": "Low Inline Documentation Coverage",
                    "description": f"Only {round(doc_ratio * 100, 1)}% of functions ({documented_functions}/{total_functions}) contain docstrings or type signatures.",
                    "severity": "medium",
                    "affected_files": [],
                    "evidence": {"doc_coverage": round(doc_ratio * 100, 1), "documented": documented_functions, "total": total_functions}
                })
                base_score -= 5

        # 7. Modernization / Legacy Recommendations
        for fw in frameworks:
            fw_name = fw.get("name", "")
            fw_ver = fw.get("version", "")
            if fw_name == "React" and fw_ver and any(fw_ver.startswith(v) for v in ["^15", "^16", "^17"]):
                findings.append({
                    "id": f"leg_{len(findings)+1}",
                    "category": "deprecated_tech",
                    "title": f"Legacy React Version: {fw_ver}",
                    "description": "Legacy React detected. Modernizing to React 18/19 unlocks React Server Components, concurrent rendering, and active security maintenance.",
                    "severity": "medium",
                    "affected_files": ["package.json"],
                    "evidence": {"current_version": fw_ver, "recommended": "React 19"}
                })
                base_score -= 5

        # Bound health score between 20 and 100
        health_score = max(20, min(100, base_score))

        # Grade calculation
        if health_score >= 90: grade = "A"
        elif health_score >= 80: grade = "B"
        elif health_score >= 70: grade = "C"
        elif health_score >= 60: grade = "D"
        else: grade = "F"

        # Tally summaries
        sev_counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        cat_counts: Dict[str, int] = {}
        for f in findings:
            s = f["severity"]
            sev_counts[s] = sev_counts.get(s, 0) + 1
            c = f["category"]
            cat_counts[c] = cat_counts.get(c, 0) + 1

        return {
            "health_score": health_score,
            "grade": grade,
            "findings": findings,
            "summary_by_severity": sev_counts,
            "summary_by_category": cat_counts
        }
