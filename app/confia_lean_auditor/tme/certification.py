"""Read-only certification projection over immutable D1–D6 artifacts.

Lock order is exam -> submissions. Gold is an independent assessment snapshot.
The cohort contains current closures, or latest current-reading run per engine.
"""
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import csv
import io
import subprocess
from typing import Optional
from pydantic import Field
from fastapi import HTTPException
from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.submissions.schemas import SubmissionModel
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.submissions.router import store as submission_store
from confia_lean_auditor.submission_audits.router import service as audit_service
from confia_lean_auditor.submission_audits.schemas import AuditRunView
from confia_lean_auditor.assessments.store import definition_hash
from .exam_store import exam_store, read_sealed, ExamConflict
from .exam_models import PageMapping
from . import certification_gold as gold
from .certification_events import normalize, run_observations, coverage
from .certification_metrics import metrics
from .correction_engine import project_audit
from .finalization import _summary
from .human_decisions import project as project_human


class CertificationRecord(SubmissionModel):
    schema_version: str = 'certification-record.v1'
    assessment_id: str
    participant_id: str
    participant_code: str
    submission_id: str
    source_submission_id: Optional[str] = None
    question_id: str
    question_attempt_id: str
    problem_id: str
    transcription_version: Optional[str] = None
    audit_run_id: Optional[str] = None
    source_sha256: Optional[str] = None
    result_sha256: Optional[str] = None
    human_decision_id: Optional[str] = None
    final_correction_id: Optional[str] = None
    gold_record_id: Optional[str] = None
    gold_version: Optional[int] = None
    gold_source_id: Optional[str] = None
    gold_dataset_version: Optional[str] = None
    gold_sha256: Optional[str] = None
    engine_mode: Optional[str] = None
    engine_version: Optional[str] = None
    suggested_score: Optional[str] = None
    human_decision_score: Optional[str] = None
    human_gold_score: Optional[str] = None
    max_score: str
    adjustment: Optional[str] = None
    absolute_error_vs_gold: Optional[str] = None
    signed_error_vs_gold: Optional[str] = None
    review_required: bool = False
    technical_uncertainty: bool = False
    checker_counts: dict = Field(default_factory=dict)
    rubric_decisions: list[dict] = Field(default_factory=list)
    rubric_gold: list[dict] = Field(default_factory=list)
    timestamps: dict = Field(default_factory=dict)


def details(aid,user):
    for path in sorted(exam_store().root.glob('exam_*')):
        try: detail=exam_store()._detail(path.name,user)
        except HTTPException as exc:
            if exc.status_code==403:continue
            raise
        if detail.submission.assessment_id==aid:yield detail


def rubric_catalog(aid,item_id,user):
    # Caller holds exam lock, public audit list acquires only submissions lock.
    catalog={}
    for detail in details(aid,user):
        for case in detail.question_attempts:
            if case.assessment_item_id!=item_id or not case.submission_id:continue
            for run in audit_service().list(case.submission_id):
                for item in project_audit(run,case,detail)['rubric_items']:
                    key=item['rubric_item_id'];maximum=item['max_points']
                    if key in catalog and catalog[key]!=maximum:raise ValueError('ambiguous rubric maximum')
                    catalog[key]=maximum
    return catalog


def gold_metadata(value):
    if not value:return None
    return {**{k:value[k] for k in ('version','source_id','dataset_version','assessment_id','evaluation_mode',
        'imported_at','previous_sha256','request_sha256','records_sha256')},'sha256':canonical_sha256(value),'record_count':len(value['records'])}


def get_gold(aid,user,version=None):
    gold.owned_assessment(aid,user)
    with exam_store()._locked():
        value,versions=gold.selected_gold(aid,version)
        return dict(current=gold_metadata(value),history=[gold_metadata(v) for v in versions],
            records=[{k:v for k,v in r.items() if k!='scorer_reference'} for r in value['records']] if value else [])


def capture_events(detail):
    s=detail.submission
    context=dict(assessment_id=s.assessment_id,participant_id=s.participant_id,submission_id=s.submission_id)
    def event(kind,key,at,**extra):
        return normalize(dict(event_id=f'{s.submission_id}:{kind}:{key}',event_type=kind,**extra),context,timestamp=at,basis='capture_or_mapping_record')
    events=[event('capture_received','',s.created_at)]
    for page in s.pages:
        row=event('page_created',page.exam_page_id,s.created_at);row['payload']={'page_id':page.exam_page_id};events.append(row)
    previous=set()
    for path in sorted(exam_store().folder(s.submission_id).glob('mapping_*.json')):
        mapping=PageMapping.model_validate(read_sealed(path))
        if path.name!=f'mapping_{mapping.version:06d}.json':raise ExamConflict('invalid mapping history')
        current={(b.question_attempt_id,b.exam_page_id,b.order) for b in mapping.bindings}
        for kind,changes in [('page_question_associated',current-previous),('page_question_disassociated',previous-current)]:
            for qid,pid,order in sorted(changes):
                row=event(kind,f'{mapping.version}:{qid}:{pid}:{order}',mapping.updated_at,question_attempt_id=qid)
                row['payload']=dict(page_id=pid,order=order,mapping_version=mapping.version);events.append(row)
        previous=current
    return events


def build(aid,user,selection='finalized',engine_mode=None,gold_version=None):
    doc=gold.owned_assessment(aid,user)
    if selection not in {'finalized','current'}:raise ValueError('invalid selection')
    rows=[];events=[];audits_history=[];questions_history=[];finals=[]
    subs=submission_store();audits=audit_service()
    with exam_store()._locked(), subs._locked(exclusive=True):
        selected,versions=gold.selected_gold(aid,gold_version)
        gold_index={(r['participant_id'],r['assessment_item_id']):r for r in selected['records']} if selected else {}
        all_runs=sorted((audits._read(p.stem) for p in audits.root.glob('aud_*.json')),key=lambda r:(r.created_at,r.audit_run_id),reverse=True)
        for detail in details(aid,user):
            summary=_summary(detail,subs,audits) # validates frozen sources and current closure
            final=summary['current_final_correction']
            if selection=='finalized' and not final:continue
            context=dict(assessment_id=aid,participant_id=detail.submission.participant_id,submission_id=detail.submission.submission_id)
            exam_events=capture_events(detail)
            exam_events.extend(normalize(e,context) for e in summary['events'])
            included=False
            for case in detail.question_attempts:
                histories=[]
                if case.submission_id:
                    folder=subs._transcriptions_folder(case.submission_id)
                    if folder:
                        histories=sorted((subs._history_from_folder(p) for p in folder.iterdir() if p.is_dir() and not p.is_symlink() and subs._transcription_name_valid(p.name)),key=lambda h:h.transcription.created_at,reverse=True)
                current=f'{histories[0].transcription.transcription_id}:{histories[0].revisions[-1].revision_number}' if histories else None
                revisions=[r for h in histories for r in h.revisions]
                version_rows=[dict(version_id=f'{r.transcription_id}:{r.revision_number}',created_at=r.created_at,current=f'{r.transcription_id}:{r.revision_number}'==current) for r in revisions]
                runs=[AuditRunView(**r.model_dump(),stale=f'{r.transcription_id}:{r.revision_number}'!=current) for r in all_runs if case.submission_id and r.submission_id==case.submission_id]
                human=project_human(case,runs,version_rows)
                contracts={r.audit_run_id:project_audit(r,case,detail) for r in runs}
                frozen=next((q for q in final['questions'] if q['question_attempt_id']==case.case_id),None) if final else None
                if selection=='finalized':chosen=[r for r in runs if r.audit_run_id==frozen['audit_run_id']]
                else:
                    chosen=[];modes=set()
                    for run in runs:
                        mode=contracts[run.audit_run_id]['engine_mode']
                        if not run.stale and mode not in modes:chosen.append(run);modes.add(mode)
                chosen=[r for r in chosen if not engine_mode or contracts[r.audit_run_id]['engine_mode']==engine_mode]
                if not chosen and engine_mode:continue
                included=True
                questions_history.append(dict(question_attempt_id=case.case_id,transcription_version_count=len(revisions),human_corrected=any(r.revision_number>1 for r in revisions)))
                qcontext=dict(**context,question_attempt_id=case.case_id,problem_id=case.problem_id)
                for r in revisions:
                    vid=f'{r.transcription_id}:{r.revision_number}'
                    for kind in (['transcription_created'] if r.revision_number==1 else ['transcription_human_corrected'])+['transcription_activated']:
                        events.append(normalize(dict(event_id=f'{vid}:{kind}',event_type=kind,transcription_version_id=vid),qcontext,timestamp=r.created_at))
                events.extend(normalize(e,qcontext) for e in human['human_decision_events'] if not engine_mode or e.get('engine_mode')==engine_mode)
                for run in runs:
                    audit=contracts[run.audit_run_id]
                    if engine_mode and audit['engine_mode']!=engine_mode:continue
                    # A stale historical run was not under review merely because of a later reading.
                    observed=project_audit(AuditRunView(**{k:v for k,v in run.model_dump().items() if k!='stale'},stale=False),case,detail)
                    audits_history.append(dict(audit_run_id=run.audit_run_id,question_attempt_id=case.case_id,engine_mode=audit['engine_mode'],
                        engine_version=audit['engine_version'],transcription_version_id=audit['transcription_version_id'],created_at=run.created_at.isoformat(),
                        status=run.status,review_required=observed['review_required'],technical_uncertainty=observed['technical_uncertainty'],
                        suggested_score=str(audit['suggested_score']) if audit['suggested_score'] is not None else None,human_corrected_reading=run.revision_number>1))
                    events.extend(run_observations(run,audit))
                g=gold_index.get((detail.submission.participant_id,case.assessment_item_id))
                for run in chosen or [None]:
                    audit=contracts[run.audit_run_id] if run else None
                    d=(frozen['human_decision'] if selection=='finalized' else human['current_human_decision'])
                    if d and (not run or d['audit_run_id']!=run.audit_run_id):d=None
                    score=str(audit['suggested_score']) if audit and audit['suggested_score'] is not None else None
                    error=Decimal(score)-Decimal(g['gold_score']) if score is not None and g else None
                    record=CertificationRecord(**context,participant_code=detail.participant.external_code,source_submission_id=case.submission_id,
                        question_id=case.assessment_item_id,question_attempt_id=case.case_id,problem_id=case.problem_id,max_score=str(case.max_score),
                        transcription_version=audit['transcription_version_id'] if audit else current,
                        audit_run_id=run.audit_run_id if run else None,source_sha256=run.source_hash if run else None,
                        result_sha256=run.result_sha256 if run else None,engine_mode=audit['engine_mode'] if audit else None,engine_version=audit['engine_version'] if audit else None,
                        suggested_score=score,human_decision_score=d['final_points'] if d else None,adjustment=d['adjustment_delta'] if d else None,
                        human_decision_id=d['human_decision_id'] if d else None,final_correction_id=final['final_correction_id'] if final else None,
                        human_gold_score=g['gold_score'] if g else None,gold_record_id=g['gold_record_id'] if g else None,
                        gold_version=selected['version'] if g else None,gold_source_id=selected['source_id'] if g else None,
                        gold_dataset_version=selected['dataset_version'] if g else None,gold_sha256=canonical_sha256(selected) if g else None,
                        absolute_error_vs_gold=str(abs(error)) if error is not None else None,signed_error_vs_gold=str(error) if error is not None else None,
                        review_required=audit['review_required'] if audit else False,technical_uncertainty=audit['technical_uncertainty'] if audit else False,
                        checker_counts=dict(Counter(c['status'] for c in audit['checker_summary'])) if audit else {},
                        rubric_decisions=[{k:i[k] for k in ('rubric_item_id','max_points','suggested_points','status')} for i in audit['rubric_items']] if audit else [],
                        rubric_gold=g['rubric_gold'] if g else [],timestamps=dict(captured_at=detail.submission.created_at.isoformat(),
                            audit_started_at=audit['started_at'] if audit else None,audit_completed_at=audit['completed_at'] if audit else None,
                            human_decided_at=d['decided_at'] if d else None,finalized_at=final['finalized_at'] if final else None))
                    rows.append(record.model_dump(mode='json'))
            if included:
                events.extend(exam_events)
                finals.extend({k:f[k] for k in ('final_correction_id','submission_id','version','previous_final_correction_id','snapshot_sha256','finalized_at')} for f in summary['final_corrections'])
        unique={}
        for event in events:
            if event['event_id'] in unique and unique[event['event_id']]!=event:raise ExamConflict('conflicting event identity')
            unique[event['event_id']]=event
        events=sorted(unique.values(),key=lambda e:(e['timestamp'],e['event_id']))
        counts=dict(proofs=len({r['submission_id'] for r in rows}),questions=len({r['question_attempt_id'] for r in rows}),records=len(rows),
            gold_available=sum(r['human_gold_score'] is not None for r in rows),events=len(events),audit_runs=len(audits_history))
        manifest=dict(schema_version='certification-export.v1',evaluation_mode='SHADOW_EVALUATION',official_correction_affected=False,
            assessment_id=aid,assessment_definition_sha256=definition_hash(doc),exported_at=datetime.now(timezone.utc).isoformat(),
            filters=dict(selection=selection,engine_mode=engine_mode,gold_version=gold_version),counts=counts,
            engine_versions=[dict(engine_mode=m,engine_version=v) for m,v in sorted({(r['engine_mode'],r['engine_version']) for r in rows if r['engine_mode']})],
            gold=gold_metadata(selected),records_sha256=canonical_sha256(rows),events_sha256=canonical_sha256(events),**code_version())
        return dict(manifest=manifest,records=rows,events=events,event_coverage=coverage(),gold_history=[gold_metadata(v) for v in versions],
            metrics=metrics(rows,audits_history,questions_history),audit_history=audits_history,question_history=questions_history,finalization_history=finals)


def code_version():
    try:
        root=get_repo_root()
        sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
        dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True))
    except (OSError,subprocess.CalledProcessError):sha=None;dirty=None
    # Includes untracked implementation modules, unlike git diff alone.
    import hashlib
    digest=hashlib.sha256()
    for p in sorted((get_repo_root()/'app').rglob('*')):
        if p.is_file() and p.suffix in {'.py','.js','.html','.css'} and not p.is_symlink():
            digest.update(str(p.relative_to(get_repo_root())).encode());digest.update(p.read_bytes())
    return dict(git_sha=sha,git_dirty=dirty,application_sha256=digest.hexdigest())


CSV_FIELDS=['participant_code','assessment_id','submission_id','source_submission_id','question_id','question_attempt_id',
    'suggested_score','human_decision_score','human_gold_score','max_score','adjustment','absolute_error_vs_gold','signed_error_vs_gold',
    'review_required','technical_uncertainty','engine_mode','engine_version','transcription_version','audit_run_id','human_decision_id',
    'final_correction_id','gold_record_id','gold_version','gold_source_id','gold_dataset_version','gold_sha256','source_sha256','result_sha256']
NUMERIC={'suggested_score','human_decision_score','human_gold_score','max_score','adjustment','absolute_error_vs_gold','signed_error_vs_gold','gold_version'}


def export_csv(data):
    metadata=['evaluation_mode','official_correction_affected','git_sha','git_dirty','application_sha256','exported_at','assessment_definition_sha256','records_sha256']
    output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=CSV_FIELDS+metadata+['selection','engine_filter','selected_gold_version','proof_count','question_count','record_count'])
    writer.writeheader()
    for record in data['records']:
        row={k:record[k] for k in CSV_FIELDS};m=data['manifest']
        row.update({k:m[k] for k in metadata});row.update(selection=m['filters']['selection'],engine_filter=m['filters']['engine_mode'],
            selected_gold_version=m['gold']['version'] if m['gold'] else None,proof_count=m['counts']['proofs'],question_count=m['counts']['questions'],record_count=m['counts']['records'])
        for key,value in row.items():
            if key not in NUMERIC and isinstance(value,str) and value.startswith(('=','+','-','@','\t','\r','\n')):row[key]="'"+value
        writer.writerow(row)
    return output.getvalue()
