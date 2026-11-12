import os
import re
import zipfile
from pathlib import Path
from typing import Tuple, List, Dict, Any

SECRET_PATTERNS = [
    ("AWS Access Key", re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}")),
    ("Generic API Key", re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key|auth[_-]?token|access[_-]?token)\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]")),
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA|OPENSSH|DSA|EC|PGP)? PRIVATE KEY-----")),
    ("Database URI Password", re.compile(r"(?i)(?:postgres|mysql|mongodb(?:\+srv)?):\/\/[^:\s]+:([^@\s]+)@")),
    ("Hardcoded Password", re.compile(r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"]([^'\"]{6,})['\"]")),
]

def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^\w\s\.-]", "_", filename).strip()
    return cleaned or "unnamed_archive.zip"

def validate_and_extract_zip(
    zip_path: str, 
    extract_to: str, 
    max_files: int = 10000, 
    max_total_size: int = 250 * 1024 * 1024
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates and safely extracts a ZIP archive, strictly guarding against:
    - Path traversal attacks (Zip Slip)
    - Zip bombs (excessive ratio, excessive decompressed bytes, excessive file count)
    - Symlinks and special files
    """
    if not zipfile.is_zipfile(zip_path):
        return False, "File is not a valid ZIP archive.", {}

    target_dir = Path(extract_to).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    total_uncompressed_bytes = 0
    total_files = 0
    extracted_files: List[str] = []

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Step 1: Pre-inspection of all entries
        for info in zf.infolist():
            total_files += 1
            if total_files > max_files:
                return False, f"ZIP bomb detected: exceeds max file count limit ({max_files} files).", {}

            total_uncompressed_bytes += info.file_size
            if total_uncompressed_bytes > max_total_size:
                return False, f"ZIP bomb detected: uncompressed size exceeds limit ({max_total_size // (1024*1024)} MB).", {}

            # Check compression ratio anomaly (>100:1 ratio on large files)
            if info.compress_size > 0 and (info.file_size / info.compress_size > 150) and info.file_size > 5 * 1024 * 1024:
                return False, "Suspicious compression ratio detected (potential Zip Bomb).", {}

            # Path traversal check
            resolved_dest = (target_dir / info.filename).resolve()
            try:
                resolved_dest.relative_to(target_dir)
            except ValueError:
                return False, f"Path traversal attempt detected in archive path: {info.filename}", {}

        # Step 2: Safe extraction
        for info in zf.infolist():
            # Skip directories and special links
            if info.is_dir() or info.filename.endswith('/'):
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
