"""Acesso por perfil SEM SENHA somente para demonstração local na porta 8888.

Não desabilita autenticação ou controle de permissões. Apenas emite sessões
para usuários SINTÉTICOS já existentes. Em produção, ou com LLM ligado,
este recurso fica completamente indisponível.
"""
import os
from typing import Literal
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from .dependencies import COOKIE_NAME, auth_enabled, auth_store, same_origin
from .models import StoredUser
from .store import SESSION_SECONDS

router = APIRouter(prefix="/auth/local-demo", tags=["demo local"])

PROFILE_ROLES = {
    "student": ("STUDENT",),
    "teacher": ("TEACHER",),
    "management": ("SCHOOL_MANAGER", "NETWORK_MANAGER"),
}
PREFERRED = {
    "student": "student.a",
    "teacher": "teacher.a",
    "management": "manager.a",
}


def enabled(request: Request) -> bool:
    if os.getenv("CONFIA_DEMO_PASSWORDLESS") != "1":
        return False
    if os.getenv("CONFIA_ENV", "development").lower() not in ("test", "development"):
        return False
    if not auth_enabled():
        return False
    if any(os.getenv(name, "0").lower() not in ("0", "false", "") for name in (
        "CONFIA_DYNAMIC_LLM_ENABLED", "CONFIA_SEMANTIC_LLM_ENABLED",
        "CONFIA_DYNAMIC_REVIEWER_ENABLED"
    )):
        return False
    if request.client is None or request.client.host not in ("127.0.0.1", "::1"):
        return False
    return (request.url.hostname in ("127.0.0.1", "localhost")
            and request.url.port == 8888)


def _choose(profile: str):
    if profile not in PROFILE_ROLES:
        raise HTTPException(422, "Perfil de demonstração inválido.")
    store = auth_store()
    with store._locked():
        raw = store._read("users.json")
    candidates = [
        (login, StoredUser.model_validate(value))
        for login, value in raw.items()
        if value.get("active", True) and value.get("role") in PROFILE_ROLES[profile]
    ]
    if not candidates:
        raise HTTPException(503, "Conta sintética deste perfil não encontrada.")
    preferred = [item for item in candidates if item[0] == PREFERRED[profile]]
    if preferred:
        selected = preferred[0][1]
    elif len(candidates) == 1:
        selected = candidates[0][1]
    else:
        raise HTTPException(409, "Há várias contas para o perfil. Especifique a identidade sintética antes de habilitar a demonstração.")
    return selected.public()


def issue_session(profile: str):
    user = _choose(profile)
    token = auth_store().create_session(user.user_id)
    return user, token


class Switch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: Literal["student", "teacher", "management"]


@router.post("/switch")
def switch(request: Request, body: Switch):
    if not enabled(request):
        raise HTTPException(404, "Não disponível.")
    if not same_origin(request):
        raise HTTPException(403, "Origem não autorizada.")
    user, token = issue_session(body.profile)
    response = JSONResponse({"profile": body.profile, "role": user.role.value})
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS,
                        path="/", httponly=True, secure=False, samesite="lax")
    response.headers["Cache-Control"] = "no-store"
    return response
