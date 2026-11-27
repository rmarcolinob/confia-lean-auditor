"""Institutional actor checks shared by capture and the school gateway."""
from fastapi import HTTPException
from .school_contracts import SchoolAttemptBinding
from confia_lean_auditor.submissions.integrity import canonical_sha256


def teacher_for(document):
    from confia_lean_auditor.auth.dependencies import auth_store
    from confia_lean_auditor.auth.models import Role
    from confia_lean_auditor.assessments.router import _teacher_classroom
    a=document.assessment
    user=auth_store().get_user(a.teacher_user_id)
    if not user or not user.active or user.role != Role.TEACHER:
        raise HTTPException(403,'Professor responsável indisponível.')
    _teacher_classroom(user,a.school_id,a.classroom_id)
    return user


def validate_manifest(submission,document,participant):
    binding=submission.school_attempt
    if binding is None:
        if document.assessment.scope == 'INSTITUTIONAL':
            raise ValueError('institutional exam requires student binding')
        return
    a=document.assessment
    if (a.scope!='INSTITUTIONAL' or a.correction_mode!='DYNAMIC' or not a.school_policy
        or binding.teacher_user_id!=a.teacher_user_id or submission.created_by_user_id!=a.teacher_user_id
        or participant.participant_kind!='REGISTERED_USER' or participant.user_id!=binding.student_user_id
        or binding.policy_sha256!=canonical_sha256(a.school_policy.model_dump(mode='json'))):
        raise ValueError('invalid school attempt binding')
    teacher_for(document)


def exam_context(case):
    if not case.exam_submission_id:return None
    from types import SimpleNamespace
    from confia_lean_auditor.tme.exam_store import exam_store
    submission,doc,participant=exam_store()._manifest(case.exam_submission_id,SimpleNamespace(user_id=case.created_by_user_id))
    if not submission.school_attempt:return None
    return submission,doc,participant


def source_binding(case):
    context=exam_context(case)
    if not context:return {}
    submission,doc,_=context;a=doc.assessment
    return dict(submitted_by_user_id=submission.school_attempt.student_user_id,
        network_id=a.network_id,school_id=a.school_id,classroom_id=a.classroom_id,
        assessment_id=a.assessment_id,assessment_item_id=case.assessment_item_id,
        assessment_definition_sha256=a.definition_sha256)


def valid_source_author(case, record):
    binding=source_binding(case)
    if binding:return all(getattr(record,key,None)==value for key,value in binding.items())
    return record.submitted_by_user_id==case.created_by_user_id


def sent_source(record):
    """Capture alone is not an institutional submission."""
    if not record.tme_case_id:return False
    from confia_lean_auditor.tme.store import case_store
    from confia_lean_auditor.tme.exam_store import exam_store,read_sealed
    case=case_store().read(record.tme_case_id)
    context=exam_context(case)
    if not context:return False
    path=exam_store().folder(case.exam_submission_id)/'school_submission.json'
    if not path.exists():return False
    sent=read_sealed(path)
    return (sent['submitted_by']==record.submitted_by_user_id
        and sent['assessment_definition_sha256']==record.assessment_definition_sha256
        and any(s['case_id']==case.case_id for s in sent['selected']))
