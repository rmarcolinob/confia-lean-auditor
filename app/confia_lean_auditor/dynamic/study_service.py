"""Student-owned context around existing DYNAMIC engines, never an official grade."""
from datetime import datetime,timezone
from types import SimpleNamespace
from pathlib import Path
from uuid import uuid4
import os,re,json
from fastapi import HTTPException
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.assessments.store import AssessmentStore
from confia_lean_auditor.submissions.router import store as submissions
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.submissions.schemas import CreateTranscriptionRequest,CreateTranscriptionRevisionRequest
from confia_lean_auditor.submissions.integrity import canonical_sha256,model_sha256
from confia_lean_auditor.submission_audits.source import convert_segments
from confia_lean_auditor.tme.exam_store import sealed,read_sealed,ExamConflict
from .study_models import StudyStatement,StudyRubric,LearningReport
from .provider import OpenAIPreparationProvider,ProviderFailure
from .preparation_models import PreparationRecord,PreparationProposal
from .grading_models import DynamicGradingContext
from .models import SuggestedRubric
from .verification import analyze
from .study_capture import receive
from . import study_feedback

CATALOG=[
 dict(id='quadratic',topic='Equações do segundo grau',statement='Resolva x² − 5x + 6 = 0 no conjunto dos números reais. Justifique e confira as soluções.'),
 dict(id='linear-system',topic='Sistemas lineares',statement='Resolva o sistema x + y = 7 e 2x − y = 2. Explique o método e confira o par obtido.'),
 dict(id='proportion',topic='Proporcionalidade',statement='Três cadernos iguais custam R$ 18. Quanto custam cinco cadernos, mantendo o preço por unidade? Justifique.'),
 dict(id='function',topic='Funções',statement='Uma função afim passa pelos pontos (0, 3) e (2, 7). Determine sua expressão e explique o significado dos coeficientes.'),
 dict(id='geometry',topic='Geometria',statement='Um retângulo mede 8 cm por 5 cm. Determine área e perímetro, explicando a diferença entre essas medidas.')]

def now():return datetime.now(timezone.utc).isoformat()
def provider():return OpenAIPreparationProvider()
def root():
    p=Path(os.getenv('CONFIA_SELF_STUDY_DIR',str(get_repo_root()/'runtime'/'self_study'))).absolute()
    if any(q.is_symlink() for q in [p,*p.parents]):raise ExamConflict('Armazenamento inválido.')
    p.mkdir(parents=True,exist_ok=True);return p

def save(path,value):SubmissionStore._write_atomic_new(path,json.dumps(sealed(value),ensure_ascii=False).encode())
def read(path):return read_sealed(path)
def session(user):
    if user is None:raise HTTPException(401,'Entre com uma conta de aluno.')
    if user.role!=Role.STUDENT or not user.active:raise HTTPException(403,'Estudo privado do aluno.')
    return user

def folder(identifier,user):
    session(user)
    if not re.fullmatch(r'study_[0-9a-f]{32}',identifier):raise HTTPException(404)
    p=root()/identifier
    if p.is_symlink():raise ExamConflict('Armazenamento inválido.')
    d=read(p/'study.json')
    if d['student_id']!=user.user_id:raise HTTPException(404)
    return p,d

def lock(p):return AssessmentStore(p/'operations')._locked()
def attempt(p,identifier):
    if not re.fullmatch(r'try_[0-9a-f]{32}',identifier):raise HTTPException(404)
    return read(p/'attempts'/identifier/'attempt.json')

def source_id(p,d,aid=None):return attempt(p,aid)['submission_id'] if aid else d['submission_id']
def history(sid,user):
    store=submissions();record=store.get_record(sid)
    if record.source!='self_study' or record.submitted_by_user_id!=user.user_id:raise HTTPException(404)
    with store._locked():store.assert_submission_integrity(sid)
    histories=store.list_transcriptions(sid)
    return (store.transcription_history(histories[0].transcription.transcription_id) if histories else None),record

def selected(p,d,user,aid=None):
    sid=source_id(p,d,aid);h,r=history(sid,user)
    if not h:raise ExamConflict('Confira uma transcrição antes de continuar.')
    revision=h.revisions[-1];digest=model_sha256(revision,exclude_unset=True)
    return sid,h,revision,digest

def proof_path(p,sid,digest):return p/'reading_confirmations'/f'{sid}_{digest}.json'
def confirmed(p,d,user,aid=None):
    sid,h,revision,digest=selected(p,d,user,aid)
    proof=read(proof_path(p,sid,digest)) if proof_path(p,sid,digest).exists() else None
    if not proof or proof['confirmed_by']!=user.user_id:raise ExamConflict('Confirme explicitamente a leitura atual.')
    text,warnings=convert_segments(revision.segments)
    if warnings or not text.strip() or re.search(r'\[\s*(ileg[ií]vel|unreadable|inaud[ií]vel|\?+)',text,re.I):raise ExamConflict('Resolva os trechos ilegíveis ou não identificados antes da análise.')
    return sid,h,revision,digest,text

def editable(p,aid):
    if aid and (p/'attempts'/aid/'analysis.json').exists():raise ExamConflict('Esta tentativa já foi analisada. Crie uma nova tentativa para revisar.')

def create(body,user):
    session(user);identifier='study_'+canonical_sha256(dict(user=user.user_id,key=body.execution_key))[:32];p=root()/identifier
    with lock(root()):
        if (p/'study.json').exists():
            _,d=folder(identifier,user)
            if d['request_sha256']!=canonical_sha256(body.model_dump(mode='json')):raise ExamConflict('Chave reutilizada com outro enunciado.')
            return view(identifier,user)
        pid='dyn_'+uuid4().hex
        sid=receive(submissions(),identifier,pid,'STATEMENT',body.source,user)
        save(p/'study.json',dict(context='SELF_STUDY',study_id=identifier,problem_id=pid,student_id=user.user_id,grade_year=body.grade_year,
            submission_id=sid,created_at=now(),request_sha256=canonical_sha256(body.model_dump(mode='json'))))
    return view(identifier,user)

def list_studies(user):
    session(user);rows=[]
    for p in root().glob('study_*'):
        d=read(p/'study.json')
        if d['student_id']==user.user_id:
            h,_=history(d['submission_id'],user);text=convert_segments(h.revisions[-1].segments)[0] if h else 'Enunciado por fotografia'
            rows.append(dict(study_id=d['study_id'],statement=text[:200],created_at=d['created_at']))
    return sorted(rows,key=lambda r:r['created_at'],reverse=True)

def revise(identifier,body,user,aid=None):
    p,d=folder(identifier,user)
    with lock(p):
        editable(p,aid);sid=source_id(p,d,aid);h,_=history(sid,user);store=submissions()
        if h:
            if h.revisions[-1].revision_number!=body.based_on_revision_number:raise ExamConflict('A leitura mudou.')
            store.create_transcription_revision(h.transcription.transcription_id,CreateTranscriptionRevisionRequest(
                based_on_revision_number=body.based_on_revision_number,reviewer_reference=user.user_id,segments=body.segments,status='NEEDS_REVIEW'))
        else:
            if body.based_on_revision_number:raise ExamConflict('A leitura mudou.')
            store.create_transcription(sid,CreateTranscriptionRequest(reviewer_reference=user.user_id,segments=body.segments))
    return view(identifier,user)

def recognize(identifier,user,aid=None):
    p,d=folder(identifier,user)
    with lock(p):
        editable(p,aid);sid=source_id(p,d,aid);history(sid,user)
        from confia_lean_auditor.recognition.service import RecognitionService
        from confia_lean_auditor.recognition.schemas import RecognitionRequest
        from confia_lean_auditor.tme.router import configured_registry
        RecognitionService(submissions(),configured_registry()).recognize(sid,RecognitionRequest(provider='mathpix_image'))
    return view(identifier,user)

def confirm_reading(identifier,body,user,aid=None):
    p,d=folder(identifier,user)
    with lock(p):
        editable(p,aid);sid,h,revision,digest=selected(p,d,user,aid)
        if (revision.revision_number,digest)!=(body.revision_number,body.revision_sha256):raise ExamConflict('A leitura mudou; confira a versão corrente.')
        text,warnings=convert_segments(revision.segments)
        if warnings or not text.strip() or re.search(r'\[\s*(ileg[ií]vel|unreadable|\?+)',text,re.I):raise ExamConflict('A leitura ainda contém trechos não resolvidos.')
        path=proof_path(p,sid,digest)
        if not path.exists():save(path,dict(schema_version='self-study-reading.v1',submission_id=sid,transcription_id=h.transcription.transcription_id,
            revision_number=revision.revision_number,revision_sha256=digest,confirmed_by=user.user_id,reviewer_role='STUDENT',confirmed_at=now()))
    return view(identifier,user)

def prepare(identifier,user):
    p,d=folder(identifier,user)
    with lock(p):
        sid,h,rev,digest,text=confirmed(p,d,user)
        version=len(list((p/'packages').glob('*.json')))+1
        pkg='pkg_'+uuid4().hex;stamp=now();statement=StudyStatement(problem_id=d['problem_id'],version_number=rev.revision_number,statement=text)
        record=dict(package_id=pkg,version=version,context='SELF_STUDY',status='TECHNICAL_ERROR',rubric_status='PROVISIONAL_FORMATIVE',grade_year=d['grade_year'],
            source_sha256=digest,source_submission_id=sid,statement=statement.model_dump(mode='json'),created_at=stamp)
        try:
            gen=provider();proposal,meta=gen.generate('study_prepare',dict(statement=statement.model_dump(mode='json'),context='SELF_STUDY'),PreparationProposal)
            proposal=PreparationProposal.model_validate(proposal.model_dump());analysis=analyze(proposal)
            prep=PreparationRecord(preparation_id='dprep_'+uuid4().hex,preparation_version=version,problem_id=d['problem_id'],source_package_id=pkg,
                statement_version=rev.revision_number,statement_sha256=canonical_sha256(statement.model_dump(mode='json')),
                status='READY_FOR_REVIEW' if analysis.trust_state=='CHECKED_WITHIN_SCOPE' else 'REVIEW_REQUIRED',created_at=stamp,completed_at=now(),requested_by=user.user_id,
                proposal=proposal,analysis=analysis,provenance=meta)
            ambiguity=bool(proposal.uncertainties or any(w.requires_review for w in proposal.warnings) or any(a.source=='INFERRED' for a in proposal.assumptions))
            record.update(preparation=prep.model_dump(mode='json'),interpretation=proposal.normalized_problem,
                uncertainties=list(proposal.uncertainties)+[w.message for w in proposal.warnings],status='NEEDS_CLARIFICATION' if ambiguity else 'AWAITING_CONFIRMATION')
            if not study_feedback.interpretation_allowed(record):
                ambiguity=True;record['status']='NEEDS_CLARIFICATION'
            if not ambiguity:
                suggestion,rmeta=gen.generate('study_rubric',dict(statement=statement.model_dump(mode='json'),preparation=proposal.model_dump(mode='json'),max_score='3',context='SELF_STUDY'),SuggestedRubric)
                suggestion=SuggestedRubric.model_validate(suggestion.model_dump())
                if suggestion.max_score!=3 or not suggestion.criteria:raise ValueError('invalid provisional rubric')
                rubric=StudyRubric(max_score=suggestion.max_score,criteria=suggestion.criteria,rubric_id='drub_'+uuid4().hex,version_number=version,provenance=rmeta.model_dump(mode='json'))
                record['rubric']=rubric.model_dump(mode='json')
        except Exception as exc:
            record.update(status='TECHNICAL_ERROR',error_code=exc.code if isinstance(exc,ProviderFailure) else 'PREPARATION_INVALID_OUTPUT',
                failure_provenance=exc.provenance.model_dump(mode='json') if isinstance(exc,ProviderFailure) and exc.provenance else None)
        save(p/'packages'/f'{version:06d}.json',record)
    return view(identifier,user)

def package(p,pkg):
    if not re.fullmatch(r'pkg_[0-9a-f]{32}',pkg):raise HTTPException(404)
    for path in (p/'packages').glob('*.json'):
        r=read(path)
        if r['package_id']==pkg:return r
    raise HTTPException(404)

def confirm_package(identifier,body,user):
    p,d=folder(identifier,user)
    with lock(p):
        pack=package(p,body.package_id);_,_,_,digest,_=confirmed(p,d,user)
        if not study_feedback.interpretation_allowed(pack) or pack['status']!='AWAITING_CONFIRMATION' or pack['source_sha256']!=digest or canonical_sha256(pack)!=body.package_sha256:raise ExamConflict('Confira uma interpretação válida da leitura atual.')
        target=p/'package_confirmations'/f'{body.package_id}.json'
        if not target.exists():save(target,dict(package_id=body.package_id,package_sha256=body.package_sha256,confirmed_by=user.user_id,confirmed_at=now(),rubric_approval=False))
    return view(identifier,user)

def create_attempt(identifier,body,user):
    p,d=folder(identifier,user)
    with lock(p):
        pack=package(p,body.package_id)
        if not study_feedback.interpretation_allowed(pack):raise ExamConflict('Confira uma interpretação compatível antes de iniciar outra tentativa.')
        proof=read(p/'package_confirmations'/f'{body.package_id}.json')
        if proof['package_sha256']!=canonical_sha256(pack):raise ExamConflict('Configuração alterada.')
        _,_,_,digest,_=confirmed(p,d,user)
        if pack['source_sha256']!=digest:raise ExamConflict('Prepare e confira a nova versão do enunciado.')
        aid='try_'+canonical_sha256(dict(study=identifier,key=body.execution_key))[:32];target=p/'attempts'/aid/'attempt.json'
        request_hash=canonical_sha256(body.model_dump(mode='json'))
        if target.exists():
            if read(target)['request_sha256']!=request_hash:raise ExamConflict('Chave de tentativa já utilizada.')
        else:
            sid=receive(submissions(),identifier,d['problem_id'],'SOLUTION',body.source,user)
            save(target,dict(attempt_id=aid,package_id=pack['package_id'],package_sha256=canonical_sha256(pack),submission_id=sid,
                created_at=now(),request_sha256=request_hash,student_id=user.user_id,number=len(list((p/'attempts').glob('try_*')))+1))
    return view(identifier,user)

def evaluate(identifier,aid,user):
    p,d=folder(identifier,user)
    with lock(p):
        a=attempt(p,aid);base=p/'attempts'/aid;target=base/'analysis.json'
        if target.exists():return view(identifier,user)
        sid,h,rev,digest,text=confirmed(p,d,user,aid);pack=package(p,a['package_id'])
        if a['package_sha256']!=canonical_sha256(pack):raise ExamConflict('Configuração divergente.')
        source=SimpleNamespace(solution_text=text,problem_id=d['problem_id'],transcription_id=h.transcription.transcription_id,revision_number=rev.revision_number,
            source_hash=canonical_sha256(dict(revision_sha256=digest,submission_id=sid,package_sha256=a['package_sha256'])),provenance=SimpleNamespace(revision=rev))
        record=dict(context='SELF_STUDY',attempt_id=aid,package_sha256=a['package_sha256'],solution_text=text,revision_sha256=digest,
            source_hash=source.source_hash,created_at=now(),evaluator='dynamic-self-study.v1',reading_confirmation=read(proof_path(p,sid,digest)))
        try:
            statement=StudyStatement.model_validate(pack['statement']);rubric=StudyRubric.model_validate(pack['rubric']);prep=PreparationRecord.model_validate(pack['preparation'])
            context=DynamicGradingContext(semantic_policy='dynamic-semantic.v1',problem_id=d['problem_id'],package_id=pack['package_id'],package_version=pack['version'],package_sha256=a['package_sha256'],
                statement_version=statement.version_number,statement_sha256=canonical_sha256(pack['statement']),preparation_id=prep.preparation_id,preparation_version=prep.preparation_version,
                preparation_sha256=canonical_sha256(pack['preparation']),rubric_id=rubric.rubric_id,rubric_version=rubric.version_number,rubric_sha256=canonical_sha256(pack['rubric']),allow_preparation_review=True)
            from .grader import DynamicSolutionGrader
            from .reviewer import blind_input
            from .semantic import review_phase
            from .review_comparison import compare_review
            from .reconciliation import reconcile_criteria
            grader=DynamicSolutionGrader().grade(source,statement,rubric,prep,context,base/('engine_'+uuid4().hex))
            payload,_,_=blind_input(source,statement,rubric,prep,context)
            phase=review_phase(payload,rubric)
            comparison=compare_review(grader,phase,rubric,text)
            review=SimpleNamespace(phase_a=phase,comparison=comparison,status='COMPLETED')
            rows=reconcile_criteria(grader,review,statement,rubric,text,'FORMATIVE_LIST')
            prior=[]
            for path in (p/'attempts').glob('try_*/analysis.json'):
                old=read(path)
                if old.get('package_sha256')==a['package_sha256'] and old.get('report'):prior.append(old)
            previous=study_feedback.public_report(max(prior,key=lambda r:r['created_at']),pack) if prior else None
            report=study_feedback.project(grader,rows,source,rubric,previous,phase.semantic_reviews)
            record.update(grader=grader.model_dump(mode='json'),reviewer=phase.model_dump(mode='json'),comparison=comparison.model_dump(mode='json'),
                reconciliation=[r.model_dump(mode='json') for r in rows],report=report.model_dump(mode='json'))
        except Exception as exc:
            record.update(error_code=exc.code if isinstance(exc,ProviderFailure) else 'EVALUATION_TECHNICAL_ERROR',report=LearningReport(status='TECHNICAL_ERROR',findings=[],comparison=[],uncertainties=['Falha técnica; sua resolução foi preservada. Nenhum erro matemático foi inferido.']).model_dump(mode='json'))
        save(target,record)
    return view(identifier,user)

def help_level(identifier,aid,body,user):
    p,d=folder(identifier,user)
    with lock(p):
        a=attempt(p,aid);base=p/'attempts'/aid;record=read(base/'analysis.json');pack=package(p,a['package_id'])
        if body.level==4 and not body.request_complete_solution:raise ExamConflict('A resolução orientada exige solicitação explícita.')
        if body.level>2 and not (base/'help'/f'{body.level-1}.json').exists():raise ExamConflict('Consulte a pista anterior antes de avançar.')
        path=base/'help'/f'{body.level}.json'
        if not path.exists():
            if not any(f['evidence'] for f in record['report']['findings']):raise ExamConflict('Não há evidência suficiente para orientar este trecho. Revise a leitura ou tente novamente.')
            report=study_feedback.public_report(record,pack)
            payload=study_feedback.help_payload(pack,record,report,body.level)
            try:
                proposal,meta=study_feedback.generate_help(provider(),payload)
                save(path,dict(level=body.level,requested_by=user.user_id,requested_at=now(),analysis_sha256=canonical_sha256(record),policy_version=study_feedback.POLICY,
                    status='ACCEPTED',complete_solution_requested=body.request_complete_solution,
                    content=proposal.model_dump(mode='json'),provenance=meta.model_dump(mode='json')))
            except Exception as exc:
                provenance=getattr(exc,'provenance',None)
                save(base/'help_failures'/f'{uuid4().hex}.json',dict(level=body.level,error_code=exc.code if isinstance(exc,ProviderFailure) else 'INVALID_PEDAGOGICAL_OUTPUT',created_at=now(),
                    raw_response=getattr(exc,'raw',None),provenance=provenance.model_dump(mode='json') if provenance else None))
                save(path,dict(level=body.level,requested_by=user.user_id,requested_at=now(),analysis_sha256=canonical_sha256(record),policy_version=study_feedback.POLICY,
                    status='SAFE_FALLBACK',complete_solution_requested=body.request_complete_solution))
    return view(identifier,user)

def source_view(p,sid,user):
    h,r=history(sid,user);rev=h.revisions[-1] if h else None;digest=model_sha256(rev,exclude_unset=True) if rev else None
    return dict(submission_id=sid,revision_number=rev.revision_number if rev else 0,revision_sha256=digest,
        confirmed=bool(digest and proof_path(p,sid,digest).exists()),automatic=bool(h and h.transcription.source=='automatic'),
        segments=[s.model_dump(mode='json') for s in rev.segments] if rev else [],
        pages=[dict(page_index=a.page_index,preview_url=f'/dynamic/self-study/{p.name}/sources/{sid}/assets/{a.filename}') for a in r.page_images],
        originals=[dict(url=f'/dynamic/self-study/{p.name}/sources/{sid}/assets/{a.filename}',media_type=a.media_type) for a in r.scan_originals or []])

def view(identifier,user):
    p,d=folder(identifier,user);packs=[];private_packs={};statement_source=source_view(p,d['submission_id'],user)
    for path in sorted((p/'packages').glob('*.json')):
        r=read(path);private_packs[r['package_id']]=r
        compatible=study_feedback.interpretation_allowed(r)
        packs.append(dict(package_id=r['package_id'],version=r['version'],sha256=canonical_sha256(r),
            status=r['status'] if compatible or r['status']=='TECHNICAL_ERROR' else 'NEEDS_CLARIFICATION',
            statement=r['statement']['statement'],current_statement=r['source_sha256']==statement_source['revision_sha256'],
            interpretation=r['statement']['statement'] if compatible else None,
            uncertainties=['Confira o enunciado: há ambiguidades ou a interpretação gerada modificou o texto.'] if not compatible or r.get('uncertainties') else [],
            error_code='PREPARATION_UNAVAILABLE' if r.get('error_code') else None,rubric_status='PROVISIONAL_FORMATIVE',
            objectives=[dict(criterion_id=study_feedback.public_id(c['criterion_id']),title='Objetivo '+str(c['order'])) for c in r.get('rubric',{}).get('criteria',[])],
            confirmed=compatible and (p/'package_confirmations'/f"{r['package_id']}.json").exists()))
    records=[];reports={};previous={}
    for path in (p/'attempts').glob('try_*/attempt.json'):
        a=read(path);base=path.parent;raw=read(base/'analysis.json') if (base/'analysis.json').exists() else None
        records.append((a,base,raw))
    # Historical public prose is never returned verbatim. This derived view does
    # not mutate the stored report, opinions, scores, or historical help records.
    for a,base,raw in sorted((row for row in records if row[2]),key=lambda row:row[2]['created_at']):
        pack=private_packs[a['package_id']]
        report=study_feedback.public_report(raw,pack,previous.get(a['package_sha256']))
        reports[a['attempt_id']]=report;previous[a['package_sha256']]=report
    attempts=[]
    for a,base,raw in records:
        report=reports.get(a['attempt_id']);helps=[];pack=private_packs[a['package_id']]
        for hp in sorted((base/'help').glob('*.json')):
            h=read(hp)
            if not raw or h['analysis_sha256']!=canonical_sha256(raw):raise ExamConflict('Vínculo da orientação inválido.')
            payload=study_feedback.help_payload(pack,raw,report,h['level'])
            content,status=study_feedback.public_help(h,payload,report)
            helps.append(dict(level=h['level'],content=content,status=status,requested_at=h['requested_at'],verification='SEMANTIC_NOT_FORMAL'))
        attempts.append(dict(attempt_id=a['attempt_id'],number=a['number'],package_id=a['package_id'],created_at=a['created_at'],source=source_view(p,a['submission_id'],user),
            report=report,help=helps))
    return dict(context='SELF_STUDY',study_id=identifier,grade_year=d['grade_year'],source=statement_source,
        packages=packs,attempts=sorted(attempts,key=lambda a:a['number']),policy=dict(version=study_feedback.POLICY,progressive=True,complete_solution_requires_request=True,official_grade_applicable=False))

def asset(identifier,sid,name,user):
    p,d=folder(identifier,user)
    allowed={d['submission_id'],*[read(path)['submission_id'] for path in (p/'attempts').glob('try_*/attempt.json')]}
    if sid not in allowed:raise HTTPException(404)
    _,record=history(sid,user)
    ref=next((a for a in [*record.page_images,*(record.scan_originals or [])] if a.filename==name),None)
    if not ref:raise HTTPException(404)
    data=(submissions()._folder(sid)/ref.filename).read_bytes()
    from hashlib import sha256
    if sha256(data).hexdigest()!=ref.sha256:raise ExamConflict('Original alterado.')
    return data,ref.media_type
