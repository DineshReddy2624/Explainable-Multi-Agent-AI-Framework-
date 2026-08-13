from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    org_id: Optional[str] = None
    organization_name: Optional[str] = None
    role: Optional[str] = None  # "ADMIN", "ANALYST", "VIEWER" — defaults to ANALYST in the handler

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        allowed = {"SUPER_ADMIN", "ORG_ADMIN", "ADMIN", "ANALYST", "VIEWER", None}
        if v is not None and v.upper() not in allowed:
            raise ValueError(f"Invalid role '{v}'. Must be one of: SUPER_ADMIN, ORG_ADMIN, ADMIN, ANALYST, VIEWER")
        return v.upper() if v else v


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    org_id: Optional[str] = None
    role: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    org_id: str
    role: str

    model_config = {"from_attributes": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str

