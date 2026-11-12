"""Server-owned mode routing and exact approved context. No UI-supplied engine."""

import os
from .models import Actor, model_sha256
from .grading_models import DynamicGradingContext
from .store import dynamic_store, DynamicConflict


def evaluator_actor(user):
    from confia_lean_auditor.tme.auth import DEMO_EVALUATOR_ID, demo_no_auth_enabled

    if user.user_id == DEMO_EVALUATOR_ID:
        from confia_lean_auditor.auth.dependencies import auth_enabled

        if (
            auth_enabled()
            or not demo_no_auth_enabled()
            or os.getenv("CONFIA_DYNAMIC_DEMO_ENABLED") != "1"
        ):
            raise DynamicConflict("Demonstração Dynamic não autorizada.")
        return Actor(actor_id="technical-demo:dynamic", kind="TECHNICAL_DEMO")
    return Actor(actor_id=user.user_id, kind="TEACHER", tenant_id=user.tenant_id)


def resolve(problem_id, actor, allow_review=False, expected=None):
    store = dynamic_store()
    with store._locked():
        doc, _ = store._owned(problem_id, actor)
        package = next(
            (p for p in doc.packages if p.package_id == doc.current_package_id), None
        )
        if not package or not any(
            a.package_id == package.package_id for a in doc.approvals
        ):
            raise DynamicConflict("Aprove uma rubrica antes da correção.")
        statement = doc.statements[-1]
        rubric = next(r for r in doc.rubrics if r.rubric_id == package.rubric_id)
        # A new draft is not silently substituted for the approved version.
        if doc.rubrics[-1].rubric_id != rubric.rubric_id:
            raise DynamicConflict(
                "Há rubrica em rascunho; revise e aprove antes da correção."
            )
        prep = store.latest_preparation(doc)
        ref = package.preparation_reference
        if (
            not prep
            or not ref
            or prep.preparation_id != ref.preparation_id
            or prep.status not in {"READY_FOR_REVIEW", "REVIEW_REQUIRED"}
        ):
            raise DynamicConflict(
                "A preparação vigente deve corresponder à configuração aprovada."
            )
        if (
            package.statement_sha256 != model_sha256(statement)
            or prep.statement_sha256 != package.statement_sha256
            or model_sha256(prep) != ref.preparation_sha256
        ):
            raise DynamicConflict("Versões de enunciado/preparação incompatíveis.")
        if prep.status == "REVIEW_REQUIRED" and not allow_review:
            raise DynamicConflict(
                "Autorize explicitamente a correção provisória com preparação que exige revisão."
            )
        context = DynamicGradingContext(
            problem_id=problem_id,
            package_id=package.package_id,
            package_version=package.package_version,
            package_sha256=model_sha256(package),
            statement_version=statement.version_number,
            statement_sha256=package.statement_sha256,
            preparation_id=prep.preparation_id,
            preparation_version=prep.preparation_version,
            preparation_sha256=ref.preparation_sha256,
            rubric_id=rubric.rubric_id,
            rubric_version=rubric.version_number,
            rubric_sha256=package.rubric_sha256,
            allow_preparation_review=allow_review,
        )
        if expected is not None and context != expected:
            raise DynamicConflict(
                "A configuração mudou; crie uma tentativa vinculada à nova aprovação."
            )
        return context, statement, rubric, prep


def resolve_pinned(problem_id, actor, expected):
    """Published Assessment selects immutable history, never the mutable current pointer."""
    store = dynamic_store()
    with store._locked():
        doc, _ = store._owned(problem_id, actor)
        package = next((p for p in doc.packages if p.package_id == expected.package_id), None)
        statement = next((s for s in doc.statements if s.version_number == expected.statement_version), None)
        rubric = next((r for r in doc.rubrics if r.rubric_id == expected.rubric_id), None)
        preparation = next((p for p in reversed(doc.preparations) if p.preparation_id == expected.preparation_id), None)
        if not all((package, statement, rubric, preparation)) or not any(a.package_id == expected.package_id for a in doc.approvals):
            raise DynamicConflict("Configuração histórica não aprovada.")
        if (model_sha256(package) != expected.package_sha256 or model_sha256(statement) != expected.statement_sha256
                or model_sha256(rubric) != expected.rubric_sha256 or model_sha256(preparation) != expected.preparation_sha256
                or package.rubric_id != rubric.rubric_id or package.statement_version != statement.version_number
                or not package.preparation_reference or package.preparation_reference.preparation_id != preparation.preparation_id):
            raise DynamicConflict("Integridade da configuração histórica inválida.")
        return expected, statement, rubric, preparation


def case_context(case):
    from confia_lean_auditor.tme.auth import TMEEvaluator

    store = dynamic_store()
    # Ownership is captured by the case, not by arbitrary submission metadata.
    with store._locked():
        doc, _ = store._load(case.problem_id)
    owner = doc.problem.created_by
    from confia_lean_auditor.tme.auth import DEMO_EVALUATOR_ID

    if owner.kind == "TECHNICAL_DEMO":
        if case.created_by_user_id != DEMO_EVALUATOR_ID:
            raise DynamicConflict("Titular divergente.")
        actor = evaluator_actor(TMEEvaluator(case.created_by_user_id))
    else:
        actor = Actor(
            actor_id=case.created_by_user_id, kind="TEACHER", tenant_id=owner.tenant_id
        )
    if case.exam_submission_id:
        from .assessment_service import pinned_activity
        pinned_activity(case)
        return resolve_pinned(case.problem_id, actor, case.dynamic_context)
    return resolve(
        case.problem_id,
        actor,
        case.dynamic_context.allow_preparation_review,
        case.dynamic_context,
    )


def audit_dynamic(source, root):
    from .grader import DynamicSolutionGrader
    from confia_lean_auditor.tme.store import case_store
    from confia_lean_auditor.submissions.router import store

    record = store().get_record(source.submission_id)
    case = case_store().read(record.tme_case_id)
    context, statement, rubric, prep = case_context(case)
    if context != source.dynamic_context:
        raise DynamicConflict("Contexto da fonte divergente.")
    return DynamicSolutionGrader().grade(source, statement, rubric, prep, context, root)
