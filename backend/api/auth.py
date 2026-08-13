import random
from fastapi import APIRouter, HTTPException
from schemas.auth import UserLogin, UserRegister, Token, ForgotPasswordRequest, ResetPasswordRequest
from core.security import create_access_token, get_password_hash, verify_password
from core.response import StandardResponse
from utils.email_service import send_password_reset_email

router = APIRouter()

# In-memory store for verification codes (or stored in DB/Redis in prod)
reset_codes_db = {}

from fastapi import APIRouter, HTTPException, Depends, Body, status
from sqlalchemy.orm import Session
from schemas.auth import UserLogin, UserRegister, Token, ForgotPasswordRequest, ResetPasswordRequest
from core.database import get_db
from core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from core.response import StandardResponse
from core.tenant_security import get_current_user, log_audit_event
from models.user import User
from models.organization import Organization
from utils.email_service import send_password_reset_email

router = APIRouter()
reset_codes_db = {}

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    email_or_user = credentials.email.strip()
    user = db.query(User).filter((User.email == email_or_user) | (User.username == email_or_user)).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        log_audit_event("LOGIN_FAILED", org_id="org_default", details={"identifier": email_or_user}, db=db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials."
        )

    if not user.is_active:
        log_audit_event("LOGIN_FAILED", org_id=user.org_id, user_id=user.id, details={"reason": "inactive"}, db=db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive."
        )

    access_token = create_access_token(data={
        "sub": str(user.id),
        "email": user.email,
        "org_id": user.org_id,
        "role": user.role
    })
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    log_audit_event("LOGIN_SUCCESS", org_id=user.org_id, user_id=user.id, db=db)

    return StandardResponse.ok(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "org_id": user.org_id
            }
        },
        message="Login successful"
    )

@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="User with this username already exists.")

    org_id = getattr(user_data, "org_id", None)
    if not org_id and getattr(user_data, "organization_name", None):
        import re
        org_id = "org_" + re.sub(r'[^a-zA-Z0-9_]', '_', user_data.organization_name.lower())
    if not org_id:
        org_id = "org_default"

    role = getattr(user_data, "role", "ANALYST") or "ANALYST"

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name or "",
        role=role.upper(),
        org_id=org_id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit_event("USER_CREATED", org_id=org_id, user_id=new_user.id, details={"email": new_user.email, "role": new_user.role}, db=db)

    return StandardResponse.ok(
        data={
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "org_id": new_user.org_id
        },
        message="User registered successfully"
    )


@router.post("/refresh")
def refresh_token_endpoint(payload: dict = Body(...), db: Session = Depends(get_db)):
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh_token.")

    try:
        decoded = decode_token(refresh_token)
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type for refresh.")

        user_id = decoded.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User inactive or missing.")

        new_access_token = create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "org_id": user.org_id,
            "role": user.role
        })

        log_audit_event("TOKEN_REFRESH", org_id=user.org_id, user_id=user.id, db=db)

        return StandardResponse.ok(
            data={"access_token": new_access_token, "token_type": "bearer"},
            message="Token refreshed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {str(e)}")

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return StandardResponse.ok(
        data={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "org_id": user.org_id,
            "is_active": user.is_active
        },
        message="Fetched current user profile"
    )

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    # Generate 6-digit OTP code
    otp_code = str(random.randint(100000, 999999))
    reset_codes_db[req.email] = otp_code

    # Dispatch email asynchronously via SMTP
    sent_success = send_password_reset_email(req.email, otp_code)

    if not sent_success:
        raise HTTPException(status_code=500, detail="Failed to dispatch reset email via SMTP server.")

    return StandardResponse.ok(
        data={"email": req.email},
        message=f"Verification code sent to {req.email}. Please check your inbox."
    )

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    stored_code = reset_codes_db.get(req.email)
    if not stored_code or stored_code != req.reset_code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    # Remove used code
    reset_codes_db.pop(req.email, None)

    return StandardResponse.ok(
        data={"email": req.email},
        message="Password reset successfully. You may now log in with your new password."
    )
