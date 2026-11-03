"""Methodological invariants: one schema, adapter, gate, rubric and score."""
from __future__ import annotations

import ast
from dataclasses import asdict, replace
import importlib
import inspect
import json

import pytest
from confia_lean_auditor.semantic.evidence_unit import EvidenceUnit, from_historical_claim, from_semantic_claim
from confia_lean_auditor.semantic.semantic_student_claim import SemanticStudentClaim, CONTRACTS
from confia_lean_auditor.semantic.semantic_claim_adapter import adapt_claim, evidence_bridge
from confia_lean_auditor.student_claims.schemas import StudentClaim
from confia_lean_auditor.evaluation.formal_award_gate import formal_award_gate, final_score, AWARD_POLICY
from confia_lean_auditor.evaluation.semantic_formal_b import evaluate_mode, evaluate_evidence
from confia_lean_auditor.evaluation.structural_metrics import case_metrics, aggregate_metrics
from test_semantic_formal_b import evidence, check, assets, ROOT, PAYLOADS, pid, raw
from confia_lean_auditor.semantic.semantic_extractor_v2 import parse_response


def decide(evs, checks):
    problem = pid(evs[0].claim_type)
    extraction = evidence_bridge(ROOT, problem, evs, checks)
    return formal_award_gate(problem, evs, checks, extraction=extraction,
                             rubric_config=assets(problem).rubric)


def decisions_only(decisions):
    # Audit labels are expected to differ; predicates and awards must not.
    return [{k: d[k] for k in ('rubric_item_id','gate_decision','award','max_points',
        'rejection_reason','obligation_satisfied','eligible_evidence_ids','failed_check_ids')}
        for d in decisions]


@pytest.mark.parametrize('kind', sorted(CONTRACTS))
@pytest.mark.parametrize('status', ['verified', 'failed', 'unsupported', 'error'])
@pytest.mark.parametrize('context', [dict(), {'scope':'exploration'}, {'hypothetical':True}])
def test_gate_invariant_to_mode_and_policy_labels(kind, status, context):
    semantic = evidence(kind, **context)
    historical = semantic.model_copy(update={'extractor_mode':'FORMAL_OFFLINE',
        'context_policy':'legacy_context_assumed', 'source_span':None,
        'provenance_limitations':['source_span_unavailable']})
    assert type(semantic) is type(historical) is EvidenceUnit
    checks = [check(semantic,status)]
    a, da = decide([semantic],checks)
    b, db = decide([historical],checks)
    assert a.score == b.score
    assert [i.points for i in a.items] == [i.points for i in b.items]
    assert decisions_only(da) == decisions_only(db)
    assert [i.max_points for i in a.items] == [i.points for i in assets(pid(kind)).rubric.items]
    assert [i.max_points for i in b.items] == [i.max_points for i in a.items]


def test_identical_evidence_has_identical_full_gate_decision():
    unit = evidence()
    units, checks = [unit], [check(unit)]
    offline_result = decide(units, checks)
    semantic_result = decide(units, checks)
    assert offline_result == semantic_result
    assert offline_result[0].score == 2.0


def test_gate_and_shared_pipeline_have_no_mode_dependent_branch():
    assert 'mode' not in inspect.signature(formal_award_gate).parameters
    assert 'mode' not in inspect.signature(evaluate_evidence).parameters
    for function in (formal_award_gate, final_score, evaluate_evidence, evidence_bridge,
                     EvidenceUnit.eligible_context, adapt_claim):
        tree = ast.parse(inspect.getsource(function).strip())
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id not in {'extractor_mode', 'mode', 'context_policy'}
            if isinstance(node, ast.Attribute):
                assert node.attr not in {'extractor_mode', 'context_policy'}
        assert 'FORMAL_OFFLINE' not in inspect.getsource(function)
        assert 'SEMANTIC_FORMAL' not in inspect.getsource(function)
    common = inspect.getsource(evaluate_evidence)
    assert 'evaluate_rubric' not in common and 'apply_student_claim_adjustments' not in common


@pytest.mark.parametrize('kind', sorted(CONTRACTS))
def test_both_converters_feed_same_adapter_and_historical_builder(kind):
    semantic = evidence(kind)
    legacy = StudentClaim(id=semantic.evidence_id, problem_id=pid(kind), claim_type=kind,
        raw_text=semantic.source_span, normalized_text='legacy', context='legacy',
        data=dict(PAYLOADS[kind], formula_text='unused provenance'))
    historical = from_historical_claim(legacy,pid(kind),semantic.source_span)
    assert type(historical) is type(semantic) is EvidenceUnit
    assert historical.context_policy == 'legacy_context_assumed'
    assert (historical.assertion_status,historical.polarity,historical.scope,
            historical.hypothetical,historical.abandoned) == ('asserted','positive','main_argument',False,False)
    assert historical.raw_extractor_metadata['context_is_inferred'] is False
    a = adapt_claim(semantic,pid(kind),semantic.source_span)
    b = adapt_claim(historical,pid(kind),semantic.source_span)
    assert asdict(a) == asdict(b)
    q=kind.split('_')[0]
    module=importlib.import_module('confia_lean_auditor.lean.student_claim_checkers.ita2025'+q)
    build=getattr(module,'_lean_statement_and_method_for_'+q+'_claim')
    assert build(a) == build(b)


def test_unanchored_llm_rejected_before_common_pipeline():
    unit = evidence().model_copy(update={'source_span':None})
    with pytest.raises(ValueError):
        from_semantic_claim(unit,'ITA2025F2Q5','O primeiro algarismo é 5.')
    with pytest.raises(ValueError):
        parse_response({'claims':[raw(text=None)]},'ITA2025F2Q5','texto','fake')
    # LLM cannot submit provenance labels to opt out of its boundary validation.
    with pytest.raises(ValueError):
        parse_response({'claims':[dict(raw(),extractor_mode='FORMAL_OFFLINE')]},
                       'ITA2025F2Q5',raw()['source_span'],'fake')


def test_absent_legacy_span_only_changes_provenance():
    ev = evidence()
    legacy = StudentClaim(id=ev.evidence_id,problem_id='ITA2025F2Q5',claim_type=ev.claim_type,
        raw_text='primeiro algarismo = 5',normalized_text='digit=5',context='legacy',data={'digit':5})
    unit=from_historical_claim(legacy,'ITA2025F2Q5',ev.source_span)
    assert unit.source_span is None
    assert unit.provenance_limitations == ['source_span_unavailable']
    a, da=decide([unit],[check(ev)])
    b, db=decide([ev],[check(ev)])
    assert a.score == b.score == 2.0
    assert decisions_only(da) == decisions_only(db)


def test_duplicate_claims_never_double_count_and_duplicate_ids_rejected():
    a=evidence()
    b=a.model_copy(update={'evidence_id':'second'})
    result, decisions=decide([a,b],[check(a),check(b)])
    assert result.score == 2.0
    assert decisions[-1]['used_evidence_ids'] == [a.evidence_id,b.evidence_id]
    with pytest.raises(ValueError,match='Duplicate evidence_id'):
        decide([a,a],[check(a)])
    with pytest.raises(ValueError,match='Duplicate rubric item'):
        final_score([result.items[-1],result.items[-1]])


def test_gate_is_pure_no_gold_or_other_file_access(monkeypatch):
    ev=evidence()
    checks=[check(ev)]
    cfg=assets('ITA2025F2Q5').rubric
    extraction=evidence_bridge(ROOT,'ITA2025F2Q5',[ev],checks)
    def deny(*args,**kwargs):
        raise AssertionError('Gate tried to open a file')
    monkeypatch.setattr('builtins.open',deny)
    monkeypatch.setattr('io.open',deny)
    result, _=formal_award_gate('ITA2025F2Q5',[ev],checks,extraction=extraction,rubric_config=cfg)
    assert result.score == 2.0


def test_per_item_audit_and_conflicting_evidence():
    good=evidence()
    bad=good.model_copy(update={'evidence_id':'failed-claim','normalized_payload':{'digit':6}})
    result, decisions=decide([good,bad],[check(good),check(bad,'failed')])
    final=decisions[-1]
    assert final['gate_decision']=='reject' and final['award']==0.0
    assert final['rejection_reason']=='conflicting_failed'
    assert final['conflicting_evidence'][0]['evidence_id']=='failed-claim'
    assert final['evidence'][0]['lean_status']=='verified'
    for item in final['evidence']:
        assert {'evidence_id','claim_type','extractor_mode','context_policy','lean_status'} <= set(item)
    assert final['used_evidence_ids']==[]


def test_common_pipeline_routes_both_modes_through_same_objects(tmp_path,monkeypatch):
    module=importlib.import_module('confia_lean_auditor.evaluation.semantic_formal_b')
    text='O primeiro algarismo é 5.'
    observed=[]
    real_adapter=module.adapt_claim
    def adapter(unit,*args):
        observed.append(unit)
        return real_adapter(unit,*args)
    def checks(root,out,problem,claims):
        return [replace(check(evidence()),id=c.id,data=c.data,raw_text=c.raw_text) for c in claims]
    monkeypatch.setattr(module,'adapt_claim',adapter)
    monkeypatch.setattr(module,'run_checks',checks)
    monkeypatch.setattr(module,'run_formal_chain',lambda *a: ([],{'certificate':{'status':'verified'},'formal_steps':[]}))
    sem=parse_response({'claims':[raw(text=text)]},'ITA2025F2Q5',text,'fake')
    a=evaluate_mode(ROOT,tmp_path/'offline','ITA2025F2Q5',text,'FORMAL_OFFLINE')
    b=evaluate_mode(ROOT,tmp_path/'semantic','ITA2025F2Q5',text,'SEMANTIC_FORMAL',sem)
    assert len(observed)==2 and all(type(e) is EvidenceUnit for e in observed)
    assert a['score']==b['score']==2.0
    assert a['award_policy']==b['award_policy']==AWARD_POLICY
    assert observed[0].source_span is None
    assert [i['max_points'] for i in a['rubric_items']] == [i['max_points'] for i in b['rubric_items']]


def test_structural_metrics_count_claims_items_and_fallbacks():
    row={'score':2.0,'fallback_used':True,'extracted_evidence':[{}, {}, {}],
        'student_claim_checks':[{'status':'verified','lean_file':'a.lean'},
            {'status':'failed','lean_file':'b.lean'},{'status':'unsupported','lean_file':None}],
        'rubric_items':[{'points':2},{'points':0},{'points':0}],
        'formal_award_decisions':[{'evidence':[{}],'rejection_reason':None},
            {'evidence':[{}],'rejection_reason':'context_rejected'},
            {'evidence':[],'rejection_reason':'formal_obligation_not_satisfied'}]}
    metrics=case_metrics(row)
    assert metrics=={'claims_extracted':3,'claims_submitted_to_checker':3,'claims_sent_to_lean':2,
        'verified':1,'failed':1,'rubric_items_with_evidence':2,'items_scored':1,
        'items_rejected_for_context':1,'items_rejected_for_insufficiency':1,
        'items_rejected_for_conflict':0,'fallbacks':1,'numeric_scores':1}
    assert aggregate_metrics([row,row])=={k:2*v for k,v in metrics.items()}
    assert case_metrics({'score':None})['numeric_scores']==0
