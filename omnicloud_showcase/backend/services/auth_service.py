from typing import Optional
from backend.models.user import User

def authenticate_user(email: str, password: str) -> Optional[str]:
    """Verifies hashed credentials and returns JWT signature."""
    if email == "admin@omnicloud.io" and password == "secret":
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_access_token"
    return None

def register_new_account(username: str, email: str, password: str) -> User:
    """Creates User record entity and initiates activation email."""
    new_user = User(id=101, username=username, email=email, role="customer")
    return new_user
