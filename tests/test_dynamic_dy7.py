"""DY7 research contracts over real shared exam, gold and audit records."""
from copy import deepcopy
from datetime import datetime,timezone
from decimal import Decimal
import pytest
from test_dynamic_dy6 import (setup,isolate_assessments,activity,add_question,activities,Revision,USER,receive,
    audit_question,reconciled_question,confirm_question)
from test_dynamic_dy3 import FACTOR
from confia_lean_auditor.tme import certification_runs as runs
from confia_lean_auditor.tme.certification_experiment_metrics import summarize,report,bootstrap_mae
from confia_lean_auditor.submissions.integrity import canonical_sha256


def api(client,url,body=None):
    r=client.get(url) if body is None else client.post(url,json=body)
    assert r.status_code in (200,201),r.text
    return r.json()


@pytest.fixture
def cohort(setup,monkeypatch):
    root,client=setup;monkeypatch.setenv('CONFIA_TME_CERTIFICATION_ENABLED','1')
    doc=add_question(activity());doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
    exam=receive(client,doc,[FACTOR]);case=exam['question_attempts'][0]
    aid=doc['assessment']['assessment_id'];url=f'/tme/assessments/{aid}/certification'
    history=api(client,f"/tme/cases/{case['case_id']}/transcriptions")[0]
    binding={k:case['dynamic_context'][k] for k in ('statement_version','statement_sha256','rubric_id','rubric_version','rubric_sha256')}
    binding.update(question_attempt_id=case['case_id'],transcription_version_id=history['transcription']['transcription_id']+':1')
    row=dict(assessment_id=aid,participant_code='S1',question_id=case['assessment_item_id'],gold_score='10',max_score='10',binding=binding,
        rubric_gold=[dict(rubric_item_id=k,gold_points=str(p),max_points=str(p)) for k,p in [('method',4),('roots',3),('check',3)]],
        evaluation=dict(evaluator_id='fixture-rater',evaluated_at=datetime.now(timezone.utc).isoformat(),blind=False,
            blindness_note='Synthetic contract fixture, not independent human research.',reference_kind='SYNTHETIC_FIXTURE',adjudication_status='SINGLE_RATER',requires_review=False,review_reason='Complete exact work'))
    payload=dict(source_id='fixture',dataset_version='gold1',expected_version=0,rows=[row])
    return root,client,url,doc,case,payload


def freeze_body(case):
    protocol='Synthetic contract test; frozen before any audit; no tuning.'
    return dict(dataset_version='dataset1',gold_version=1,protocol=protocol,protocol_sha256=canonical_sha256(protocol),cases=[dict(question_attempt_id=case['case_id'],split='HOLDOUT',group_id='group1',source_kind='SYNTHETIC',domain='algebra',solution_type='correct')])


def test_blind_gold_before_grading_no_automatic_human_gold_and_immutable_run(cohort,monkeypatch):
    root,client,url,doc,case,payload=cohort
    assert api(client,url+'?selection=current')['manifest']['gold'] is None
    api(client,url+'/gold',payload)
    frozen=api(client,url+'/datasets',freeze_body(case))
    assert api(client,url+'/datasets/'+frozen['id'])==frozen
    run=audit_question(client,case);rec=reconciled_question(client,case,run,monkeypatch);confirm_question(client,case,run,rec)
    before={p:p.read_bytes() for p in root.rglob('*.json')}
    result=api(client,url+'/runs',dict(dataset_id=frozen['id']))
    assert result['evaluation_mode']=='SHADOW_EVALUATION' and result['official_correction_affected'] is False
    assert result['metrics']['strata'][0]['metrics']['stages']['G0']['score']['MAE']=='0.0'
    assert set(result['records'][0]['dynamic_evaluation']['stages'])=={'G0','G1','G2','G3'}
    assert result['records'][0]['dynamic_evaluation']['stages']['G3']['score']=='10.0'
    assert all(p.read_bytes()==data for p,data in before.items())
    assert api(client,url+'/runs',dict(dataset_id=frozen['id']))==result
    assert client.post(url+'/runs',json=dict(dataset_id=frozen['id'],bootstrap_seed=12)).status_code==409
    # New gold cannot mutate the sealed result or the audit.
    newer=deepcopy(payload);newer.update(dataset_version='gold2',expected_version=1)
    newer['rows'][0]['gold_score']='9';newer['rows'][0]['rubric_gold'][0]['gold_points']='3'
    api(client,url+'/gold',newer)
    assert api(client,url+'/runs/'+result['id'])==result
    assert 'G2' in client.get(url+'/runs/'+result['id']+'/export.csv').text
    assert 'PILOT_METRICS_AVAILABLE' in client.get(url+'/runs/'+result['id']+'/report.md').text
    assert api(client,url+'/runs')[0]['id']==result['id']


@pytest.mark.parametrize('field,value,reason',[
    ('rubric_version',99,'RUBRIC_MISMATCH'),('statement_version',99,'STATEMENT_MISMATCH')])
def test_version_mismatch_excluded_from_all_metrics(cohort,field,value,reason):
    _,client,url,_,case,payload=cohort
    payload['rows'][0]['binding'][field]=value
    api(client,url+'/gold',payload);audit_question(client,case)
    data=api(client,url+'?selection=current')
    assert data['metrics']['confia_vs_gold']['N']==0
    assert reason in data['records'][0]['dynamic_evaluation']['exclusions']
    assert data['dynamic_metrics']['strata'][0]['metrics']['stages']['G0']['score']['N']==0
    assert client.post(url+'/datasets',json=freeze_body(case)).status_code==422


def test_holdout_cannot_be_relabelled_after_grading(cohort):
    _,client,url,_,case,payload=cohort
    api(client,url+'/gold',payload);audit_question(client,case)
    assert client.post(url+'/datasets',json=freeze_body(case)).status_code==422


def test_no_gold_from_decision_and_gold_requires_explicit_provenance(cohort,monkeypatch):
    _,client,url,_,case,payload=cohort
    grade=audit_question(client,case);rec=reconciled_question(client,case,grade,monkeypatch);confirm_question(client,case,grade,rec)
    data=api(client,url+'?selection=current')
    assert data['manifest']['gold'] is None and data['dynamic_metrics']['strata'][0]['metrics']['stages']['G3']['score']['N']==0
    del payload['rows'][0]['binding']
    assert client.post(url+'/gold',json=payload).status_code==422


def metric_row(g0='5',g1='3',g2='3',gold='3',review=False):
    def s(value):return dict(score=value,criteria=[dict(criterion_id='c',points=value,max_points='5')],review_required=review,status='COMPLETED',technical_failures=[])
    return dict(question_attempt_id='q',participant_id='p',max_score='5',human_gold_score=gold,
        rubric_gold=[dict(rubric_item_id='c',gold_points=gold,max_points='5')],
        dataset_case=dict(group_id='p',source_kind='SYNTHETIC',split='DEV',domain='algebra',solution_type='partial'),
        dynamic_evaluation=dict(policy_profile='FORMATIVE_LIST',stages=dict(G0=s(g0),G1=s(g1),G2=s(g2),G3=s(None)),
            exclusions=[],gold_evaluation=dict(requires_review=True,ratings=[]),feedback_eligible=False))


def test_metric_arithmetic_false_partial_credit_and_selective_risk():
    rows=[metric_row(),metric_row('0','2','2','4',True)]
    m=summarize(rows,Decimal('1'))
    g=m['stages']['G0'];assert g['score']['MAE']=='3' and g['score']['bias']=='-1'
    assert Decimal(g['score']['RMSE'])==Decimal(10).sqrt()
    assert g['criterion']['false_credit_count']==1 and g['criterion']['missed_credit_count']==1
    assert g['criterion']['over_credit_points']=='2' and g['criterion']['under_credit_points']=='4'
    assert g['automation_coverage']=='0.5' and g['unsafe_automation_rate']=='1'
    assert g['review_precision']=='1' and g['missed_escalation']==1
    assert m['reconciliation_value']['errors_corrected']==1
    assert m['reconciliation_value']['under_credit_points_recovered']=='2'
    assert m['uncertainty']['interval'] is None


def test_agreement_not_truth_technical_exclusions_and_origin_strata():
    r=metric_row('5','5','5','0');m=summarize([r])
    assert m['reviewer_value']['agree_but_gold_disagrees']==1 and m['reviewer_value']['grader_errors_missed']==1
    r['dynamic_evaluation']['stages']['G2']['technical_failures']=['PROVIDER_FAILURE']
    assert summarize([r])['stages']['G2']['score']['N']==0
    assert summarize([r])['technical_failure_cases']==1
    other=deepcopy(r);other['dataset_case']['source_kind']='REAL_STUDENT'
    assert len(report([r,other])['strata'])==2


def test_bootstrap_reproducible_only_with_sufficient_groups():
    rows=[]
    for i in range(20):
        r=metric_row(str(i%5));r['participant_id']=str(i);r['dataset_case']['group_id']=str(i);rows.append(r)
    assert bootstrap_mae(rows,'G0',9)==bootstrap_mae(rows,'G0',9)
    assert bootstrap_mae(rows,'G0',9)['interval'] is not None


def test_multirater_adjudication_and_no_inferred_blindness(cohort):
    _,client,url,_,case,payload=cohort
    e=payload['rows'][0]['evaluation'];now=e['evaluated_at']
    e.update(adjudication_status='ADJUDICATED',adjudication_reason='Independent resolution of a one-point difference',ratings=[dict(rater_id=k,score=score,blind=True,independent=True,evaluated_at=now) for k,score in [('A','10'),('B','9')]])
    api(client,url+'/gold',payload);audit_question(client,case)
    result=api(client,url+'?selection=current')['dynamic_metrics']['strata'][0]['metrics']['inter_rater']
    assert result['N_pairs']==1 and result['MAE']=='1' and result['exact_agreement']=='0'


def test_gold_transcription_revision_mismatch_preserves_old_reference(cohort):
    _,client,url,_,case,payload=cohort
    api(client,url+'/gold',payload);run=audit_question(client,case)
    base=f"/tme/cases/{case['case_id']}/transcriptions/{run['transcription_id']}"
    api(client,base+'/revisions',dict(based_on_revision_number=1,change_reason='New reading',segments=[dict(segment_id='text:0',page_index=0,order=0,kind='text',text='y=9')]))
    audit_question(client,case)
    data=api(client,url+'?selection=current');r=data['records'][0]
    assert 'TRANSCRIPTION_MISMATCH' in r['dynamic_evaluation']['exclusions'] and r['human_gold_score'] is None
    assert api(client,url+'/gold?version=1')['records'][0]['binding']==payload['rows'][0]['binding']


def test_freeze_preserves_splits_and_requires_frozen_code(cohort,monkeypatch):
    _,client,url,_,case,payload=cohort
    api(client,url+'/gold',payload);frozen=api(client,url+'/datasets',freeze_body(case))
    altered=freeze_body(case);altered['cases'][0]['split']='DEV'
    assert client.post(url+'/datasets',json=altered).status_code==409
    monkeypatch.setattr(runs.cert,'code_version',lambda:dict(application_sha256='changed'))
    assert client.post(url+'/runs',json=dict(dataset_id=frozen['id'])).status_code==409


def test_experimental_gates_do_not_imply_certification():
    m=report([metric_row()]);g=dict(label='test-only',profile='FORMATIVE_LIST',split='DEV',source_kind='SYNTHETIC',min_n=1,max_mae='0')
    assert runs.gate_verdict(m,g)['status']=='GATE_MET_FOR_DEFINED_PROFILE'
    g['min_n']=2;assert runs.gate_verdict(m,g)['status']=='INSUFFICIENT_EVIDENCE'
    g['min_n']=1;g['max_mae']='0';m=report([metric_row(g2='1')])
    assert runs.gate_verdict(m,g)['status']=='GATE_NOT_MET'


def test_paired_metrics_separate_arms_and_shared_gold():
    from confia_lean_auditor.tme.certification_paired import paired_metrics
    rows=[dict(gold_score='4',dynamic_score='4',specialized_score='3',dynamic_review_required=False,specialized_review_required=True,exclusions=[]),
        dict(gold_score='4',dynamic_score='2',specialized_score='4',dynamic_review_required=True,specialized_review_required=False,exclusions=[]),
        dict(exclusions=['RUBRIC_MISMATCH'])]
    m=paired_metrics(rows)
    assert m['N']==2 and m['dynamic_better']==m['specialized_better']==1 and m['mean_absolute_error_delta_dynamic_minus_specialized']=='0.5'
    assert m['N_criterion_aligned']==0 and m['false_credit_count_difference'] is None


def test_real_specialized_arm_rejects_unmatched_problem_and_maximum(cohort,monkeypatch):
    _,client,url,_,case,payload=cohort
    monkeypatch.setenv('CONFIA_TME_QUESTION_USE_LEAN','0')
    api(client,url+'/gold',payload);frozen=api(client,url+'/datasets',freeze_body(case))
    grade=audit_question(client,case);reconciled_question(client,case,grade,monkeypatch)
    run=api(client,url+'/runs',dict(dataset_id=frozen['id']))
    spec=api(client,'/tme/assessments',dict(title='Specialized comparison',academic_year=2026,items=[dict(problem_id='TME2026P1',points=20)]))
    from test_tme_full_exam import package,pdf,receive as capture
    from test_tme_question_audit import reading,request_for,analyze
    body=package(client,pdf(1));body['assessment_identifier']=spec['assessment']['assessment_id']
    exam=capture(client,body);sc=exam['question_attempts'][0]
    r=client.put(f"/tme/exam-submissions/{exam['submission']['submission_id']}/page-mapping",json=dict(expected_version=1,bindings=[dict(question_attempt_id=sc['case_id'],exam_page_id=exam['submission']['pages'][0]['exam_page_id'],order=1)]))
    assert r.status_code==200,r.text
    rev,_=reading(client,sc['case_id'],1,FACTOR);sr=analyze(client,sc['case_id'],request_for(client,sc['case_id'],rev))
    response=api(client,url+'/comparisons',dict(dynamic_run_id=run['id'],experiment='END_TO_END',preparation_difference_note='Separate natural preparation for each arm; explicit non-comparable test.',pairs=[dict(dynamic_question_attempt_id=case['case_id'],specialized_question_attempt_id=sc['case_id'],specialized_audit_run_id=sr['audit_run_id'],alignment_justification='Different problems deliberately rejected by the adapter.')]))
    assert response['metrics']['N']==0
    assert 'STATEMENT_MISMATCH' in response['pairs'][0]['exclusions'] and 'MAXIMUM_MISMATCH' in response['pairs'][0]['exclusions']
    assert api(client,url+'/comparisons/'+response['id'])==response


def test_partial_reviewer_criteria_are_measured_without_fabricated_total():
    r=metric_row();r['dynamic_evaluation']['stages']['G1']['score']=None
    m=summarize([r])['stages']['G1']
    assert m['score']['N']==0 and m['criterion']['N']==1 and m['criterion']['exact_agreement']=='1'


def test_unresolved_criterion_gold_is_not_counted():
    r=metric_row();r['rubric_gold'][0]['adjudication_status']='UNRESOLVED'
    assert summarize([r])['stages']['G0']['criterion']['N']==0


def test_dataset_duplicate_response_across_splits_rejected(cohort):
    _,client,url,doc,case,payload=cohort
    second=receive(client,doc,[FACTOR],'S2')['question_attempts'][0]
    history=api(client,f"/tme/cases/{second['case_id']}/transcriptions")[0]
    row=deepcopy(payload['rows'][0]);row['participant_code']='S2';row['binding'].update(question_attempt_id=second['case_id'],transcription_version_id=history['transcription']['transcription_id']+':1')
    payload['rows'].append(row);api(client,url+'/gold',payload)
    body=freeze_body(case);body['cases'].append(dict(body['cases'][0],question_attempt_id=second['case_id'],split='DEV',group_id='group2'))
    assert client.post(url+'/datasets',json=body).status_code==422


def test_run_tamper_detected_and_dataset_retry_is_idempotent(cohort,monkeypatch):
    import json
    root,client,url,doc,case,payload=cohort
    api(client,url+'/gold',payload);body=freeze_body(case);frozen=api(client,url+'/datasets',body)
    grade=audit_question(client,case);reconciled_question(client,case,grade,monkeypatch)
    assert api(client,url+'/datasets',body)==frozen
    result=api(client,url+'/runs',dict(dataset_id=frozen['id']))
    p=runs.path(doc['assessment']['assessment_id'],result['id']);raw=json.loads(p.read_text());raw['data']['records'][0]['human_gold_score']='0';p.write_text(json.dumps(raw))
    assert client.get(url+'/runs/'+result['id']).status_code==409



def test_agreement_wrong_at_criterion_level_even_with_exact_total():
    r=metric_row('3','3','3','3')
    r['rubric_gold']=[dict(rubric_item_id='a',gold_points='2',max_points='3'),dict(rubric_item_id='b',gold_points='1',max_points='2')]
    for s in r['dynamic_evaluation']['stages'].values():s['criteria']=[dict(criterion_id='a',points='1',max_points='3'),dict(criterion_id='b',points='2',max_points='2')]
    m=summarize([r]);assert m['reviewer_value']['agree_but_gold_disagrees']==1
    assert m['stages']['G0']['score']['MAE']=='0' and m['stages']['G0']['criterion']['false_credit_count']==1



def test_holdout_rejects_configuration_drift(cohort,monkeypatch):
    _,client,url,_,case,payload=cohort
    api(client,url+'/gold',payload);frozen=api(client,url+'/datasets',freeze_body(case))
    monkeypatch.setenv('CONFIA_DYNAMIC_REVIEWER_MODEL','different-experiment-model')
    assert client.post(url+'/runs',json=dict(dataset_id=frozen['id'])).status_code==409
