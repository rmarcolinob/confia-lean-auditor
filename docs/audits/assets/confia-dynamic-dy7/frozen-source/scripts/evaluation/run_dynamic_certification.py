#!/usr/bin/env python3
"""Run a predeclared textual benchmark through the real shared Dynamic lifecycle.

Requires a NEW isolated storage directory. Default providers are explicitly
synthetic, deterministic fixtures; they never receive gold labels. --live uses
the configured DY2/DY4 providers and must be reported as a separate experiment.
No IDs, grading heuristics, policies or gold are inferred from observed scores.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))


def configure(root):
    if root.exists() and any(root.iterdir()):raise ValueError('benchmark storage must be a new empty directory')
    root.mkdir(parents=True,exist_ok=True)
    for name in ('DYNAMIC','TME_CASES','SUBMISSIONS','SUBMISSION_AUDITS','TME_EXAMS','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','AUTH','INSTITUTIONAL'):
        os.environ[f'CONFIA_{name}_DIR']=str(root/name.lower())
    os.environ.update(CONFIA_AUTH_ENABLED='0',CONFIA_TME_DEMO_NO_AUTH='1',CONFIA_DYNAMIC_DEMO_ENABLED='1',CONFIA_TME_CERTIFICATION_ENABLED='1',CONFIA_ENV='test')


def metadata(payload,raw,schema,operation):
    from confia_lean_auditor.dynamic.preparation_models import GenerationProvenance
    from confia_lean_auditor.submissions.integrity import canonical_sha256
    return GenerationProvenance(provider='synthetic-dy7-fixture',requested_model='not-an-LLM',returned_model='fixture.v1',reasoning_effort=None,
        prompt_version='dy7-fixture:'+operation,schema_version=schema.__name__+'.v1',input_sha256=canonical_sha256(payload),
        output_sha256=canonical_sha256(json.dumps(raw,ensure_ascii=False)),response_id=None,created_at=datetime.now(timezone.utc),code_sha=None,max_output_tokens=10000,raw_output=json.dumps(raw,ensure_ascii=False))


class PreparationFixture:
    def __init__(self,problem):self.problem=problem
    def generate(self,operation,payload,schema):
        if operation=='prepare':raw=self.problem['preparation_fixture']
        elif operation=='rubric':raw=dict(max_score=self.problem['max_score'],criteria=self.problem['criteria'],warnings=[])
        else:raw=dict(warnings=[],overlap_detected=False,vague_criteria=False,impossible_dependency=False,absent_information_required=False,unjustified_single_strategy=False,rationale='Synthetic rubric protocol; no scientific human approval claimed.')
        return schema.model_validate(raw),metadata(payload,raw,schema,operation)


class ReviewFixture:
    def generate(self,payload,schema):
        # Intentionally overconfident fixture: proposes full credit from all independently
        # extracted claims. DY4 checks and DY5 policy decide whether any credit is usable.
        # Does not inspect gold, G0, case IDs, split or benchmark expected outcomes.
        refs=[c['claim_id'] for c in payload['mathematical_evidence']]
        raw=dict(detected_strategy='Synthetic all-evidence proposal',alternative_strategy='sqrt' in payload['solution'],additional_claims=[],warnings=[],
            criterion_reviews=[dict(criterion_id=c['criterion_id'],assessment='COMPLETE',proposed_points=c['max_points'],claim_ids=refs,
                explanation='Controlled maximal proposal, subject to independent evidence checks.',uncertainty=[]) for c in payload['approved_rubric']['criteria']])
        return schema.model_validate(raw),metadata(payload,raw,schema,'review')


def request(client,method,url,body=None):
    result=client.request(method,url,json=body)
    if result.status_code not in (200,201):raise RuntimeError(f'{method} {url}: {result.status_code} {result.text[:500]}')
    return result.json()


def execute(dataset_path,storage,output,live=False):
    spec=json.loads(dataset_path.read_text());spec_sha=hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    configure(storage);output.mkdir(parents=True,exist_ok=True)
    from fastapi.testclient import TestClient
    from confia_lean_auditor.main import app
    from confia_lean_auditor.dynamic.models import Actor,CreateProblem,PreparationRequest,SuggestionRequest,ApproveRubric,SaveRubric
    from confia_lean_auditor.dynamic.preparation import PreparationService
    from confia_lean_auditor.dynamic.store import dynamic_store
    from confia_lean_auditor.dynamic.review_service import DynamicReviewService
    from confia_lean_auditor.dynamic.provider import provider_available
    from confia_lean_auditor.dynamic.review_provider import reviewer_available
    from confia_lean_auditor.dynamic import router
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.submissions.integrity import canonical_sha256
    from confia_lean_auditor.tme import certification_runs
    actor=Actor(actor_id='technical-demo:dynamic',kind='TECHNICAL_DEMO')
    if live and not (provider_available() and reviewer_available()):raise ValueError('Live preparation/reviewer are not configured')
    # External spec bytes and review fixture code are frozen before ANY attempt runs.
    freeze_record=dict(spec_sha256=spec_sha,harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       frozen_at=datetime.now(timezone.utc).isoformat(),live=live,dataset_version=spec['dataset_version'])
    (output/'protocol-freeze.json').write_text(json.dumps(freeze_record,indent=2))
    with ExitStack() as stack:
        client=stack.enter_context(TestClient(app))
        if not live:stack.enter_context(patch.object(router,'independent_review_service',lambda:DynamicReviewService(service(),ReviewFixture())))
        pending=[];all_runs=[]
        for profile in spec['profiles']:
            doc=request(client,'POST','/dynamic/assessments',dict(title=f"DY7 {spec['dataset_version']} {profile}",policy_profile=profile,feedback_policy='AFTER_CONFIRMATION'))
            aid=doc['assessment']['assessment_id'];base=f'/dynamic/assessments/{aid}'
            for p in spec['problems']:
                store=dynamic_store();problem=store.create(CreateProblem(title=p['title'],statement=p['statement'],max_score=p['max_score'],correction_mode='DYNAMIC'),actor)
                prep=PreparationService(store) if live else PreparationService(store,PreparationFixture(p))
                pid=problem['problem']['problem_id'];problem=prep.start(pid,PreparationRequest(expected_revision=problem['revision']),actor)
                problem=prep.suggest(pid,SuggestionRequest(expected_revision=problem['revision'],preparation_id=problem['current_preparation']['preparation_id']),actor)
                if live:
                    # Fixed protocol rubric, recorded as a demo edit. A live proposal is
                    # never allowed to silently redefine the already-authored gold.
                    problem=store.save_rubric(pid,SaveRubric(expected_revision=problem['revision'],statement_version=1,max_score=p['max_score'],criteria=p['criteria']),actor,base_id=problem['rubrics'][-1]['rubric_id'])
                # This is fixture approval, explicitly recorded as TECHNICAL_DEMO.
                store.approve(pid,problem['rubrics'][-1]['rubric_id'],ApproveRubric(expected_revision=problem['revision'],acknowledge_warnings=True),actor)
                doc=request(client,'POST',base+'/questions',dict(expected_revision=doc['dynamic_revision'],problem_id=pid))
            doc=request(client,'POST',base+'/activate',dict(expected_revision=doc['dynamic_revision']))
            gold_rows=[];registered=[];attempts=[]
            for participant in spec['participants']:
                exam=request(client,'POST','/tme/exam-submissions/text',dict(assessment_identifier=aid,external_participant_code=participant['code'],
                    idempotency_key=profile+':'+participant['code'],solutions=[s['text'] for s in participant['solutions']]))
                for i,(case,solution) in enumerate(zip(exam['question_attempts'],participant['solutions'])):
                    cid=case['case_id'];history=request(client,'GET',f'/tme/cases/{cid}/transcriptions')[0]
                    tid=history['transcription']['transcription_id'];revision=history['latest_revision']['revision_number']
                    accepted=request(client,'POST',f'/tme/cases/{cid}/transcriptions/{tid}/accept',dict(revision_number=revision))
                    context=case['dynamic_context'];binding={k:context[k] for k in ('statement_version','statement_sha256','rubric_id','rubric_version','rubric_sha256')}
                    binding.update(question_attempt_id=cid,transcription_version_id=f'{tid}:{revision}')
                    p=spec['problems'][i];gold_points=solution['gold_criteria']
                    gold_rows.append(dict(assessment_id=aid,participant_code=participant['code'],question_id=case['assessment_item_id'],
                        max_score=p['max_score'],gold_score=str(sum(map(Decimal,gold_points.values()))),binding=binding,
                        rubric_gold=[dict(rubric_item_id=c['criterion_id'],gold_points=gold_points[c['criterion_id']],max_points=c['max_points']) for c in p['criteria']],
                        evaluation=dict(evaluator_id='synthetic-protocol-author',evaluated_at=freeze_record['frozen_at'],blind=False,
                            blindness_note='Synthetic author saw fixture definitions; labels fixed before outputs. Not an independent human study.',
                            reference_kind='SYNTHETIC_FIXTURE',adjudication_status='SINGLE_RATER',requires_review=solution['requires_review'],review_reason=solution['review_reason'])))
                    registered.append(dict(question_attempt_id=cid,split=participant['split'],group_id=participant['group_id'],source_kind='SYNTHETIC',
                        domain=p['domain'],difficulty=p['difficulty'],difficulty_basis=p.get('difficulty_basis','UNSPECIFIED'),solution_type=solution['type']))
                    attempts.append(dict(case=case,request=dict(transcription_id=tid,revision_number=revision,acceptance_id=accepted['acceptance']['acceptance_id'],execution_key='dy7-grade'),human_points=solution.get('human_points')))
            certbase=f'/tme/assessments/{aid}/certification'
            request(client,'POST',certbase+'/gold',dict(source_id='dy7-controlled-protocol',dataset_version=spec['dataset_version'],expected_version=0,rows=gold_rows))
            protocol=spec['protocol']+' | spec_sha256='+spec_sha+' | harness_sha256='+freeze_record['harness_sha256']
            frozen=request(client,'POST',certbase+'/datasets',dict(dataset_version=spec['dataset_version'],gold_version=1,protocol=protocol,protocol_sha256=canonical_sha256(protocol),cases=registered,material_error_points=spec['material_error_points']))
            pending.append((profile,certbase,frozen,attempts))
        # Every profile/participant/split has now been registered before any grading.
        for profile,certbase,frozen,attempts in pending:
            for item in attempts:
                case=item['case'];cid=case['case_id']
                grade=request(client,'POST',f'/tme/cases/{cid}/audits',item['request'])
                if grade['status']!='COMPLETED':continue
                auditbase=f"/dynamic/attempts/{cid}/audits/{grade['audit_run_id']}"
                review=request(client,'POST',auditbase+'/independent-reviews',dict(execution_key='dy7-review'))['review']
                if review['status']!='COMPLETED':continue
                rec=request(client,'POST',auditbase+'/reconciliations',dict(independent_review_id=review['review_id']))['reconciliation']
                if item['human_points'] is not None:
                    request(client,'POST',f'/tme/cases/{cid}/decision',dict(audit_run_id=grade['audit_run_id'],transcription_version_id=grade['transcription_version_id'],
                        reconciliation_id=rec['reconciliation_id'],decision_type='ADJUST_SCORE',final_points=item['human_points'],
                        override_reason='Synthetic operational decision predeclared separately from gold.',execution_key='dy7-human'))
            for eid in sorted({item['case']['exam_submission_id'] for item in attempts}):
                summary=request(client,'GET',f'/tme/exam-submissions/{eid}/correction')
                if summary['ready_to_finalize']:
                    request(client,'POST',f'/tme/exam-submissions/{eid}/correction/finalize',dict(expected_snapshot_sha256=summary['snapshot_sha256'],execution_key='dy7-final'))
            result=request(client,'POST',certbase+'/runs',dict(dataset_id=frozen['id']))
            all_runs.append(result)
            (output/(profile+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
            (output/(profile+'.csv')).write_text(certification_runs.export_csv(result))
            (output/(profile+'.md')).write_text(certification_runs.markdown(result))
        (output/'index.json').write_text(json.dumps(dict(**freeze_record,runs=[dict(id=r['id'],assessment_id=r['assessment_id'],verdict=r['verdict']) for r in all_runs]),indent=2))
    return all_runs


if __name__=='__main__':
    from decimal import Decimal
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dataset',type=Path,required=True);parser.add_argument('--storage',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--live',action='store_true')
    args=parser.parse_args();result=execute(args.dataset,args.storage,args.output,args.live)
    print(json.dumps([dict(id=r['id'],N=r['metrics']['N'],verdict=r['verdict']['status']) for r in result],indent=2))
