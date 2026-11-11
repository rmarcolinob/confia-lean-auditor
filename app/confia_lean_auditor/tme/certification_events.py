"""Versioned, text-free event projection. Existing IDs are retained, not copied.

Derived stage observations have audit-record timestamp granularity. Per-checker
start times and rejected extraction candidates are not present in stable output.
"""
from datetime import datetime
from typing import Optional
from pydantic import Field
from confia_lean_auditor.submissions.schemas import SubmissionModel


class CertificationEvent(SubmissionModel):
    schema_version: str = 'certification-event.v1'
    event_id: str
    event_type: str
    timestamp: datetime
    assessment_id: str
    participant_id: Optional[str] = None
    submission_id: Optional[str] = None
    question_attempt_id: Optional[str] = None
    transcription_version_id: Optional[str] = None
    audit_run_id: Optional[str] = None
    human_decision_id: Optional[str] = None
    final_correction_id: Optional[str] = None
    engine_mode: Optional[str] = None
    engine_version: Optional[str] = None
    problem_id: Optional[str] = None
    rubric_item_id: Optional[str] = None
    checker_type: Optional[str] = None
    checker_status: Optional[str] = None
    correlation_id: str
    source_event_type: Optional[str] = None
    timestamp_basis: str = 'persisted_operation'
    aliases: list[str] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)


# No transcription text, feedback, free-form adjustment reason, scorer name,
# raw exception, local filesystem path or unrestricted metadata enters exports.
SAFE_PAYLOAD = {'status','suggested_points','suggested_score','final_score','adjustment_delta',
    'old_score','new_score','previous_audit_run_id','new_audit_run_id','new_transcription_version_id',
    'superseded_by','suggested_total','final_total','total_adjustment','question_count',
    'adjusted_question_count','review_question_count','human_decision_ids','engines','checker_id'}


def normalize(event, context, *, timestamp=None, basis='persisted_operation'):
    fields = {k:v for k,v in context.items() if k in CertificationEvent.model_fields}
    fields.update({k:v for k,v in event.items() if k in CertificationEvent.model_fields and k not in {'payload','schema_version'}})
    fields['timestamp'] = event.get('timestamp') or event.get('created_at') or timestamp
    fields['correlation_id'] = fields.get('audit_run_id') or fields.get('final_correction_id') or fields.get('submission_id') or fields['assessment_id']
    fields['timestamp_basis'] = basis
    fields['payload'] = {k:v for k,v in event.items() if k in SAFE_PAYLOAD}
    if fields['event_type'] == 'checker_result_recorded':
        fields['source_event_type'] = 'checker_result_recorded'
        fields['checker_status'] = event.get('status')
        fields['event_type'] = 'checker_failed' if event.get('status') == 'technical_error' else 'checker_completed'
    if fields['event_type'] == 'rubric_item_decided': fields['aliases'] = ['award_decided']
    return CertificationEvent.model_validate(fields).model_dump(mode='json')


def run_observations(raw, audit):
    context = {k:audit.get(k) for k in ('assessment_id','participant_id','submission_id','question_attempt_id',
        'transcription_version_id','audit_run_id','engine_mode','engine_version','problem_id')}
    timestamp = raw.completed_at or raw.created_at
    events = [normalize(e,context,timestamp=timestamp,basis='audit_record') for e in audit['events']]
    def add(kind,suffix='',payload=None,**extra):
        event = dict(event_id=f'{raw.audit_run_id}:{kind}:{suffix}',event_type=kind,**extra)
        result=normalize(event,context,timestamp=timestamp,basis='audit_record')
        result['payload']=payload or {};events.append(result)
    if not raw.result:return events
    result = raw.result.model_dump(mode='json')
    auditor = result.get('bridge',{}).get('auditor',{})
    for claim in auditor.get('records',[]):
        add('claim_extracted',claim['record_id'],payload=dict(claim_id=claim['record_id'],claim_type=claim['claim_type'],
            grounding_status=claim['source']['grounding_status'],source_sha256=claim['source'].get('source_sha256'),
            source_start=claim['source'].get('source_start'),source_end=claim['source'].get('source_end')))
    for fact in auditor.get('facts',[]):
        for cid in fact['source_claim_ids']:
            add('claim_mapped',f'{cid}:{fact["fact_id"]}',payload=dict(claim_id=cid,fact_id=fact['fact_id'],
                verification_id=fact['verification']['verification_id']))
    seen=set()
    def obligations(item):
        for o in item.get('obligations',[]):
            oid=o['obligation_id']
            if oid in seen:continue
            seen.add(oid)
            if o.get('source_claim_ids') or o.get('evidence_refs'):
                add('obligation_mapped',oid,rubric_item_id=item['item_id'],payload=dict(obligation_id=oid,
                    source_claim_ids=o.get('source_claim_ids',[]),effective_status=o['effective_status'],
                    verification_source=o.get('verification_source')))
        for child in item.get('children',[]):obligations(child)
    for item in result.get('assessment',{}).get('items',[]):obligations(item)
    if audit['suggested_score'] is not None:
        add('suggested_score_created',payload=dict(suggested_score=str(audit['suggested_score']),result_sha256=raw.result_sha256))
    return events


def coverage():
    return dict(schema_version='certification-event-coverage.v1',
        unavailable={'checker_started':'No per-checker start timestamp is persisted by the stable engine.',
            'claim_rejected':'Rejected extraction candidates are not durably recorded; refuted claims are not rejected extraction.'},
        aliases={'award_decided':'rubric_item_decided (same observation, not a second event)'},
        timestamp_policy='Stage observations use audit record time; not timing traces or measured latencies.')
