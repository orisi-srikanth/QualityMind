"""
Authentication & Persona Endpoints
Provides JWT Bearer tokens for demo personas and retrieves user profile details.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.app.core.security import create_access_token

router = APIRouter()

class LoginPayload(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "engineer@precisionaero.com"}, description="User email (admin, engineer, operator)")
    password: str = Field(..., json_schema_extra={"example": "Engineer123!"}, description="User password")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str

@router.post("/auth/login", tags=["Auth"], summary="Authenticate user persona", description="Generates JWT bearer token for demo personas: admin@precisionaero.com, engineer@precisionaero.com, operator@precisionaero.com.")
def login(payload: LoginPayload):
    user_roles = {
        "admin@precisionaero.com": "admin",
        "engineer@precisionaero.com": "quality_engineer",
        "operator@precisionaero.com": "operator"
    }
    role = user_roles.get(payload.username, "quality_engineer")
    token = create_access_token({"sub": payload.username, "role": role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": role,
        "name": payload.username.split("@")[0].capitalize()
    }

@router.get("/auth/me", tags=["Auth"], summary="Get current user profile", description="Returns authenticated profile including root cause confirmation authorization flag.")
def get_me():
    return {
        "id": "usr-qe-01",
        "name": "Sarah Chen, Lead Quality Engineer",
        "email": "engineer@precisionaero.com",
        "role": "quality_engineer",
        "authorized_to_confirm_root_cause": True
    }
