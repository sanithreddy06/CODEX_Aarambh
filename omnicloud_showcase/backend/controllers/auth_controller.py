from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from backend.services.auth_service import authenticate_user, register_new_account
from backend.models.user import User

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

@router.post("/login")
async def login(payload: LoginRequest):
    """Authenticates user credentials and issues signed JWT bearer token."""
    token = authenticate_user(payload.email, payload.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"access_token": token, "token_type": "bearer"}

@router.post("/register")
async def register(payload: RegisterRequest):
    """Enrolls a new customer account in database."""
    user = register_new_account(payload.username, payload.email, payload.password)
    return {"status": "created", "user_id": user.id, "email": user.email}
