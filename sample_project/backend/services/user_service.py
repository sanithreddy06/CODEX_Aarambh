from typing import Dict, Any, Optional
from sample_project.backend.services.auth_service import hash_password

fake_users_db = []

def create_user(email: str, password: str, full_name: str = "") -> Dict[str, Any]:
    """Creates and persists a new user account."""
    hashed = hash_password(password)
    user = {
        "id": len(fake_users_db) + 1,
        "email": email,
        "hashed_password": hashed,
        "full_name": full_name,
        "is_active": True
    }
    fake_users_db.append(user)
    return user

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves user record by email."""
    for u in fake_users_db:
        if u["email"] == email:
            return u
    return None
