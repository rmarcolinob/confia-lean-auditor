"""Session endpoints with generic credential errors and no secret serialization."""
from __future__ import annotations
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import ValidationError

from .dependencies import COOKIE_NAME, auth_enabled, auth_store, current_user
from .models import AuthUser, LoginRequest
from .store import SESSION_SECONDS

router = APIRouter(prefix="/auth", tags=["local authentication"])


def cookie_secure() -> bool:
    value = os.environ.get("CONFIA_COOKIE_SECURE", "1").lower()
    if value not in {"0", "1", "false", "true"}:
        raise RuntimeError("invalid CONFIA_COOKIE_SECURE")
    secure = value in {"1", "true"}
    if not secure and os.environ.get("CONFIA_ENV", "development").lower() == "production":
        raise RuntimeError("insecure cookie in production")
    return secure


@router.post("/login", response_model=AuthUser)
async def login(request: Request, response: Response):
    if not auth_enabled():
        raise HTTPException(404)
    secure = cookie_secure()
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 4096:
            raise HTTPException(401, "Credenciais inválidas.")
    try:
        credentials = LoginRequest.model_validate_json(bytes(raw))
    except (ValidationError, ValueError):
        raise HTTPException(401, "Credenciais inválidas.") from None
    user = auth_store().authenticate(credentials.login, credentials.password)
    if user is None:
        raise HTTPException(401, "Credenciais inválidas.")
    token = auth_store().create_session(user.user_id)
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, path="/",
                        httponly=True, secure=secure, samesite="lax")
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, _user: Optional[AuthUser] = Depends(current_user)):
    secure = cookie_secure()
    auth_store().revoke_session(request.cookies.get(COOKIE_NAME))
    response.delete_cookie(COOKIE_NAME, path="/", secure=secure, samesite="lax", httponly=True)
    response.headers["Cache-Control"] = "no-store"


@router.get("/me", response_model=AuthUser)
def me(response: Response, user: Optional[AuthUser] = Depends(current_user)):
    if user is None:
        raise HTTPException(404)
    response.headers["Cache-Control"] = "no-store"
    return user
