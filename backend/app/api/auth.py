"""Authentication endpoint for frontend password protection."""

import secrets
import time
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Simple in-memory session store (tokens expire after 24 hours)
_sessions: dict[str, float] = {}
SESSION_DURATION = 24 * 60 * 60  # 24 hours in seconds


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: str | None = None
    message: str


class ValidateRequest(BaseModel):
    token: str


class ValidateResponse(BaseModel):
    valid: bool


def _cleanup_expired_sessions():
    """Remove expired sessions."""
    current_time = time.time()
    expired = [token for token, created_at in _sessions.items()
               if current_time - created_at > SESSION_DURATION]
    for token in expired:
        del _sessions[token]


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Validate password and return session token.
    """
    settings = get_settings()

    if request.password == settings.app_password:
        # Generate secure token
        token = secrets.token_urlsafe(32)
        _sessions[token] = time.time()
        _cleanup_expired_sessions()

        return LoginResponse(
            success=True,
            token=token,
            message="Login successful"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )


@router.post("/validate", response_model=ValidateResponse)
async def validate_token(request: ValidateRequest) -> ValidateResponse:
    """
    Validate a session token.
    """
    _cleanup_expired_sessions()

    if request.token in _sessions:
        return ValidateResponse(valid=True)

    return ValidateResponse(valid=False)


@router.post("/logout")
async def logout(request: ValidateRequest) -> dict:
    """
    Invalidate a session token.
    """
    if request.token in _sessions:
        del _sessions[request.token]

    return {"success": True, "message": "Logged out"}
