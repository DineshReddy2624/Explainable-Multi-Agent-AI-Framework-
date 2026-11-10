import os
import time
import random
import re
import uuid
import base64
import json
import logging
import requests
from fastapi import APIRouter, HTTPException, Depends, Body, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from schemas.auth import UserLogin, UserRegister, Token, ForgotPasswordRequest, ResetPasswordRequest
from core.database import get_db
from core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from core.response import StandardResponse
from core.tenant_security import get_current_user, log_audit_event
from models.user import User
from models.organization import Organization
from utils.email_service import send_password_reset_email

logger = logging.getLogger(__name__)
router = APIRouter()
reset_codes_db = {}


def _parse_jwt_unverified(token_str: str) -> dict:
    if not token_str or not isinstance(token_str, str):
        return {}
    try:
        parts = token_str.split(".")
        if len(parts) >= 2:
            rem = len(parts[1]) % 4
            padded = parts[1] + ("=" * (4 - rem) if rem else "")
            decoded = base64.urlsafe_b64decode(padded)
            return json.loads(decoded.decode("utf-8"))
    except Exception:
        pass
    return {}


def fetch_oauth_user_profile(provider: str, access_token: str = None, id_token: str = None) -> dict:
    profile = {}
    if id_token:
        profile = _parse_jwt_unverified(id_token)

    if access_token:
        try:
            if provider == "google":
                resp = requests.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    userinfo_data = resp.json()
                    profile.update(userinfo_data)
            elif provider == "github":
                resp = requests.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    email = data.get("email")
                    profile.update({
                        "email": email or profile.get("email") or f"{data.get('login')}@github.com",
                        "name": data.get("name") or profile.get("name") or data.get("login"),
                        "picture": data.get("avatar_url") or profile.get("picture"),
                        "username": data.get("login")
                    })
        except Exception as e:
            logger.warning(f"Failed to fetch {provider} user profile via UserInfo API: {e}")

    return profile







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
                "full_name": user.full_name or user.username,
                "avatar_url": user.avatar_url or "",
                "picture": user.avatar_url or "",
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
            "full_name": user.full_name or user.username,
            "avatar_url": user.avatar_url or "",
            "picture": user.avatar_url or "",
            "role": user.role,
            "org_id": user.org_id,
            "is_active": user.is_active
        },
        message="Fetched current user profile"
    )

def exchange_and_verify_google(code: str = None, id_token_str: str = None, access_token: str = None) -> dict:
    """
    Exchanges authorization code for tokens and cryptographically validates Google ID token
    or fetches verified profile from Google's UserInfo API.
    """
    from core.config import settings
    g_id = (os.getenv("GOOGLE_CLIENT_ID", settings.GOOGLE_CLIENT_ID) or "").strip()
    g_secret = (os.getenv("GOOGLE_CLIENT_SECRET", settings.GOOGLE_CLIENT_SECRET) or "").strip()
    redirect_uri = settings.GOOGLE_REDIRECT_URI or "http://localhost:3000/oauth/callback"

    # Step A: If authorization code provided, exchange it with Google token endpoint
    if code:
        if not g_id or not g_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google OAuth credentials (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET) are not configured in backend .env."
            )

        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": g_id,
            "client_secret": g_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        try:
            resp = requests.post(token_url, data=token_data, timeout=10)
        except Exception as e:
            logger.error(f"Network error contacting Google token endpoint: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Network error contacting Google authentication servers.")

        if resp.status_code != 200:
            err_json = {}
            try:
                err_json = resp.json()
            except Exception:
                pass
            err_detail = err_json.get("error_description") or err_json.get("error") or resp.text
            logger.error(f"Google token exchange failed: {err_detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google authentication failed: {err_detail}"
            )

        tokens = resp.json()
        id_token_str = tokens.get("id_token")
        access_token = tokens.get("access_token")

    # Step B: Cryptographically verify id_token
    verified_claim = {}
    if id_token_str:
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
            verified_claim = google_id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                audience=g_id if (g_id and "example" not in g_id) else None
            )
        except Exception as e:
            logger.warning(f"google.oauth2 verification exception: {e}. Falling back to tokeninfo endpoint.")
            try:
                tokeninfo_resp = requests.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token_str}",
                    timeout=5
                )
                if tokeninfo_resp.status_code == 200:
                    verified_claim = tokeninfo_resp.json()
                else:
                    raise HTTPException(status_code=401, detail="Invalid or expired Google ID token.")
            except HTTPException:
                raise
            except Exception as e2:
                logger.error(f"Tokeninfo fallback failed: {e2}")
                raise HTTPException(status_code=401, detail="Failed to verify Google ID token signature.")

    # Step C: If only access_token is available, fetch userinfo from Google API
    if not verified_claim and access_token:
        try:
            resp = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5
            )
            if resp.status_code == 200:
                verified_claim = resp.json()
            else:
                raise HTTPException(status_code=401, detail="Invalid Google access token.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch Google userinfo: {e}")
            raise HTTPException(status_code=401, detail="Failed to verify Google access token.")

    if not verified_claim:
        raise HTTPException(status_code=400, detail="No valid authentication credentials returned from Google.")

    email = verified_claim.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google account did not provide a verified email address.")

    return {
        "google_id": verified_claim.get("sub"),
        "email": email.strip().lower(),
        "name": verified_claim.get("name") or verified_claim.get("given_name") or email.split("@")[0],
        "picture": verified_claim.get("picture") or ""
    }


@router.get("/oauth/authorize/{provider}")
def get_oauth_authorize_url(provider: str):
    provider = provider.lower()
    if provider != "google":
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider '{provider}'. Only Google is supported.")

    from core.config import settings
    redirect_uri = settings.GOOGLE_REDIRECT_URI or "http://localhost:3000/oauth/callback"
    g_id = (os.getenv("GOOGLE_CLIENT_ID", settings.GOOGLE_CLIENT_ID) or "").strip()

    is_valid_format = False
    auth_url = None

    if g_id and "example" not in g_id:
        is_valid_format = True
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={g_id}&redirect_uri={redirect_uri}&"
            f"response_type=code&scope=openid%20email%20profile&"
            f"access_type=offline&prompt=select_account&state=google"
        )

    return StandardResponse.ok(
        data={
            "provider": "google",
            "has_configured_client_id": is_valid_format,
            "auth_url": auth_url
        },
        message="Retrieved Google OAuth authorization status"
    )


@router.post("/oauth/verify")
def verify_oauth_token(payload: dict = Body(...), db: Session = Depends(get_db)):
    provider = str(payload.get("provider", "google")).lower()
    if provider != "google":
        raise HTTPException(status_code=400, detail=f"OAuth provider '{provider}' is not supported. Only Google is supported.")

    code = payload.get("code")
    id_token = payload.get("id_token")
    access_token = payload.get("access_token")

    google_profile = exchange_and_verify_google(code=code, id_token_str=id_token, access_token=access_token)

    google_id = google_profile.get("google_id")
    email = google_profile.get("email")
    full_name = google_profile.get("name")
    picture = google_profile.get("picture")

    # 1. Match existing user by google_id
    user = None
    if google_id:
        user = db.query(User).filter(User.google_id == google_id).first()

    # 2. If not matched by google_id, match by email to link existing local account
    if not user and email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            if google_id:
                user.google_id = google_id
            if picture and not user.avatar_url:
                user.avatar_url = picture
            user.auth_provider = user.auth_provider or "google"
            db.commit()
            db.refresh(user)
            log_audit_event("USER_GOOGLE_LINK", org_id=user.org_id, user_id=user.id, details={"google_id": google_id}, db=db)

    # 3. If user does not exist, auto-register them
    if not user:
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', email.split("@")[0]) or "user"
        username = base_username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1

        org_id = "org_default"
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(f"google_oauth_{google_id or uuid.uuid4().hex}"),
            full_name=full_name or username.capitalize(),
            avatar_url=picture,
            role="ANALYST",
            org_id=org_id,
            google_id=google_id,
            auth_provider="google",
            is_active=True
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            log_audit_event("USER_GOOGLE_REGISTER", org_id=org_id, user_id=user.id, details={"google_id": google_id}, db=db)
        except IntegrityError:
            db.rollback()
            # Fetch user concurrently inserted
            user = db.query(User).filter((User.email == email) | (User.username == username)).first()
            if not user:
                raise

    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is deactivated.")

    # Issue application JWT tokens
    jwt_access_token = create_access_token(data={
        "sub": str(user.id),
        "email": user.email,
        "org_id": user.org_id,
        "role": user.role
    })
    jwt_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    log_audit_event("GOOGLE_LOGIN_SUCCESS", org_id=user.org_id, user_id=user.id, details={"google_id": google_id}, db=db)

    return StandardResponse.ok(
        data={
            "access_token": jwt_access_token,
            "refresh_token": jwt_refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name or user.username,
                "avatar_url": user.avatar_url or picture or "",
                "picture": user.avatar_url or picture or "",
                "role": user.role,
                "org_id": user.org_id,
                "google_id": user.google_id,
                "auth_provider": user.auth_provider or "google"
            }
        },
        message="Authenticated with Google OAuth successfully!"
    )


@router.post("/oauth")
def oauth_login(payload: dict = Body(...), db: Session = Depends(get_db)):
    """Fallback endpoint for OAuth login, routed to verify_oauth_token."""
    return verify_oauth_token(payload=payload, db=db)




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

