"""Identity for TME only; never supplies a platform AuthUser or school role."""
import os
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request

from confia_lean_auditor.auth.dependencies import optional_user
from confia_lean_auditor.auth.models import Role

DEMO_EVALUATOR_ID = "tme-demo-evaluator"


def demo_no_auth_enabled() -> bool:
    value = os.environ.get("CONFIA_TME_DEMO_NO_AUTH", "0").strip().lower()
    if value not in {"0", "1", "false", "true"}:
        raise RuntimeError("invalid CONFIA_TME_DEMO_NO_AUTH: use 0/false or 1/true")
    enabled = value in {"1", "true"}
    if enabled and os.environ.get("CONFIA_ENV", "development").strip().lower() == "production":
        raise RuntimeError("CONFIA_TME_DEMO_NO_AUTH is only for local pilot/demo; forbidden in production")
    return enabled


@dataclass(frozen=True)
class TMEEvaluator:
    evaluator_id: str
    tenant_id: Optional[str] = None

    @property
    def user_id(self) -> str:
        # Artifact stores use this field for provenance, not authentication.
        return self.evaluator_id


def require_tme_evaluator(request: Request) -> TMEEvaluator:
    demo = demo_no_auth_enabled()
    user = optional_user(request)
    if user is not None:
        if user.role != Role.TEACHER:
            raise HTTPException(403, "Acesso ao piloto não autorizado.")
        return TMEEvaluator(user.user_id, user.tenant_id)
    if demo:
        return TMEEvaluator(DEMO_EVALUATOR_ID)
    raise HTTPException(401, "Autenticação necessária.")
