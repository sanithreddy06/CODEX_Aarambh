from fastapi import APIRouter, HTTPException, Depends
from sample_project.backend.schemas.user_schema import UserCreate, UserLogin, UserResponse, TokenResponse
from sample_project.backend.services.user_service import create_user, get_user_by_email
from sample_project.backend.services.auth_service import verify_password, generate_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register_user(payload: UserCreate):
    """Registers a new user account with validated credentials."""
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = create_user(payload.email, payload.password, payload.full_name)
    return user

@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin):
    """Authenticates credentials and returns a Bearer access token."""
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = generate_access_token(user["id"], user["email"])
    return {"access_token": token, "token_type": "bearer"}
