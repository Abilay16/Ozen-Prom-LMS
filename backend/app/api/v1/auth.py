from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DB
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import UnauthorizedError
from app.models.user import User, AdminUser

router = APIRouter()


class LoginRequest(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    full_name: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DB):
    """Login for both admin and learner. Returns role in response."""
    # Try admin first
    result = await db.execute(select(AdminUser).where(AdminUser.login == body.login))
    admin = result.scalar_one_or_none()
    if admin and admin.is_active and verify_password(body.password, admin.password_hash):
        admin.last_login = datetime.now(timezone.utc)
        access = create_access_token(str(admin.id), {"role": "admin"})
        refresh = create_refresh_token(str(admin.id))
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            role="admin",
            user_id=str(admin.id),
            full_name=admin.full_name,
        )

    # Try learner
    result = await db.execute(select(User).where(User.login == body.login))
    user = result.scalar_one_or_none()
    if user and user.is_active and verify_password(body.password, user.password_hash):
        user.last_login = datetime.now(timezone.utc)
        access = create_access_token(str(user.id), {"role": "learner"})
        refresh = create_refresh_token(str(user.id))
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            role="learner",
            user_id=str(user.id),
            full_name=user.full_name,
        )

    raise UnauthorizedError("Invalid login or password")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: DB):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    user_id = payload.get("sub")

    # Check admin
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    admin = result.scalar_one_or_none()
    if admin and admin.is_active:
        access = create_access_token(str(admin.id), {"role": "admin"})
        refresh = create_refresh_token(str(admin.id))
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            role="admin",
            user_id=str(admin.id),
            full_name=admin.full_name,
        )

    # Check learner
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user and user.is_active:
        access = create_access_token(str(user.id), {"role": "learner"})
        refresh = create_refresh_token(str(user.id))
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            role="learner",
            user_id=str(user.id),
            full_name=user.full_name,
        )

    raise UnauthorizedError("User not found or inactive")


@router.post("/logout")
async def logout():
    """Client should discard tokens. Stateless JWT."""
    return {"message": "Logged out successfully"}
