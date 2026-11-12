from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, deque
from pathlib import Path

class DependencyGraphAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.adj_list: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_adj: Dict[str, Set[str]] = defaultdict(set)

    def add_node(self, node_id: str, label: str, node_type: str, language: str = "", layer: str = "", line_count: int = 0):
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "language": language,
            "layer": layer,
            "line_count": line_count
        }

    def add_edge(self, source: str, target: str, edge_type: str = "import", confidence: str = "confirmed", evidence: Dict[str, Any] = None):
        edge = {
            "id": f"{source}->{target}",
            "source": source,
            "target": target,
            "edge_type": edge_type,
            "confidence": confidence,
            "evidence": evidence or {}
        }
        self.edges.append(edge)
        self.adj_list[source].add(target)
        self.reverse_adj[target].add(source)

    def build_graph(self, files_metadata: List[Dict[str, Any]], parsed_files: Dict[str, Dict[str, Any]]):
        """Constructs graph from scanned files and their parsed imports/calls."""
        file_paths = {f["relative_path"]: f for f in files_metadata}

        for rel_path, meta in file_paths.items():
            self.add_node(
                node_id=rel_path,
                label=Path(rel_path).name,
                node_type="file",
                language=meta.get("language", ""),
                layer=meta.get("layer", ""),
                line_count=meta.get("line_count", 0)
            )

        # Resolve imports to other files in repository
        for rel_path, parsed in parsed_files.items():
            imports = parsed.get("imports", [])
            for imp in imports:
                target_rel = self._resolve_import(rel_path, imp["source"], file_paths)
                if target_rel and target_rel != rel_path:
                    self.add_edge(
                        source=rel_path,
                        target=target_rel,
                        edge_type="import",
                        confidence="confirmed",
                        evidence={
                            "imported_symbol": imp.get("imported"),
                            "line": imp.get("line"),
                            "raw_source": imp.get("source")
                        }
                    )

    def _resolve_import(self, current_file: str, import_src: str, file_paths: Dict[str, Any]) -> str:
        """Resolves relative and package imports to actual files in the repository."""
        curr_dir = Path(current_file).parent
        
        # Relative import (JS/TS or Python)
        if import_src.startswith("."):
            clean_src = import_src.lstrip("./")
            candidate = (curr_dir / clean_src).as_posix()
            candidates = [
                candidate,
                f"{candidate}.py",
                f"{candidate}.ts",
                f"{candidate}.tsx",
                f"{candidate}.js",
                f"{candidate}.jsx",
                f"{candidate}/index.ts",
                f"{candidate}/index.js",
                f"{candidate}/__init__.py"
            ]
            for cand in candidates:
                cand_clean = cand.lstrip("./")
                if cand_clean in file_paths:
                    return cand_clean

        # Python package style import: e.g. "backend.app.models" or "app.models"
        py_path = import_src.replace(".", "/")
        py_candidates = [
            f"{py_path}.py",
            f"{py_path}/__init__.py"
        ]
        for c in py_candidates:
            if c in file_paths:
                return c

        # Exact match or suffix match
        for f in file_paths:
            if f.endswith(f"/{import_src}.py") or f.endswith(f"/{import_src}.ts") or f.endswith(f"/{import_src}.js"):
                return f

        return ""

    def detect_circular_dependencies(self) -> List[List[str]]:
        """Identifies circular dependencies (cycles) using DFS cycle detection."""
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
        cycles: List[List[str]] = []

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            path.append(node)

            for neighbor in self.adj_list.get(node, set()):
                if visited.get(neighbor, 0) == 1:
                    cycle_start_idx = path.index(neighbor)
                    cycle = path[cycle_start_idx:] + [neighbor]
                    cycles.append(cycle)
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor, path)

            path.pop()
            visited[node] = 2

        for node in list(self.nodes.keys()):
            if visited.get(node, 0) == 0:
                dfs(node, [])

        return cycles[:10]  # Limit to top 10 cycles

    def find_high_dependency_modules(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Finds modules with highest in-degree (heavily depended on) and out-degree."""
        scores = []
        for node_id in self.nodes:
            in_deg = len(self.reverse_adj.get(node_id, set()))
            out_deg = len(self.adj_list.get(node_id, set()))
            scores.append({
                "node_id": node_id,
                "label": self.nodes[node_id]["label"],
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_degree": in_deg + out_deg,
                "centrality_role": "Hub (High Fan-out)" if out_deg > in_deg else "Core Utility (High Fan-in)"
            })
        scores.sort(key=lambda x: x["total_degree"], reverse=True)
        return scores[:top_n]

    def find_isolated_modules(self) -> List[str]:
        """Finds modules with 0 incoming and 0 outgoing edges (excluding entry points)."""
        isolated = []
        for node_id in self.nodes:
            in_deg = len(self.reverse_adj.get(node_id, set()))
            out_deg = len(self.adj_list.get(node_id, set()))
            if in_deg == 0 and out_deg == 0:
                isolated.append(node_id)
        return isolated

    def analyze_impact(self, target_node: str, max_depth: int = 4) -> Dict[str, Any]:
        """
        Dependency impact analysis:
        Calculates which components will be affected if target_node is changed.
        Uses reverse adjacency to traverse backwards to all dependents.
        """
        if target_node not in self.nodes:
            return {
                "target_node": target_node,
                "direct_dependents": [],
                "indirect_dependents": [],
                "affected_files": [],
                "severity": "low",
                "evidence": []
            }

        direct = list(self.reverse_adj.get(target_node, set()))
        indirect: Set[str] = set()
        queue = deque([(dep, 1) for dep in direct])
        visited: Set[str] = set(direct)
        evidence = []

        for d in direct:
            evidence.append({
                "dependent": d,
                "depends_on": target_node,
                "relationship": "direct_import",
                "depth": 1
            })

        while queue:
            curr, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for parent in self.reverse_adj.get(curr, set()):
                if parent not in visited and parent != target_node:
                    visited.add(parent)
                    indirect.add(parent)
                    queue.append((parent, depth + 1))
                    evidence.append({
                        "dependent": parent,
                        "depends_on": curr,
                        "relationship": "transitive_import",
                        "depth": depth + 1
                    })

        all_affected = list(visited)
        total_nodes = max(1, len(self.nodes))
        pct_affected = (len(all_affected) / total_nodes) * 100

        if pct_affected > 40:
            severity = "critical"
        elif pct_affected > 20:
            severity = "high"
        elif pct_affected > 5:
            severity = "medium"
        else:
            severity = "low"

        return {
            "target_node": target_node,
            "direct_dependents": direct,
            "indirect_dependents": list(indirect),
            "affected_files": all_affected,
            "severity": severity,
            "evidence": evidence
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "circular_dependencies": self.detect_circular_dependencies(),
            "high_dependency_modules": self.find_high_dependency_modules(),
            "isolated_modules": self.find_isolated_modules()
        }
