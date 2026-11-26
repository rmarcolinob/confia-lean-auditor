"""Accepted revision -> real opt-in engine -> immutable AuditRun -> existing API."""
import json
from uuid import uuid4
from pathlib import Path
from decimal import Decimal

import pytest
from test_tme_pilot import setup, scan_payload
from test_submissions import payload
from confia_lean_auditor.submission_audits import router as audits
from confia_lean_auditor.submission_audits.schemas import AuditRequest
from confia_lean_auditor.tme import accepted_audit
from confia_lean_auditor.tme.registry import audit_tme
from confia_lean_auditor.rubric.pauta import PautaEngine

ROOT = Path(__file__).resolve().parents[1]
CASES = {n: {c['id']: c for c in json.loads((ROOT/f'tests/fixtures/tme2_p{n}_digital/cases.json').read_text())} for n in range(1,6)}
FULL = {1:['a_complete','b_complete','c_complete','d_complete'],2:['a_text_complete','b_complete','c_complete'],
        3:['a_complete','b_official','c_complete'],4:['a_complete','b_official','c_complete'],
        5:['a_complete','b_complete','c_complete','d_complete']}
PARTIAL = {1:'a_only_inverse',2:'a_pairs_only',3:'a_answer_only',4:'b_partial',5:'a_list_only'}
FALSE = {1:'a_single_arithmetic_error',2:'b_false_center',3:'a_wrong_probability',4:'a_wrong_perimeter',5:'a_false_product'}


def solution_for(n, identifiers):
    solution={}
    for identifier in identifiers:
        c=CASES[n][identifier]
        solution.update(c.get('solution',{c['item']:c['text']}))
    return solution


@pytest.fixture
def offline(setup, monkeypatch):
    original=audits.service
    def factory():
        service=original();service.tme_use_lean=False;return service
    monkeypatch.setattr(audits,'service',factory)
    # TME router imported the factory by name; preserve the same store/engine.
    from confia_lean_auditor.tme import router
    monkeypatch.setattr(router,'audit_service',factory)
    return setup


def prepare(client, n, solution, mode='DIGITAL_INK', *, accept=True, headers=False):
    response=client.post('/tme/cases',json=dict(problem_id=f'TME2026P{n}',external_candidate_ref='CONTROL',source_mode=mode))
    assert response.status_code==201,response.text
    case=response.json();base=f'/tme/cases/{case["case_id"]}'
    if mode=='IMAGE_SCAN':response=client.post(base+'/scan',json=scan_payload(2))
    else:
        body=payload();body['student_reference']=None;snapshot=json.loads(body['snapshot_json']);snapshot['problem_id']=case['problem_id'];snapshot['local_snapshot_id']='test:'+uuid4().hex;body['snapshot_json']=json.dumps(snapshot)
        response=client.post(base+'/digital-submission',json=body)
    assert response.status_code==201,response.text
    sid=response.json()['submission_id'];segments=[]
    for i,(item,entry) in enumerate(solution.items()):
        value=entry if isinstance(entry,str) else entry.get('text','')
        segment=dict(segment_id=f'seg-{i}',page_index=0,order=i,kind='text')
        if value:segment['text']=(f'[{item}]\n'+value) if headers else value
        if not headers:segment['tme_item_id']=item
        if isinstance(entry,dict) and entry.get('diagrams'):
            segment['tme_diagrams']=entry['diagrams']
            if not value:segment['kind']='diagram'
        segments.append(segment)
    response=client.post(f'/submissions/{sid}/transcriptions',json=dict(reviewer_reference='evaluator',segments=segments))
    assert response.status_code==201,response.text
    rev=response.json();tid=rev['transcription_id']
    acc_id='acc_'+'0'*32
    if accept:
        response=client.post(f'{base}/transcriptions/{tid}/accept',json={'revision_number':1})
        assert response.status_code==200,response.text
        acc_id=response.json()['acceptance']['acceptance_id']
    request=dict(transcription_id=tid,revision_number=1,acceptance_id=acc_id)
    return base,sid,rev,request


def execute(client, base, request):
    response=client.post(base+'/audits',json=request)
    assert response.status_code==200,response.text
    run=response.json();assert run['status']=='COMPLETED',run.get('error_code')
    stored=audits.service().get(run['audit_run_id'])
    assert client.get(base+'/audits').json()==[run]
    assert client.get(f'/submission-audits/{run["audit_run_id"]}').json()==run
    return run,stored


@pytest.mark.parametrize('n',range(1,6))
@pytest.mark.parametrize('kind',['full','partial','false','indeterminate'])
def test_five_problems_accepted_engine_persistence_api(offline,n,kind):
    client,calls,_=offline
    solution=solution_for(n,FULL[n] if kind=='full' else [PARTIAL[n] if kind=='partial' else FALSE[n]]) if kind!='indeterminate' else {'a':'Uma ideia ainda não estabelecida com segurança.'}
    base,sid,rev,request=prepare(client,n,solution)
    run,stored=execute(client,base,request)
    mathematical=stored.result
    b,a=audit_tme(f'TME2026P{n}',solution,solution_id=mathematical.assessment.solution_id,use_lean=False)
    assert mathematical.bridge.model_dump(mode='json')==b.model_dump(mode='json')
    assert mathematical.assessment.model_dump(mode='json')==a.model_dump(mode='json')
    assert run['source']['provenance']['revision']['segments']==rev['segments']
    assert mathematical.accepted_transcription_revision_id==f'{rev["transcription_id"]}:1'
    assert mathematical.context.pauta_sha256==a.config_sha256
    assert calls==[]  # The ITA/LLM entry point is never invoked.
    if kind=='full':assert mathematical.score==20 and not mathematical.needs_review
    if kind=='false':assert any(f.verification.status=='refuted' for f in b.auditor.facts)
    if kind=='indeterminate':assert mathematical.needs_review and all(e.status=='indeterminate' for e in b.evidence.obligations)
    if kind=='partial':assert mathematical.needs_review


@pytest.mark.parametrize('n',range(1,6))
def test_digital_photo_equal_accepted_math(offline,n):
    client,_,_=offline;solution=solution_for(n,FULL[n]);results=[]
    for mode in ('DIGITAL_INK','IMAGE_SCAN'):
        base,_,_,request=prepare(client,n,solution,mode)
        _,stored=execute(client,base,request);results.append(stored)
    assert results[0].result.bridge==results[1].result.bridge
    assert results[0].result.assessment==results[1].result.assessment
    assert results[0].source.provenance.original_artifacts!=results[1].source.provenance.original_artifacts


def test_acceptance_required_and_no_raw_fallback(offline):
    client,calls,_=offline;base,_,_,req=prepare(client,2,{'a':'line_sum: 15'},accept=False)
    response=client.post(base+'/audits',json=req)
    assert response.status_code==409 and response.json()['error_code']=='TRANSCRIPTION_NOT_ACCEPTED'
    assert calls==[] and not list(audits.service().root.glob('aud_*.json'))


@pytest.mark.parametrize('problem',[None,'','ITA2025Q1','TME2026P6'])
def test_tme_service_rejects_invalid_problem(problem):
    with pytest.raises(accepted_audit.InvalidTMEProblem):accepted_audit.pauta_for(problem)


def test_headers_idempotency_new_acceptance_and_human_decision(offline):
    client,_,_=offline;base,sid,rev,req=prepare(client,2,solution_for(2,FULL[2]),headers=True)
    run,stored=execute(client,base,req);path=audits.service()._path(run['audit_run_id']);before=path.read_bytes()
    again=client.post(base+'/audits',json=req).json();assert again==run and path.read_bytes()==before
    # Human adjustment is separate and requires a reason.
    body=dict(audit_run_id=run['audit_run_id'],max_points=20,final_points=19,feedback='Revisão humana')
    assert client.post(base+'/decision',json=body).status_code==422
    body['override_reason']='Ajuste justificado pelo avaliador'
    response=client.post(base+'/decision',json=body);assert response.status_code==201,response.text
    assert Decimal(response.json()['suggested_points'])==20 and Decimal(response.json()['final_points'])==19
    assert path.read_bytes()==before
    response=client.post(f'{base}/transcriptions/{rev["transcription_id"]}/revisions',json=dict(based_on_revision_number=1,segments=[dict(segment_id='new',page_index=0,order=0,kind='text',text='[a]\nline_sum: 15')]))
    assert response.status_code==201,response.text
    acc=client.post(f'{base}/transcriptions/{rev["transcription_id"]}/accept',json={'revision_number':2}).json()['acceptance']
    new=client.post(base+'/audits',json={**req,'revision_number':2,'acceptance_id':acc['acceptance_id']}).json()
    assert new['status']=='COMPLETED' and new['audit_run_id']!=run['audit_run_id']
    assert path.read_bytes()==before and audits.service().get(run['audit_run_id']).stale


def test_p2_diagram_and_missing_diagram(offline):
    client,_,_=offline
    for solution,expected in [(solution_for(2,['a_diagram_only']),5),({'a':'pairs: {(1,9),(2,8),(3,7),(4,6)}'},3)]:
        base,_,_,req=prepare(client,2,solution);_,run=execute(client,base,req)
        a=run.result.assessment.items[0];assert a.points_awarded==expected
        if expected==5:
            record=next(r for r in run.result.bridge.auditor.records if r.claim_type=='diagram_state')
            assert record.source.source_start is None and record.source.confirmed
        else:
            evidence={e.obligation_id:e.status for e in run.result.bridge.evidence.obligations}
            assert evidence['a.placement']=='indeterminate' and a.needs_review


@pytest.mark.parametrize('n,case',[(3,'b_tree'),(4,'b_parallelogram'),(5,'c_general'),(5,'d_cf_valid')])
def test_alternative_and_carry_forward_survive(offline,n,case):
    client,_,_=offline;solution=solution_for(n,[case]);base,_,_,req=prepare(client,n,solution)
    _,run=execute(client,base,req);_,expected=audit_tme(f'TME2026P{n}',solution,solution_id=run.result.assessment.solution_id,use_lean=False)
    assert run.result.assessment.model_dump(mode='json')==expected.model_dump(mode='json')
    if case=='d_cf_valid':
        def carried(d):return d.carry_forward_applied or any(carried(c) for c in d.children)
        assert any(carried(i) for i in expected.items)


def test_technical_failure_is_not_zero(offline,monkeypatch):
    client,_,_=offline;original=accepted_audit.audit_tme
    def technical(*args,**kwargs):
        bridge,assessment=original(*args,**kwargs)
        evidence=bridge.evidence.model_copy(update={'obligations':tuple(e.model_copy(update={'status':'technical_error'}) for e in bridge.evidence.obligations)})
        bridge=bridge.model_copy(update={'evidence':evidence})
        return bridge,PautaEngine().evaluate(accepted_audit.pauta_for(args[0]),evidence)
    monkeypatch.setattr(accepted_audit,'audit_tme',technical)
    base,_,_,req=prepare(client,2,{'a':'line_sum: 15'});_,run=execute(client,base,req)
    assert run.result.score is None and run.result.needs_review
    assert all(i.status=='technical_error' for i in run.result.assessment.items)


def test_real_local_lean_status_certificates_preserved(offline):
    client,_,_=offline
    base,_,_,req=prepare(client,2,{'c':'pair_permutations: 4!=24\npair_orientations: 2^4=8'})
    service=audits.service();service.tme_use_lean=True
    sid=service.submissions.transcription_history(req['transcription_id']).transcription.submission_id
    run=service.execute(sid,AuditRequest(**req))
    assert run.status=='COMPLETED'
    checks=[f.student_check for f in run.result.bridge.auditor.facts if f.student_check]
    assert {c['status'] for c in checks}=={'verified','refuted'}
    certificates=[a for a in run.required_artifacts if a.artifact_type in ('student_proof','refutation')]
    assert len(certificates)==2 and all(Path(a.file).is_file() for a in certificates)
    assert service.get(run.audit_run_id).result==run.result
    # Mandatory copied certificate integrity is checked on every read.
    Path(certificates[0].file).write_text('changed')
    from confia_lean_auditor.submission_audits.errors import ResultIntegrityError
    with pytest.raises(ResultIntegrityError):service.get(run.audit_run_id)


def test_version_changes_create_new_run_and_keep_old_readable(offline,monkeypatch):
    client,_,_=offline;base,_,_,req=prepare(client,2,{'a':'line_sum: 15'})
    first,_=execute(client,base,req);path=audits.service()._path(first['audit_run_id']);before=path.read_bytes()
    context=accepted_audit.audit_context
    monkeypatch.setattr(accepted_audit,'audit_context',lambda *a:context(*a).model_copy(update={'auditor_version':'test-next-version'}))
    second=client.post(base+'/audits',json=req).json()
    assert second['status']=='COMPLETED' and second['audit_run_id']!=first['audit_run_id']
    assert audits.service().get(first['audit_run_id']).result and path.read_bytes()==before


def test_unlabelled_text_is_preserved_without_item_guess(offline):
    client,_,_=offline;base,sid,rev,req=prepare(client,1,{'a':'137'},accept=False)
    revision=client.post(f'{base}/transcriptions/{rev["transcription_id"]}/revisions',json=dict(based_on_revision_number=1,
        segments=[dict(segment_id='no-item',page_index=0,order=0,kind='text',text='137')])).json()
    acceptance=client.post(f'{base}/transcriptions/{rev["transcription_id"]}/accept',json={'revision_number':2}).json()['acceptance']
    _,run=execute(client,base,{**req,'revision_number':2,'acceptance_id':acceptance['acceptance_id']})
    assert run.source.solution_text=='137' and run.result.input_warnings
    assert not run.result.bridge.auditor.records and run.result.needs_review


def test_mathpix_mock_raw_output_is_never_audited_before_edited_acceptance(offline,monkeypatch):
    import httpx
    from confia_lean_auditor.recognition.registry import RecognizerRegistry
    from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider
    from confia_lean_auditor.tme import router
    client,calls,_=offline;base,sid,_,_=prepare(client,2,{'a':'raw placeholder'},'IMAGE_SCAN',accept=False)
    monkeypatch.setenv('CONFIA_MATHPIX_APP_ID','synthetic-test-id')
    monkeypatch.setenv('CONFIA_MATHPIX_APP_KEY','synthetic-test-key')
    registry=RecognizerRegistry()
    registry.register('mathpix_image',lambda:MathpixImageProvider(httpx.MockTransport(lambda _:httpx.Response(200,json={'text':'[a]\nline_sum: 999'}))))
    monkeypatch.setattr(router,'configured_registry',lambda:registry)
    response=client.post(base+'/recognize',json={});assert response.status_code==200,response.text
    summary=client.get(base+'/transcriptions').json()[0];rev=summary['latest_revision'];tid=rev['transcription_id']
    assert rev['source']=='automatic' and rev['status']=='NEEDS_REVIEW'
    assert client.post(base+'/audits',json=dict(transcription_id=tid,revision_number=1,acceptance_id='acc_'+'0'*32)).status_code==409
    edited=client.post(f'{base}/transcriptions/{tid}/revisions',json=dict(based_on_revision_number=1,
        segments=[dict(segment_id='confirmed',page_index=0,order=0,kind='text',text='[a]\nline_sum: 15')]))
    assert edited.status_code==201,edited.text
    acc=client.post(f'{base}/transcriptions/{tid}/accept',json={'revision_number':2}).json()['acceptance']
    _,photo=execute(client,base,dict(transcription_id=tid,revision_number=2,acceptance_id=acc['acceptance_id']))
    digital_base,_,_,req=prepare(client,2,{'a':'line_sum: 15'},headers=True)
    _,digital=execute(client,digital_base,req)
    assert photo.result.bridge==digital.result.bridge and photo.result.assessment==digital.result.assessment
    assert '999' not in photo.source.solution_text and photo.source.provenance.revision.source=='automatic'
    assert calls==[]


@pytest.mark.parametrize('body',[
    dict(external_candidate_ref='X',source_mode='IMAGE_SCAN'),
    dict(problem_id='TME2026P6',external_candidate_ref='X',source_mode='IMAGE_SCAN')])
def test_missing_or_unknown_tme_problem_rejected_at_case_entry(offline,body):
    client,calls,_=offline
    assert client.post('/tme/cases',json=body).status_code==422
    assert calls==[]


def test_unrecognized_diagram_remains_pending_with_text_preserved(offline):
    client,_,_=offline;base,sid,rev,req=prepare(client,2,{'a':'line_sum: 15'},accept=False)
    segments=[dict(segment_id='text',page_index=0,order=0,kind='text',text='line_sum: 15',tme_item_id='a'),
              dict(segment_id='drawing',page_index=0,order=1,kind='diagram',tme_item_id='a')]
    tid=rev['transcription_id']
    assert client.post(f'{base}/transcriptions/{tid}/revisions',json=dict(based_on_revision_number=1,segments=segments)).status_code==201
    acc=client.post(f'{base}/transcriptions/{tid}/accept',json={'revision_number':2}).json()['acceptance']
    _,run=execute(client,base,{**req,'revision_number':2,'acceptance_id':acc['acceptance_id']})
    assert run.result.input_warnings and run.result.needs_review
    assert run.result.assessment.items[0].points_awarded==1
    evidence={e.obligation_id:e.status for e in run.result.bridge.evidence.obligations}
    assert evidence['a.placement']=='indeterminate' and evidence['a.complete_configuration']=='indeterminate'
    assert not any(r.claim_type=='diagram_state' for r in run.result.bridge.auditor.records)


def test_service_failure_persists_failed_run_without_fictitious_score(offline,monkeypatch):
    client,_,_=offline;base,_,_,req=prepare(client,2,{'a':'line_sum: 15'})
    def broken(*args,**kwargs):raise RuntimeError('synthetic local failure')
    monkeypatch.setattr(accepted_audit,'audit_tme',broken)
    response=client.post(base+'/audits',json=req)
    assert response.status_code==200,response.text
    run=response.json();assert run['status']=='FAILED' and run['result'] is None
    assert run['error_code']=='AUDITOR_FAILED' and run['result_sha256'] is None
    assert audits.service().get(run['audit_run_id']).result is None


def test_multiple_accepted_segments_keep_text_boundaries(offline):
    client,_,_=offline;base,sid,rev,req=prepare(client,2,{'a':'placeholder'},accept=False)
    tid=rev['transcription_id']
    segments=[dict(segment_id='sum',page_index=0,order=0,kind='math',text='line_sum: 15',tme_item_id='a'),
              dict(segment_id='pairs',page_index=0,order=1,kind='math',text='pairs: {(1,9),(2,8),(3,7),(4,6)}',tme_item_id='a')]
    assert client.post(f'{base}/transcriptions/{tid}/revisions',json=dict(based_on_revision_number=1,segments=segments)).status_code==201
    acc=client.post(f'{base}/transcriptions/{tid}/accept',json={'revision_number':2}).json()['acceptance']
    _,run=execute(client,base,{**req,'revision_number':2,'acceptance_id':acc['acceptance_id']})
    b,a=audit_tme('TME2026P2',{'a':'\n'.join(s['text'] for s in segments)},solution_id=run.result.assessment.solution_id,use_lean=False)
    assert run.result.bridge.model_dump(mode='json')==b.model_dump(mode='json')
    assert run.result.assessment.model_dump(mode='json')==a.model_dump(mode='json')


def test_irrelevant_technical_alternative_does_not_override_engine_suggestion(offline,monkeypatch):
    client,_,_=offline;original=accepted_audit.audit_tme
    def alternative_failure(*args,**kwargs):
        bridge,_=original(*args,**kwargs)
        evidence=bridge.evidence.model_copy(update={'obligations':tuple(e.model_copy(update={'status':'technical_error'}) if e.obligation_id=='a.placement' else e for e in bridge.evidence.obligations)})
        return bridge.model_copy(update={'evidence':evidence}),PautaEngine().evaluate(accepted_audit.pauta_for(args[0]),evidence)
    monkeypatch.setattr(accepted_audit,'audit_tme',alternative_failure)
    base,_,_,req=prepare(client,2,solution_for(2,FULL[2]));run,_=execute(client,base,req)
    assert run['result']['score']==20
    body=dict(audit_run_id=run['audit_run_id'],max_points=20,final_points=19)
    assert client.post(base+'/decision',json=body).status_code==422
    body.update(final_points=20)
    response=client.post(base+'/decision',json=body);assert response.status_code==201,response.text
    assert Decimal(response.json()['suggested_points'])==20
