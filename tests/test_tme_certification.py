"""D7: independent gold and provenance over real D1–D6 artifacts."""
import csv
import io
import json
from decimal import Decimal
import pytest
from test_tme_finalization import demo, exam, populate, finalize, summary
from confia_lean_auditor.tme.certification_metrics import comparisons, metrics, rubric_metrics

@pytest.fixture
def shadow(exam,monkeypatch):
    monkeypatch.setenv('CONFIA_TME_CERTIFICATION_ENABLED','1')
    client,root,eid,cases=exam
    aid=summary(client,eid)['assessment_id']
    return exam,aid,f'/tme/assessments/{aid}/certification'


def payload(aid,version='v1',expected=0):
    return dict(source_id='test-independent-gold',dataset_version=version,expected_version=expected,rows=[
        dict(assessment_id=aid,participant_code='PROVA-2026-001',question_id=f'TME2026P{i}',gold_score=score,max_score=20)
        for i,score in enumerate([20,18,19],1)])


def get(client,url):
    r=client.get(url);assert r.status_code==200,r.text;return r.json()


def test_no_gold_read_only_and_opt_in(shadow,monkeypatch):
    ex,aid,url=shadow;client,root,eid,_=ex
    before={p:p.read_bytes() for p in root.rglob('*.json')}
    data=get(client,url+'?selection=current')
    assert data['manifest']['counts']['questions']==3 and data['manifest']['gold'] is None
    assert data['metrics']['confia_vs_gold']['N']==0 and data['metrics']['confia_vs_gold']['MAE'] is None
    assert all(r['suggested_score'] is None and r['human_gold_score'] is None for r in data['records'])
    assert before=={p:p.read_bytes() for p in root.rglob('*.json')}
    assert not get(client,url)['records']
    monkeypatch.delenv('CONFIA_TME_CERTIFICATION_ENABLED')
    assert client.get(url).status_code==404


def test_real_records_import_json_metrics_exports_provenance_and_privacy(shadow):
    ex,aid,url=shadow;client,root,eid,cases=ex
    _,runs,decisions=populate(ex);f=finalize(client,eid)
    before={p:p.read_bytes() for p in root.rglob('*.json')}
    no_gold=get(client,url);assert no_gold['metrics']['confia_vs_gold']['N']==0
    r=client.post(url+'/gold',json=payload(aid));assert r.status_code==201,r.text
    assert all(p.read_bytes()==v for p,v in before.items())
    data=get(client,url);m=data['manifest'];rows=data['records'];stats=data['metrics']
    assert m['evaluation_mode']=='SHADOW_EVALUATION' and m['official_correction_affected'] is False
    assert m['counts']['proofs']==1 and m['counts']['questions']==3 and m['counts']['gold_available']==3
    assert len(m['git_sha'])==40 and len(m['application_sha256'])==64
    assert [Decimal(r['suggested_score']) for r in rows]==[20,15,20]
    assert [Decimal(r['human_decision_score']) for r in rows]==[20,18,19]
    assert [Decimal(r['human_gold_score']) for r in rows]==[20,18,19]
    assert stats['confia_vs_gold']['N']==3 and Decimal(stats['confia_vs_gold']['MAE'])==Decimal(4)/3
    assert Decimal(stats['confia_vs_gold']['bias'])==Decimal(-2)/3
    assert Decimal(stats['confia_vs_gold']['within_1'])==Decimal(2)/3
    assert stats['human_decision_vs_gold']['MAE']=='0.0'
    assert stats['stages']['human_adjustment']['adjusted_count']==2
    for row,run,decision in zip(rows,runs,decisions):
        assert row['audit_run_id']==run['audit_run_id'] and row['human_decision_id']==decision['human_decision_id']
        assert row['final_correction_id']==f['final_correction_id'] and row['transcription_version'] and row['source_submission_id']
        assert row['source_sha256'] and row['result_sha256'] and row['gold_record_id'] and row['gold_sha256']
        assert row['rubric_decisions'] and row['checker_counts']
    types={e['event_type'] for e in data['events']}
    assert {'capture_received','page_created','page_question_associated','transcription_created','audit_started','audit_completed','claim_extracted','claim_mapped','obligation_mapped','checker_completed','rubric_item_decided','suggested_score_created','question_confirmed','score_adjusted','correction_finalized'}<=types
    assert 'checker_started' not in types and 'claim_rejected' not in types
    assert len({e['event_id'] for e in data['events']})==len(data['events'])
    assert data['events']==get(client,url)['events']
    assert any(e['aliases']==['award_decided'] for e in data['events'])
    exported=client.get(url+'/export.csv');assert exported.status_code==200
    csv_rows=list(csv.DictReader(io.StringIO(exported.text)));assert len(csv_rows)==3
    assert csv_rows[1]['signed_error_vs_gold']=='-3.0' and csv_rows[1]['evaluation_mode']=='SHADOW_EVALUATION'
    full=get(client,url+'/export.json');assert full['records']==rows
    encoded=json.dumps(full)
    for forbidden in ['raw_text','override_reason','reviewer_reference','created_by','finalized_by','imported_by','Conferência humana','@','CPF']:
        assert forbidden not in encoded
    assert get(client,url+'?engine_mode=DYNAMIC')['records']==[]
    assert get(client,url+'?engine_mode=TME_CURRENT')['records']==rows


def test_csv_import_versioning_history_and_replay(shadow):
    ex,aid,url=shadow;client,root,eid,_=ex
    body=payload(aid);output=io.StringIO();writer=csv.DictWriter(output,fieldnames=body['rows'][0].keys());writer.writeheader();writer.writerows(body['rows'])
    endpoint=url+'/gold?source_id=test-independent-gold&dataset_version=v1&expected_version=0'
    r=client.post(endpoint,content=output.getvalue(),headers={'Content-Type':'text/csv'});assert r.status_code==201,r.text
    assert client.post(endpoint,content=output.getvalue(),headers={'Content-Type':'text/csv'}).json()==r.json()
    second=payload(aid,'v2',1);second['rows'][0]['gold_score']=19
    assert client.post(url+'/gold',json=second).status_code==201
    history=get(client,url+'/gold');assert len(history['history'])==2 and history['current']['version']==2
    assert history['history'][1]['previous_sha256']==history['history'][0]['sha256']
    assert get(client,url+'/gold?version=1')['records'][0]['gold_score']=='20'
    assert get(client,url+'?gold_version=1')['manifest']['gold']['version']==1
    assert client.get(url+'?gold_version=3').status_code==404
    assert client.post(url+'/gold',json=payload(aid,'v3',0)).status_code==409
    body['rows'][0]['gold_score']=1
    assert client.post(url+'/gold',json=body).status_code==409

@pytest.mark.parametrize('mutation',[
    lambda b:b['rows'].append(dict(b['rows'][0])),
    lambda b:b['rows'][0].update(gold_score=-1),lambda b:b['rows'][0].update(gold_score=21),
    lambda b:b['rows'][0].update(gold_score='NaN'),lambda b:b['rows'][0].update(max_score=19),
    lambda b:b['rows'][0].update(participant_code='UNKNOWN'),lambda b:b['rows'][0].update(question_id='UNKNOWN'),
    lambda b:b['rows'][0].update(assessment_id='asmt_'+'0'*32),
    lambda b:b['rows'][0].update(email='person@example.com'),lambda b:b['rows'][0].update(scorer_reference='person@example.com'),
    lambda b:b['rows'][0].update(rubric_gold=[dict(rubric_item_id='invented',gold_points=1,max_points=1)]),
])
def test_reject_invalid_gold_without_write(shadow,mutation):
    ex,aid,url=shadow;client,root,_,_=ex;body=payload(aid);mutation(body)
    assert client.post(url+'/gold',json=body).status_code==422
    assert get(client,url+'/gold')['history']==[]

@pytest.mark.parametrize('raw',['bad,headers\nx,y','assessment_id,participant_code,question_id,gold_score,max_score\nx,y,z,1,2,extra','\udcff'])
def test_invalid_csv(shadow,raw):
    ex,aid,url=shadow;client,*_=ex
    assert client.post(url+'/gold?source_id=s&dataset_version=v&expected_version=0',content=raw.encode('utf8',errors='surrogateescape'),headers={'Content-Type':'text/csv'}).status_code==422


def test_known_score_metrics_and_missing_pairs():
    rows=[dict(a=a,b=b) for a,b in [(0,2),(3,0),(4,4),(5,4),(1,3),(None,1)]]
    m=comparisons(rows,'a','b')
    assert m==dict(N=5,exact_score_agreement='0.2',MAE='1.6',bias='0',within_1='0.4',within_2='0.8',under_score_count=2,over_score_count=2,zero_when_gold_positive=1,positive_when_gold_zero=1)


def test_multiple_engines_adjustments_reanalysis_and_rubric_denominators():
    rows=[dict(engine_mode=mode,suggested_score=str(a),human_decision_score='2',human_gold_score='2',adjustment=str(2-a),rubric_decisions=[],rubric_gold=[]) for mode,a in [('SPECIALIZED',1),('DYNAMIC',3)]]
    history=[dict(question_attempt_id='q',audit_run_id=str(i),engine_mode='SPECIALIZED',created_at=str(i),status='COMPLETED',review_required=False,technical_uncertainty=False,transcription_version_id=str(i),human_corrected_reading=i>1,suggested_score=str(i)) for i in (1,2)]
    m=metrics(rows,history,[dict(transcription_version_count=2,human_corrected=True)])
    assert set(m['by_engine_mode'])=={'SPECIALIZED','DYNAMIC'}
    assert m['by_engine_mode']['DYNAMIC']['confia_vs_gold']['bias']=='1'
    assert m['stages']['transcription']['correction_rate']=='1'
    assert m['stages']['reanalysis']['mean_score_change_after_reading_correction']=='1'
    assert m['stages']['human_adjustment']['upward_count']==m['stages']['human_adjustment']['downward_count']==1
    r=dict(rubric_decisions=[dict(rubric_item_id=str(i),suggested_points=a,max_points=2) for i,a in enumerate([1,1,0])],rubric_gold=[dict(rubric_item_id=str(i),gold_points=str(b),max_points='2') for i,b in enumerate([1,0,1])])
    rubric=rubric_metrics([r]);assert rubric['precision']==rubric['recall']=='0.5'
    assert rubric['false_positive_awards']==rubric['missed_awards']==1 and rubric['obligation_precision'] is None


def test_real_reading_reanalysis_invalidates_decision_and_preserves_events(shadow):
    from test_tme_review_workspace import revision
    from test_tme_question_audit import request_for, analyze
    ex,aid,url=shadow;client,root,eid,cases=ex;versions,runs,decisions=populate(ex)
    cid=cases[0]['case_id'];rev=revision(client,cid,versions[0]['transcription_id'],1,'[a]\n731 - 137 = 594').json()
    result=analyze(client,cid,request_for(client,cid,rev))
    data=get(client,url+'?selection=current')
    r=data['records'][0];assert r['audit_run_id']==result['audit_run_id'] and r['human_decision_id'] is None
    assert data['metrics']['stages']['reanalysis']['reanalyzed_questions']==1
    assert data['metrics']['stages']['reanalysis']['N_reading_change_pairs']==1
    assert data['metrics']['stages']['transcription']['human_corrected_questions']==1
    assert {'transcription_human_corrected','question_reanalysis_requested','confirmation_invalidated_by_transcription_change'}<={e['event_type'] for e in data['events']}


def test_observed_rubric_gold_partial_labels(shadow):
    ex,aid,url=shadow;client,root,eid,cases=ex;populate(ex)
    records=get(client,url+'?selection=current')['records'];item=records[0]['rubric_decisions'][0]
    body=payload(aid);body['rows'][0]['rubric_gold']=[dict(rubric_item_id=item['rubric_item_id'],max_points=item['max_points'],gold_points=0)]
    response=client.post(url+'/gold',json=body);assert response.status_code==201,response.text
    rubric=get(client,url+'?selection=current')['metrics']['rubric_awards']
    assert rubric['N_rubric_pairs']==1 and rubric['false_positive_awards']==1


def test_gold_concurrent_version_and_integrity(shadow):
    from concurrent.futures import ThreadPoolExecutor
    ex,aid,url=shadow;client,root,eid,cases=ex
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(client.post,url+'/gold',json=payload(aid,v)) for v in ['v1','v2']]
        assert sorted(f.result(timeout=20).status_code for f in futures)==[201,409]
    path=next((root/'tme_exams'/'.certification'/aid).glob('gold_*.json'))
    data=json.loads(path.read_text());data['data']['records'][0]['gold_score']='0';path.write_text(json.dumps(data))
    assert client.get(url).status_code==409


def test_owner_scope_size_and_csv_formula_guard(shadow,monkeypatch):
    from confia_lean_auditor.tme.certification import export_csv
    ex,aid,url=shadow;client,root,eid,cases=ex
    assert client.post(url+'/gold',content=b'x'*(2*1024*1024+1),headers={'Content-Type':'text/csv'}).status_code==413
    assert client.post(url+'/gold',content='x',headers={'Content-Type':'text/plain'}).status_code==415
    assert client.get(url+'?selection=anything').status_code==422
    data=get(client,url+'?selection=current');data['records'][0]['participant_code']='-unsafe'
    assert list(csv.DictReader(io.StringIO(export_csv(data))))[0]['participant_code']=="'-unsafe"
    from types import SimpleNamespace
    from confia_lean_auditor.tme.auth import require_tme_evaluator
    client.app.dependency_overrides[require_tme_evaluator]=lambda:SimpleNamespace(user_id='other')
    try:
        assert client.get(url).status_code==403
        assert client.post(url+'/gold',json=payload(aid)).status_code==403
    finally:client.app.dependency_overrides.pop(require_tme_evaluator,None)
