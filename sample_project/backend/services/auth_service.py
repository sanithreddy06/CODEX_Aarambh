import hashlib
from typing import Optional

def hash_password(password: str) -> str:
    """Computes SHA-256 hash for password."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that plaintext password matches hash."""
    return hash_password(plain_password) == hashed_password

def generate_access_token(user_id: int, email: str) -> str:
    """Generates mock JWT access token."""
    raw = f"{user_id}:{email}:codex_secret"
    return hashlib.sha256(raw.encode()).hexdigest()
