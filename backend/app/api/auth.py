"""Authentication endpoint for frontend password protection."""

import hashlib
import secrets
import time
from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Session store: token -> {user_id, created_at}
_sessions: dict[str, dict] = {}
SESSION_DURATION = 24 * 60 * 60  # 24 hours in seconds

# Header for user token
USER_TOKEN_HEADER = APIKeyHeader(name="X-User-Token", auto_error=False)


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: str | None = None
    user_id: str | None = None
    message: str


class ValidateRequest(BaseModel):
    token: str


class ValidateResponse(BaseModel):
    valid: bool


def _cleanup_expired_sessions():
    """Remove expired sessions."""
    current_time = time.time()
    expired = [token for token, data in _sessions.items()
               if current_time - data["created_at"] > SESSION_DURATION]
    for token in expired:
        del _sessions[token]


def _generate_user_id() -> str:
    """Generate a unique user ID."""
    return secrets.token_hex(16)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Validate password and return session token with user ID.
    """
    settings = get_settings()

    if request.password == settings.app_password:
        # Generate secure token and user ID
        token = secrets.token_urlsafe(32)
        user_id = _generate_user_id()

        _sessions[token] = {
            "user_id": user_id,
            "created_at": time.time()
        }
        _cleanup_expired_sessions()

        return LoginResponse(
            success=True,
            token=token,
            user_id=user_id,
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


async def get_user_id_from_token(
    user_token: str | None = Security(USER_TOKEN_HEADER),
) -> str:
    """
    Extract user_id from the X-User-Token header.

    Returns:
        The user_id associated with the token

    Raises:
        HTTPException: If token is missing or invalid
    """
    _cleanup_expired_sessions()

    if user_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user token. Include X-User-Token header.",
        )

    session = _sessions.get(user_token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired user token. Please login again.",
        )

    return session["user_id"]
