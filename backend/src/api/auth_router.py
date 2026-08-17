"""Auth endpoints: pick-a-user login (BR1), logout, current-user lookup."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from auth import SESSION_COOKIE_NAME, AuthService, UserNotFoundError, session_cookie_is_secure

from .deps import AuthContext, get_auth_context, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str


@router.get("/users")
async def list_demo_users(auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.list_demo_users()


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        session = await auth_service.login(body.username)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="Unknown user")

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(session.id),
        httponly=True,
        samesite="lax",
        secure=session_cookie_is_secure(),
    )
    user = await auth_service.validate_session(session.id)
    return user


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    raw_session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if raw_session_id is not None:
        try:
            await auth_service.logout(UUID(raw_session_id))
        except ValueError:
            pass  # malformed cookie value - nothing to delete server-side
    response.delete_cookie(SESSION_COOKIE_NAME, httponly=True, samesite="lax", secure=session_cookie_is_secure())
    return {"status": "logged out"}


@router.get("/me")
async def get_me(auth: AuthContext = Depends(get_auth_context)):
    return auth.user
