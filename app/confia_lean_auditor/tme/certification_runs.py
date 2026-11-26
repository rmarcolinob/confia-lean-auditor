"""Immutable experiment snapshots inside the existing D7 certification store.

Frozen datasets and runs refer to the shared gold chain. They cannot publish
HumanDecision, FinalCorrection, official scores or a production certification.
"""
import csv
import io
import json
import platform
import os
import hashlib
from importlib.metadata import version, PackageNotFoundError
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from . import certification as cert, certification_gold as gold
from .certification_experiment_metrics import report
from .exam_store import exam_store, sealed, read_sealed, ExamConflict
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.submissions.integrity import canonical_sha256


def now():return datetime.now(timezone.utc).isoformat()


def execution_environment():
    root=cert.get_repo_root()
    dependencies={}
    for package in ('pydantic','sympy','fastapi','openai'):
        try:dependencies[package]=version(package)
        except PackageNotFoundError:dependencies[package]=None
    config={k:os.getenv(k) for k in ('CONFIA_DYNAMIC_MODEL','CONFIA_DYNAMIC_REASONING_EFFORT','CONFIA_DYNAMIC_LLM_ENABLED',
        'CONFIA_DYNAMIC_REVIEWER_MODEL','CONFIA_DYNAMIC_REVIEWER_REASONING_EFFORT','CONFIA_DYNAMIC_REVIEWER_ENABLED')}
    files={name:hashlib.sha256((root/name).read_bytes()).hexdigest() if (root/name).is_file() else None
           for name in ('pyproject.toml','lakefile.toml','lake-manifest.json','lean-toolchain')}
    return dict(python=platform.python_version(),system=platform.system(),machine=platform.machine(),dependencies=dependencies,
                configuration=config,dependency_files_sha256=files,lean_toolchain=(root/'lean-toolchain').read_text().strip())


def path(aid,identity):
    if not re.fullmatch(r'(dataset|run|comparison)_[0-9a-f]{64}',identity):raise ValueError('invalid experiment identifier')
    return gold.folder(aid)/(identity+'.json')


def save(aid,identity,value):
    target=path(aid,identity);target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if target.exists():
        if read_sealed(target)!=value:raise ExamConflict('immutable experiment already exists')
        return value
    SubmissionStore._write_atomic_new(target,json.dumps(sealed(value),ensure_ascii=False,indent=2).encode())
    return value


def read(aid,identity,user):
    gold.owned_assessment(aid,user)
    value=read_sealed(path(aid,identity))
    if value.get('assessment_id')!=aid or value.get('id')!=identity:raise ExamConflict('experiment identity mismatch')
    return value


def freeze(aid,body,user):
    doc=gold.owned_assessment(aid,user)
    if doc.assessment.correction_mode!='DYNAMIC':raise ValueError('Dynamic dataset requires Dynamic assessment')
    if canonical_sha256(body.protocol)!=body.protocol_sha256:raise ValueError('protocol digest mismatch')
    request=body.model_dump(mode='json')
    with exam_store()._locked():
        for p in gold.folder(aid).glob('dataset_*.json'):
            previous=read_sealed(p)
            if previous['request']['dataset_version']==body.dataset_version:
                if previous['request']!=request:raise ExamConflict('dataset version is immutable')
                return previous
    data=cert.build(aid,user,'current',gold_version=body.gold_version)
    if not data['manifest']['gold']:raise ValueError('import independent gold before dataset freeze')
    rows={r['question_attempt_id']:r for r in data['records']}
    selected=[]
    participant_splits={};text_splits={}
    for c in body.cases:
        row=rows.get(c.question_attempt_id)
        if not row or not row['transcription_version']:raise ValueError('unknown attempt or missing transcription')
        if row['dynamic_evaluation']['exclusions']:raise ValueError('dataset requires comparable versioned gold')
        if c.split=='HOLDOUT' and any(r['question_attempt_id']==c.question_attempt_id for r in data['audit_history']):
            raise ValueError('holdout must be frozen before any grading')
        participant=row['participant_id']
        if participant in participant_splits and participant_splits[participant]!=c.split:raise ValueError('participant crosses splits')
        participant_splits[participant]=c.split
        from confia_lean_auditor.submissions.router import store as submissions
        from confia_lean_auditor.submission_audits.source import convert_segments
        tid,rev=row['transcription_version'].split(':')
        history=submissions().transcription_history(tid)
        revision=next(r for r in history.revisions if r.revision_number==int(rev))
        text_hash=canonical_sha256(convert_segments(revision.segments)[0])
        text_key=(row['dynamic_evaluation']['context']['statement_sha256'],text_hash)
        if text_key in text_splits and text_splits[text_key]!=c.split:raise ValueError('identical problem/response crosses splits')
        text_splits[text_key]=c.split
        selected.append(dict(**c.model_dump(mode='json'),participant_id=participant,input_text_sha256=text_hash,transcription_version=row['transcription_version'],
            context=row['dynamic_evaluation']['context'],gold_record_id=row['gold_record_id']))
    request=body.model_dump(mode='json');identity='dataset_'+canonical_sha256([aid,request])
    value=dict(schema_version='certification-dataset.v1',id=identity,assessment_id=aid,request=request,cases=selected,
        gold_sha256=data['manifest']['gold']['sha256'],gold_version=body.gold_version,
        frozen_at=now(),frozen_by=user.user_id,code=cert.code_version(),environment=execution_environment(),evaluation_mode='SHADOW_EVALUATION',official_correction_affected=False)
    with exam_store()._locked():
        for p in gold.folder(aid).glob('dataset_*.json'):
            prior=read_sealed(p)
            if prior['request']['dataset_version']==body.dataset_version:
                if prior['request']!=request:raise ExamConflict('dataset version is immutable')
                return prior
            overlap={c['question_attempt_id'] for c in prior['cases']} & {c.question_attempt_id for c in body.cases}
            if overlap:raise ExamConflict('attempt already registered; new holdout requires new attempts')
            for c in prior['cases']:
                key=(c['context']['statement_sha256'],c.get('input_text_sha256'))
                if key in text_splits and (c['split']=='HOLDOUT' or text_splits[key]=='HOLDOUT'):
                    raise ExamConflict('holdout response already registered in another dataset')
        return save(aid,identity,value)


def gate_verdict(metrics,gates):
    if not gates:
        n=sum(s['metrics']['stages']['G2']['score']['N'] for s in metrics['strata'])
        return dict(status='PILOT_METRICS_AVAILABLE' if n else 'INSUFFICIENT_EVIDENCE',configured=False)
    stratum=next((s for s in metrics['strata'] if all(s[k]==gates[k] for k in ('profile','split','source_kind'))),None)
    if not stratum:return dict(status='INSUFFICIENT_EVIDENCE',configured=True,reason='No matching profile/split/source stratum')
    m=stratum['metrics'];s=m['stages']['G2'];values=dict(max_mae=s['score']['MAE'],max_false_credit_rate=s['criterion']['false_credit_rate'],
        min_review_precision=s['review_precision'],max_technical_failure_rate=m['technical_failure_rate'],max_automation_risk=s['unsafe_automation_rate'])
    checks=[]
    for name,value in values.items():
        limit=gates.get(name)
        if limit is not None:checks.append(dict(metric=name,value=value,threshold=limit,met=None if value is None else Decimal(value)>=Decimal(limit) if name.startswith('min_') else Decimal(value)<=Decimal(limit)))
    enough=s['score']['N']>=gates['min_n'] and checks and all(c['met'] is not None for c in checks)
    status='INSUFFICIENT_EVIDENCE' if not enough else 'GATE_MET_FOR_DEFINED_PROFILE' if all(c['met'] for c in checks) else 'GATE_NOT_MET'
    return dict(status=status,configured=True,label=gates['label'],profile=gates['profile'],split=gates['split'],source_kind=gates['source_kind'],N=s['score']['N'],min_n=gates['min_n'],checks=checks,
        interpretation='Experimental gate only; no institutional threshold or production authorization')


def create(aid,body,user):
    dataset=read(aid,body.dataset_id,user)
    request=body.model_dump(mode='json');identity='run_'+canonical_sha256([aid,request])
    with exam_store()._locked():
        if path(aid,identity).exists():return read(aid,identity,user)
        for p in gold.folder(aid).glob('run_*.json'):
            previous=read_sealed(p)
            if previous['dataset_id']==body.dataset_id:raise ExamConflict('dataset already evaluated; preserve the original run')
    code=cert.code_version()
    if code['application_sha256']!=dataset['code']['application_sha256']:raise ExamConflict('application changed after freeze; new dataset version and holdout required')
    environment=execution_environment()
    if environment!=dataset['environment']:raise ExamConflict('environment changed after freeze; new protocol required')
    data=cert.build(aid,user,'current',gold_version=dataset['gold_version'])
    if data['manifest']['gold']['sha256']!=dataset['gold_sha256']:raise ExamConflict('gold snapshot changed')
    indexed={r['question_attempt_id']:r for r in data['records']};records=[]
    for c in dataset['cases']:
        row=indexed.get(c['question_attempt_id'])
        if not row:raise ExamConflict('registered attempt missing')
        e=row['dynamic_evaluation']
        if row['transcription_version']!=c['transcription_version']:e['exclusions'].append('TRANSCRIPTION_MISMATCH')
        if e['context']!=c['context']:e['exclusions'].append('RUBRIC_MISMATCH')
        if c['split']=='HOLDOUT':
            # Chronology is checked against persisted AuditRun time, not user metadata.
            if row['timestamps']['audit_started_at'] and row['timestamps']['audit_started_at']<=dataset['frozen_at']:
                raise ExamConflict('holdout was graded before freeze')
        e['exclusions']=sorted(set(e['exclusions']));row['dataset_case']=c;records.append(row)
    metrics=report(records,Decimal(dataset['request']['material_error_points']),body.bootstrap_seed)
    value=dict(schema_version='certification-run.v1',id=identity,assessment_id=aid,dataset_id=body.dataset_id,dataset_sha256=canonical_sha256(dataset),
        request=request,created_at=now(),created_by=user.user_id,evaluation_mode='SHADOW_EVALUATION',official_correction_affected=False,
        code=code,environment=environment,
        manifest=data['manifest'],source_events=data['events'],finalization_history=data['finalization_history'],records=records,records_sha256=canonical_sha256(records),metrics=metrics,
        verdict=gate_verdict(metrics,dataset['request'].get('gates')),events=[dict(event_type='certification_run_created',dataset_id=body.dataset_id)],
        formal_validation=dict(status='ENVIRONMENT_PENDING',reference='CONFIA_DYNAMIC_DY6_MULTIQUESTION_IMPLEMENTACAO_01.md',
            tests=['test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline','test_real_local_lean_status_certificates_preserved',
                   'test_wrong_reasoning_correct_final_is_refuted_by_real_lean','test_real_formal_verified_is_preserved_and_not_semantic']))
    with exam_store()._locked():
        # Repeat the single-run guard under the publication lock.
        for p in gold.folder(aid).glob('run_*.json'):
            prior=read_sealed(p)
            if prior['dataset_id']==body.dataset_id:
                if prior['request']==request:return prior
                raise ExamConflict('dataset already evaluated')
        return save(aid,identity,value)


def listing(aid,user):
    gold.owned_assessment(aid,user)
    with exam_store()._locked():
        return [dict(id=v['id'],created_at=v['created_at'],dataset_id=v['dataset_id'],verdict=v['verdict'])
                for v in (read_sealed(p) for p in sorted(gold.folder(aid).glob('run_*.json')))]


def export_csv(run):
    fields=['schema_version','run_id','dataset_id','participant_code','question_attempt_id','split','source_kind','domain','difficulty','solution_type',
            'profile','stage','criteria_json','checkers_json','grader_version','reviewer_version','policy_version','application_sha256','created_at','score','gold_score','max_score','review_required','technical_failures','exclusions','transcription_version','rubric_id','rubric_version','gold_record_id','gold_version','git_sha']
    out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
    for r in run['records']:
        d=r['dynamic_evaluation'];m=r['dataset_case']
        for name,s in d['stages'].items():
            row=dict(schema_version='certification-stages-csv.v1',run_id=run['id'],dataset_id=run['dataset_id'],participant_code=r['participant_code'],
                question_attempt_id=r['question_attempt_id'],**{k:m[k] for k in ('split','source_kind','domain','difficulty','solution_type')},
                profile=d['policy_profile'],stage=name,criteria_json=json.dumps(s['criteria'],ensure_ascii=False),checkers_json=json.dumps(d['checkers'],ensure_ascii=False),grader_version=d['context']['grader_version'],reviewer_version=d['provenance']['reviewer_version'],policy_version=d['provenance']['policy_version'],application_sha256=run['code']['application_sha256'],created_at=run['created_at'],score=s['score'],gold_score=r['human_gold_score'],max_score=r['max_score'],review_required=s['review_required'],
                technical_failures='|'.join(s['technical_failures']),exclusions='|'.join(d['exclusions']),transcription_version=r['transcription_version'],
                rubric_id=d['context']['rubric_id'],rubric_version=d['context']['rubric_version'],gold_record_id=r['gold_record_id'],gold_version=r['gold_version'],git_sha=run['code']['git_sha'])
            for key,v in row.items():
                if key not in {'score','gold_score','max_score'} and isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r','\n')):row[key]="'"+v
            writer.writerow(row)
    return out.getvalue()


def markdown(run):
    lines=['# Dynamic — resultado experimental', '', 'SHADOW_EVALUATION · Sem alteração da correção oficial.', '',f"Run: `{run['id']}`; dataset: `{run['dataset_id']}`.",
        f"Git SHA: `{run['code']['git_sha']}`; aplicação SHA256: `{run['code']['application_sha256']}`.", '',
        '| Perfil | Split | Origem | Estágio | N | MAE | False credit | Missed credit | Automação | Risco automático |',
        '|---|---|---|---|---:|---:|---:|---:|---:|---:|']
    for stratum in run['metrics']['strata']:
        for name,s in stratum['metrics']['stages'].items():
            values=[stratum['profile'],stratum['split'],stratum['source_kind'],name,s['score']['N'],s['score']['MAE'],s['criterion']['false_credit_rate'],s['criterion']['missed_credit_rate'],s['automation_coverage'],s['unsafe_automation_rate']]
            lines.append('| '+' | '.join('—' if v is None else str(v) for v in values)+' |')
        lines.extend(['',f"Exclusões: `{stratum['metrics']['exclusions']}`. Falhas técnicas: {stratum['metrics']['technical_failure_cases']}.",
            f"Incerteza: `{stratum['metrics']['uncertainty']['status']}`; grupos independentes: {stratum['metrics']['uncertainty']['N_groups']}.",''])
    lines.extend(['Amostras pequenas são pilotos descritivos. Concordância entre agentes não é verdade. Gold sintético não demonstra eficácia em alunos reais.',
                  '',f"Veredito experimental: **{run['verdict']['status']}**.",''])
    return '\n'.join(lines)
