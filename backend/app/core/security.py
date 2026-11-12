import os
import re
import stat
import shutil
import zipfile
from pathlib import Path
from typing import Tuple, List, Dict, Any, Set

SECRET_PATTERNS = [
    ("AWS Access Key", re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}")),
    ("GitHub Personal Access Token", re.compile(r"(?:ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82})")),
    ("Slack Webhook / Token", re.compile(r"(?:https:\/\/hooks\.slack\.com\/services\/T[a-zA-Z0-9_]+\/B[a-zA-Z0-9_]+\/[a-zA-Z0-9_]+|xox[baprs]-[0-9a-zA-Z]{10,48})")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{30,40}")),
    ("Stripe API Secret", re.compile(r"(?:sk|pk)_(?:test|live)_[0-9a-zA-Z]{24,}")),
    ("JWT Authentication Token", re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")),
    ("Generic API Key", re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key|auth[_-]?token|access[_-]?token)\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]")),
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA|OPENSSH|DSA|EC|PGP)? PRIVATE KEY-----")),
    ("Database URI Password", re.compile(r"(?i)(?:postgres|mysql|mongodb(?:\+srv)?):\/\/[^:\s]+:([^@\s]+)@")),
    ("Hardcoded Password", re.compile(r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"]([^'\"]{6,})['\"]")),
]

IGNORED_ARCHIVE_DIRS = {
    "node_modules", ".git", ".venv", "venv", "env", "__pycache__",
    ".pytest_cache", "dist", "build", "vendor", ".idea", ".vscode"
}

def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^\w\s\.-]", "_", filename).strip()
    return cleaned or "unnamed_archive.zip"

def validate_and_extract_zip(
    zip_path: str, 
    extract_to: str, 
    max_files: int = 100000, 
    max_total_size: int = 1000 * 1024 * 1024
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates and safely extracts a ZIP archive, strictly guarding against:
    - Path traversal attacks (Zip Slip)
    - Zip bombs (excessive ratio, excessive decompressed bytes, excessive file count)
    - Symlinks, hardlinks, and special device files
    - Duplicate path collisions
    """
    if not zipfile.is_zipfile(zip_path):
        return False, "File is not a valid ZIP archive.", {}

    target_dir = Path(extract_to).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    total_uncompressed_bytes = 0
    total_files = 0
    extracted_files: List[str] = []
    seen_paths: Set[str] = set()

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Step 1: Pre-inspection of all entries before writing any byte
            for info in zf.infolist():
                norm_name = os.path.normpath(info.filename)
                parts = Path(info.filename).parts
                in_ignored_dir = any(p in IGNORED_ARCHIVE_DIRS for p in parts)

                # Check duplicate entries
                if norm_name in seen_paths:
                    return False, f"Duplicate or conflicting path detected in archive: {info.filename}", {}
                seen_paths.add(norm_name)

                # Disallow absolute paths and leading slashes or Windows drive letters
                if info.filename.startswith(("/", "\\")) or re.match(r"^[a-zA-Z]:", info.filename):
                    return False, f"Absolute path detected in archive entry: {info.filename}", {}

                # Check for symlinks and special files in Unix permissions (external_attr >> 16)
                mode = info.external_attr >> 16
                if mode != 0:
                    if stat.S_ISLNK(mode):
                        # Symlinks in dependencies (e.g. node_modules/.bin) are safely ignored
                        if in_ignored_dir:
                            continue
                        return False, f"Symlinks are disallowed for security reasons: {info.filename}", {}
                    if stat.S_ISCHR(mode) or stat.S_ISBLK(mode) or stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode):
                        if in_ignored_dir:
                            continue
                        return False, f"Special device or FIFO file detected in archive: {info.filename}", {}

                total_files += 1
                if total_files > max_files:
                    return False, f"ZIP bomb detected: exceeds max file count limit ({max_files} files).", {}

                total_uncompressed_bytes += info.file_size
                if total_uncompressed_bytes > max_total_size:
                    return False, f"ZIP bomb detected: uncompressed size exceeds limit ({max_total_size // (1024*1024)} MB).", {}

                # Check compression ratio anomaly (>150:1 ratio on large files)
                if info.compress_size > 0 and (info.file_size / info.compress_size > 150) and info.file_size > 5 * 1024 * 1024:
                    return False, "Suspicious compression ratio detected (potential Zip Bomb).", {}

                # Path traversal check (Zip Slip)
                resolved_dest = (target_dir / info.filename).resolve()
                try:
                    resolved_dest.relative_to(target_dir)
                except ValueError:
                    return False, f"Path traversal attempt detected in archive path: {info.filename}", {}

            # Step 2: Safe extraction
            for info in zf.infolist():
                # Skip directories
                if info.is_dir() or info.filename.endswith('/'):
                    continue

                # Skip symlinks (never extract symlinks to disk)
                mode = info.external_attr >> 16
                if mode != 0 and stat.S_ISLNK(mode):
                    continue
                
                dest_path = (target_dir / info.filename).resolve()
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                with zf.open(info) as src, open(dest_path, 'wb') as dst:
                    while chunk := src.read(65536):
                        dst.write(chunk)
                
                extracted_files.append(str(dest_path.relative_to(target_dir)))

        return True, "Archive extracted safely.", {
            "total_files": total_files,
            "extracted_files_count": len(extracted_files),
            "total_uncompressed_bytes": total_uncompressed_bytes
        }
    except Exception as e:
        # Clean up any partially extracted files on failure
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        return False, f"Archive extraction failed: {str(e)}", {}

def scan_file_for_secrets(file_path: str, relative_path: str, max_file_size_kb: int = 1024) -> List[Dict[str, Any]]:
    findings = []
    try:
        p = Path(file_path)
        if not p.is_file() or p.stat().st_size > max_file_size_kb * 1024:
            return findings

        with open(file_path, 'r', errors='ignore') as f:
            for line_no, line in enumerate(f, start=1):
                for secret_name, pattern in SECRET_PATTERNS:
                    match = pattern.search(line)
                    if match:
                        findings.append({
                            "type": "potential_secret",
                            "name": secret_name,
                            "file": relative_path,
                            "line": line_no,
                            "severity": "high",
                            "description": f"Potential {secret_name} found in source code."
                        })
    except Exception:
        pass
    return findings
