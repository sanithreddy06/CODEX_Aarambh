import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

IGNORED_DIRS = {
    "node_modules", ".git", "dist", "build", ".venv", "venv", "env",
    "__pycache__", "vendor", ".idea", ".vscode", "target", ".next",
    ".nuxt", "out", "coverage", ".turbo", ".gradle", "bin", "obj"
}

IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".class", ".o", ".obj", ".so", ".dylib",
    ".dll", ".exe", ".bin", ".tar", ".gz", ".zip", ".png", ".jpg",
    ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot",
    ".mp4", ".mp3", ".pdf", ".lock"
}

EXT_TO_LANGUAGE = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown",
    ".xml": "XML",
    ".prisma": "Prisma Schema",
}

ENTRY_POINT_NAMES = {
    "main.py", "app.py", "server.py", "wsgi.py", "asgi.py", "manage.py",
    "index.js", "server.js", "app.js", "main.js",
    "index.ts", "server.ts", "app.ts", "main.ts",
    "main.go", "Application.java", "Main.java"
}

class RepositoryScanner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.total_files = 0
        self.total_lines = 0
        self.ignored_files = 0
        self.files_by_lang: Dict[str, List[Path]] = {}
        self.languages_count: Dict[str, int] = {}
        self.languages_lines: Dict[str, int] = {}
        self.detected_frameworks: List[Dict[str, Any]] = []
        self.scanned_files: List[Dict[str, Any]] = []

    def scan(self) -> Dict[str, Any]:
        """Performs comprehensive repository traversal and detection."""
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

            for file_name in files:
                full_path = Path(root) / file_name
                rel_path = full_path.relative_to(self.root_dir).as_posix()
                ext = full_path.suffix.lower()

                if ext in IGNORED_EXTENSIONS or file_name.startswith("."):
                    self.ignored_files += 1
                    continue

                lang = EXT_TO_LANGUAGE.get(ext, "Unknown")
                if lang == "Unknown":
                    # Check shebang or filename
                    if file_name.lower() == "dockerfile":
                        lang = "Dockerfile"
                    elif file_name.lower() in ("makefile", "cmakelists.txt"):
                        lang = "Build Script"

                try:
                    file_size = full_path.stat().st_size
                    # Count lines for text files under 2MB
                    line_count = 0
                    if file_size < 2 * 1024 * 1024 and lang not in ("Unknown", "Binary"):
                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                line_count = sum(1 for _ in f)
                        except Exception:
                            line_count = 0
                    
                    self.total_files += 1
                    self.total_lines += line_count
                    self.languages_count[lang] = self.languages_count.get(lang, 0) + 1
                    self.languages_lines[lang] = self.languages_lines.get(lang, 0) + line_count

                    category, layer = self._categorize_file(rel_path, lang)
                    is_entry = file_name in ENTRY_POINT_NAMES or (
                        lang in ("Python", "JavaScript", "TypeScript") and ("main" in file_name or "server" in file_name)
                    )

                    self.scanned_files.append({
                        "relative_path": rel_path,
                        "full_path": str(full_path),
                        "language": lang,
                        "size_bytes": file_size,
                        "line_count": line_count,
                        "category": category,
                        "layer": layer,
                        "is_entry_point": is_entry
                    })

                except Exception:
                    self.ignored_files += 1
                    continue

        # Detect frameworks from configuration files
        self._detect_frameworks()

        # Format language breakdown
        languages_summary = []
        for lang, count in sorted(self.languages_count.items(), key=lambda x: x[1], reverse=True):
            if lang in ("Unknown", "Markdown", "JSON", "YAML", "TOML"):
                continue
            pct = round((count / max(1, self.total_files)) * 100, 1)
            languages_summary.append({
                "language": lang,
                "file_count": count,
                "line_count": self.languages_lines.get(lang, 0),
                "percentage": pct
            })

        primary_lang = languages_summary[0]["language"] if languages_summary else "Unknown"

        return {
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "ignored_files": self.ignored_files,
            "primary_language": primary_lang,
            "languages": languages_summary,
            "frameworks": self.detected_frameworks,
            "files": self.scanned_files
        }

    def _categorize_file(self, rel_path: str, lang: str) -> Tuple[str, str]:
        path_lower = rel_path.lower()
        
        # Test detection
        if any(t in path_lower for t in ["test", "tests", "spec", "__test__"]) or path_lower.endswith(("_test.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js")):
            return "test", "test"

        # Config detection
        if any(c in path_lower for c in ["config", "settings", "env", "dockerfile", "docker-compose", ".json", ".yaml", ".yml", ".toml"]):
            return "config", "config"

        # Database detection
        if any(d in path_lower for d in ["model", "models", "schema", "schemas", "migration", "migrations", "entity", "entities", "db", "database", "repository", "dao", ".sql", ".prisma"]):
            return "database", "database"

        # Frontend detection
        if any(f in path_lower for f in ["frontend", "src/pages", "src/components", "views", "templates", "public", "static", "assets", "styles", "ui", ".tsx", ".jsx", ".vue", ".svelte", ".html", ".css", ".scss"]):
            return "frontend", "presentation"

        # API & Routes
        if any(a in path_lower for a in ["api", "route", "routes", "controller", "controllers", "endpoint", "endpoints"]):
            return "backend", "api"

        # Business Logic / Services
        if any(s in path_lower for s in ["service", "services", "manager", "logic", "usecase", "domain", "handler", "handlers", "worker"]):
            return "backend", "business_logic"

        # Default classification
        if lang in ("Python", "Java", "Go", "Rust", "C#", "PHP", "Ruby"):
            return "backend", "business_logic"
        elif lang in ("JavaScript", "TypeScript"):
            return "frontend" if "src" in path_lower and not ("server" in path_lower or "api" in path_lower) else "backend", "presentation"

        return "other", "unknown"

    def _detect_frameworks(self):
        # Python dependencies
        req_path = self.root_dir / "requirements.txt"
        if req_path.is_file():
            try:
                content = req_path.read_text(encoding="utf-8", errors="ignore").lower()
                if "fastapi" in content: self.detected_frameworks.append({"name": "FastAPI", "type": "backend_framework", "evidence": "requirements.txt"})
                if "flask" in content: self.detected_frameworks.append({"name": "Flask", "type": "backend_framework", "evidence": "requirements.txt"})
                if "django" in content: self.detected_frameworks.append({"name": "Django", "type": "backend_framework", "evidence": "requirements.txt"})
                if "sqlalchemy" in content: self.detected_frameworks.append({"name": "SQLAlchemy", "type": "orm", "evidence": "requirements.txt"})
                if "pytest" in content: self.detected_frameworks.append({"name": "Pytest", "type": "testing", "evidence": "requirements.txt"})
                if "celery" in content: self.detected_frameworks.append({"name": "Celery", "type": "task_queue", "evidence": "requirements.txt"})
            except Exception:
                pass

        # Node / JS / TS dependencies
        pkg_path = self.root_dir / "package.json"
        if not pkg_path.is_file():
            # Check subdirectories for frontend/backend package.json
            for sub_pkg in self.root_dir.glob("*/package.json"):
                pkg_path = sub_pkg
                break

        if pkg_path.is_file():
            try:
                data = json.loads(pkg_path.read_text(encoding="utf-8", errors="ignore"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                rel_pkg = pkg_path.relative_to(self.root_dir).as_posix()
                if "react" in deps: self.detected_frameworks.append({"name": "React", "version": deps["react"], "type": "frontend_library", "evidence": rel_pkg})
                if "vue" in deps: self.detected_frameworks.append({"name": "Vue", "version": deps["vue"], "type": "frontend_framework", "evidence": rel_pkg})
                if "express" in deps: self.detected_frameworks.append({"name": "Express.js", "version": deps["express"], "type": "backend_framework", "evidence": rel_pkg})
                if "next" in deps: self.detected_frameworks.append({"name": "Next.js", "version": deps["next"], "type": "fullstack_framework", "evidence": rel_pkg})
                if "nestjs" in deps or "@nestjs/core" in deps: self.detected_frameworks.append({"name": "NestJS", "type": "backend_framework", "evidence": rel_pkg})
                if "prisma" in deps or "@prisma/client" in deps: self.detected_frameworks.append({"name": "Prisma", "type": "orm", "evidence": rel_pkg})
                if "mongoose" in deps: self.detected_frameworks.append({"name": "Mongoose", "type": "odm", "evidence": rel_pkg})
                if "sequelize" in deps: self.detected_frameworks.append({"name": "Sequelize", "type": "orm", "evidence": rel_pkg})
                if "tailwindcss" in deps: self.detected_frameworks.append({"name": "Tailwind CSS", "type": "styling", "evidence": rel_pkg})
            except Exception:
                pass

        # Java / Spring Boot
        pom_path = self.root_dir / "pom.xml"
        if pom_path.is_file():
            try:
                content = pom_path.read_text(encoding="utf-8", errors="ignore")
                if "spring-boot" in content:
                    self.detected_frameworks.append({"name": "Spring Boot", "type": "backend_framework", "evidence": "pom.xml"})
                if "hibernate" in content:
                    self.detected_frameworks.append({"name": "Hibernate", "type": "orm", "evidence": "pom.xml"})
            except Exception:
                pass

        # Docker
        if (self.root_dir / "Dockerfile").is_file():
            self.detected_frameworks.append({"name": "Docker", "type": "containerization", "evidence": "Dockerfile"})
        if (self.root_dir / "docker-compose.yml").is_file() or (self.root_dir / "docker-compose.yaml").is_file():
            self.detected_frameworks.append({"name": "Docker Compose", "type": "orchestration", "evidence": "docker-compose.yml"})
