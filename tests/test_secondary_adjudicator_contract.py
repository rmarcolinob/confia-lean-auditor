"""Rubric-bounded decisions with fake responses; never contacts a provider."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from tests.secondary_selection_helpers import selection

from confia_lean_auditor.rubric import secondary_adjudicator as secondary
from confia_lean_auditor.rubric.secondary_context import prepare_payload
from confia_lean_auditor.rubric.scoring_policy import apply_scoring_policy
from confia_lean_auditor.core.problem_assets import validate_problem_assets
from confia_lean_auditor.core.schemas import ClaimExtraction, RubricAssessment, RubricItemResult

ROOT=Path(__file__).resolve().parents[1]


def payload(max_points=2):
    return {"solution_text":"Logo a=-1 e b=3.", "pending_criteria":[{
        "id":"final_answer", "description":"Conclui corretamente a=-1 e b=3.",
        "max_points":max_points, "allowed_points":[0,max_points], "input_status":"indeterminate"}]}


def decision(p, kind="award"):
    return {c["id"]:{"decision":kind, "suggested_points":c["max_points"] if kind=="award" else 0,
        "evidence":[p["solution_text"][:800]], "rationale":secondary.rationale_options(c)[kind][0]}
        for c in p["pending_criteria"]}


def fake_client(monkeypatch, replies):
    import openai
    seen=[];config=[]
    class Client:
        def __init__(self, **kwargs):config.append(kwargs);self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kwargs):
            seen.append(kwargs)
            reply=replies[len(seen)-1]
            if isinstance(reply,Exception):raise reply
            if callable(reply):reply=reply(kwargs)
            if isinstance(reply,SimpleNamespace):return reply
            return SimpleNamespace(status="completed",output_text=json.dumps(reply) if isinstance(reply,dict) else reply,
                id="fake-response",model="fake-resolved-model")
    monkeypatch.setenv("OPENAI_API_KEY","unit-test-not-a-real-key")
    monkeypatch.setattr(openai,"OpenAI",Client)
    return seen,config


@pytest.mark.parametrize("points",[1,2,3])
@pytest.mark.parametrize("kind",["award","deny"])
def test_valid_contract_and_strict_schema(monkeypatch,points,kind):
    p=payload(points);expected=selection(p,kind);seen,config=fake_client(monkeypatch,[expected])
    actual,meta=secondary.adjudicate(p)
    assert {k:{f:v for f,v in d.items() if f!='evidence'} for k,d in actual.items()}==expected and len(seen)==1 and config==[{"timeout":45.0,"max_retries":0}]
    call=seen[0];schema=call["text"]["format"]["schema"];item=next(b for b in schema["properties"]["final_answer"]["anyOf"] if b["properties"]["decision"]["enum"]==[kind] and b["properties"]["reason_code"]["enum"]==[expected["final_answer"]["reason_code"]])
    assert call["store"] is False and call["temperature"]==0 and call["text"]["format"]["strict"]
    assert schema["additionalProperties"] is False and item["additionalProperties"] is False
    assert set(item["required"])==set(expected["final_answer"])
    assert item["properties"]["suggested_points"]["enum"]==([points] if kind=="award" else [0])
    assert meta["criteria"][0]["decision"]==kind and meta["validation_status"]=="accepted"
    assert meta["schema_version"] and meta["prompt_version"] and meta["resolved_model"]=="fake-resolved-model"


@pytest.mark.parametrize("value",[.5,1.5,-1,3,True,"2",float('nan'),float('inf'),10**1000])
def test_only_permitted_numeric_points(value):
    p=payload();d=decision(p);d["final_answer"]["suggested_points"]=value
    with pytest.raises(secondary.AdjudicationError) as caught:secondary.validate_decisions(d,p)
    assert caught.value.code=="ADJUDICATOR_INVALID_POINTS"


@pytest.mark.parametrize("field,value,category",[
    ("evidence",["Trecho inexistente"],"invalid_evidence"),
    ("evidence",[],"invalid_evidence"),("evidence","Logo a=-1 e b=3.","invalid_evidence"),
    ("rationale"," ","missing_rationale"),("decision","maybe","invalid_enum"),
    ("decision","deny","decision_points_conflict"),
    ("rationale","Embora os valores finais estejam corretos, a resposta é muito vaga e não apresenta uma conclusão formal.","unauthorized_rationale"),
    ("rationale","Falta uma prova completa e um passo adicional.","unauthorized_rationale")])
def test_local_validation_rejects_invalid_or_invented_content(field,value,category):
    p=payload();d=decision(p);d["final_answer"][field]=value
    with pytest.raises(secondary.AdjudicationError) as caught:secondary.validate_decisions(d,p)
    assert caught.value.category==category and caught.value.criterion_id=="final_answer"


@pytest.mark.parametrize("mutation,category",[
    (lambda d:d["final_answer"].pop("rationale"),"missing_field"),
    (lambda d:d["final_answer"].pop("decision"),"missing_field"),
    (lambda d:d["final_answer"].update(extra="unused"),"extra_field"),
    (lambda d:d.update(wrong=d.pop("final_answer")),"wrong_criterion_id")])
def test_missing_extra_fields_and_wrong_criterion(mutation,category):
    p=payload();d=decision(p);mutation(d)
    with pytest.raises(secondary.AdjudicationError) as caught:secondary.validate_decisions(d,p)
    assert caught.value.category==category


@pytest.mark.parametrize("raw",['not json','```json\n{}\n```','{','NaN','Infinity'])
def test_invalid_json_is_classified(raw):
    with pytest.raises(secondary.AdjudicationError) as caught:secondary.parse_response(raw)
    assert caught.value.category=="json_parse_failure"


@pytest.mark.parametrize("raw",['{"x":1,"x":2}','{"x":{"points":0,"points":2}}'])
def test_duplicate_json_keys_are_not_silently_overwritten(raw):
    with pytest.raises(secondary.AdjudicationError) as caught:secondary.parse_response(raw)
    assert caught.value.category=="duplicate_json_key"
    excerpt=secondary.diagnostic(caught.value,payload(),raw)["response_excerpt"]
    duplicated="points" if '"points"' in raw else "x"
    assert excerpt.count(json.dumps(duplicated))==2


def test_one_retry_changes_only_correction_instructions(monkeypatch):
    p=payload();seen,_=fake_client(monkeypatch,['not json',selection(p)])
    d,m=secondary.adjudicate(p)
    assert {k:{f:v for f,v in x.items() if f!="evidence"} for k,x in d.items()}==selection(p) and m["attempts"]==2 and m["retry_count"]==1
    assert m["attempt_details"][0]["validation_error"]["category"]=="json_parse_failure"
    assert seen[0]["input"]==seen[1]["input"] and seen[0]["text"]==seen[1]["text"]
    assert seen[1]["instructions"].startswith(seen[0]["instructions"])
    assert "Não altere a pauta" in seen[1]["instructions"]


def test_invented_formal_conclusion_is_retried_not_locally_awarded(monkeypatch):
    p=payload();bad=selection(p,"deny")
    bad["final_answer"]["rationale"]="Valores corretos, mas falta conclusão formal."
    seen,_=fake_client(monkeypatch,[bad,selection(p)])
    d,m=secondary.adjudicate(p)
    assert len(seen)==2 and d["final_answer"]["decision"]=="award"
    assert m["attempt_details"][0]["validation_error"]["category"]=="unauthorized_rationale"


def test_two_invalid_responses_fail_closed_with_redacted_bounded_diagnostics(monkeypatch):
    assert 'unrecognized-secret' not in secondary.redact('{"api_key":"unrecognized-secret"}')
    assert 'database-password' not in secondary.redact('postgres://user:database-password@host/db')
    p=payload();secret="sk-testprivatecredential12345";monkeypatch.setenv("OTHER_SECRET",secret)
    encoded=json.dumps({"evidence":[secret]}).replace(secret,''.join('\\u%04x' % ord(c) for c in secret))
    redacted=secondary.diagnostic(secondary.AdjudicationError("ADJUDICATOR_INVALID_EVIDENCE"),p,encoded)
    assert secret not in json.dumps(json.loads(redacted["response_excerpt"]),ensure_ascii=False)
    bad=selection(p);bad["final_answer"]["evidence_ids"]=[secret+' /Users/alice/private '+('a'*64)+' noise '*1000]
    seen,_=fake_client(monkeypatch,[bad,bad])
    with pytest.raises(secondary.AdjudicationError) as caught:secondary.adjudicate(p)
    exc=caught.value;meta=exc.diagnostics;serialized=json.dumps(meta)
    assert exc.code=="ADJUDICATOR_INVALID_RESPONSE" and len(seen)==2
    assert secret not in serialized and '/Users/alice' not in serialized and 'a'*64 not in serialized
    assert meta["retry_count"]==1 and len(meta["attempt_details"])==2
    for attempt in meta["attempt_details"]:
        assert len(attempt["response_excerpt"])<=secondary.MAX_EXCERPT
        assert attempt["validation_error"]["category"]=="invalid_evidence_ids"
        assert attempt["criterion_id"]=="final_answer" and attempt["allowed_points"]==[0,2]
    assert meta["criteria"][0]["suggested_points"] is None


@pytest.mark.parametrize("kind",["request","timeout","incomplete","refusal"])
def test_non_validation_failure_is_not_retried(monkeypatch,kind):
    import httpx,openai
    reply={"request":RuntimeError("secret response body"),
        "timeout":openai.APITimeoutError(request=httpx.Request("POST","https://invalid.example")),
        "incomplete":SimpleNamespace(status="incomplete",output_text="partial",model="test",id="test"),
        "refusal":SimpleNamespace(status="completed",output_text="",model="test",id="test",
            output=[{"content":[{"type":"refusal","refusal":"Refusal text"}]}])}[kind]
    seen,_=fake_client(monkeypatch,[reply])
    with pytest.raises(secondary.AdjudicationError) as caught:secondary.adjudicate(payload())
    assert len(seen)==1 and caught.value.diagnostics["retry_count"]==0
    assert "secret response body" not in json.dumps(caught.value.diagnostics)
    if kind=="refusal":assert caught.value.diagnostics["attempt_details"][0]["validation_error"]["category"]=="model_refusal"


@pytest.mark.parametrize("pid",["ITA2025F2Q1","ITA2025F2Q5","ITA2025Q3","ITA2025Q4"])
def test_real_rubric_context_and_prompt_are_criterion_specific(monkeypatch,pid):
    assets=validate_problem_assets(ROOT/'problems'/pid,pid);config=assets.rubric.items[-1]
    item=RubricItemResult(id=config.id,description=config.description,detected=False,points=None,
        max_points=config.points,mathematical_status="indeterminate")
    p=prepare_payload(pending=[item],solution="Resposta do estudante.",assets=assets,microclaims=[],student_checks=[])
    seen,_=fake_client(monkeypatch,[selection(p,"deny")]);secondary.adjudicate(p)
    wire=json.loads(seen[0]["input"]);c=wire["pending_criteria"][0]
    assert c["description"]==config.description and c["allowed_points"]==[0,config.points]
    assert set(wire)=={"problem","pending_criteria"}
    assert set(wire["problem"])=={"statement"} and len(wire["pending_criteria"])==1
    instructions=seen[0]["instructions"]
    assert "VOCÊ NÃO PODE CRIAR NOVAS EXIGÊNCIAS" in instructions and "evidence_ids" in instructions
    assert "score sugerido" in instructions and "não é matemática verificada" in instructions
    assert config.description in json.dumps(seen[0]["text"],ensure_ascii=False)


@pytest.mark.parametrize("status,points",[("supported",2),("refuted",0)])
def test_decided_criterion_is_not_called_or_overwritten(monkeypatch,status,points):
    from tests.test_score_policy import inputs
    data=inputs([status]);seen,_=fake_client(monkeypatch,[])
    result=apply_scoring_policy(**data)
    assert not seen and result.items[0].suggested_points==points
    assert result.items[0].mathematical_status==status
    trace=secondary.artifact_trace(result)["criteria"][0]
    assert trace["validation_status"]=="not_requested" and trace["reason"]=="first_pass_decided"


@pytest.mark.parametrize("status",["supported","refuted"])
def test_inconsistent_decided_primary_state_fails_without_call(monkeypatch,status):
    from tests.test_score_policy import inputs
    data=inputs([status]);data["rubric"].items[0].points=None
    seen,_=fake_client(monkeypatch,[]);result=apply_scoring_policy(**data)
    assert not seen and result.score is None and result.unscorable_reason=="ADJUDICATOR_INVALID_CRITERIA"


def test_secondary_points_leave_coverage_status_and_technical_error_unchanged(monkeypatch):
    from tests.test_score_policy import inputs
    data=inputs(["supported"]*4+["indeterminate"],technical=True)
    seen,_=fake_client(monkeypatch,[lambda call:selection(json.loads(call["input"]))])
    result=apply_scoring_policy(**data)
    assert result.score==10 and result.coverage==.8 and result.estimated_points==2 and result.needs_review
    final=result.items[-1]
    assert final.points is None and final.suggested_points==2 and final.scoring_basis=="secondary_adjudication"
    assert final.mathematical_status=="indeterminate" and final.verification_status=="technical_error"
    assert len(seen)==1 and len(json.loads(seen[0]["input"])["pending_criteria"])==1


def test_final_invalid_failure_preserves_primary_points_and_trace(monkeypatch):
    from tests.test_score_policy import inputs
    data=inputs(["supported","indeterminate"]);fake_client(monkeypatch,['broken','broken'])
    result=apply_scoring_policy(**data)
    assert result.score is None and result.unscorable_reason=="ADJUDICATOR_INVALID_RESPONSE"
    assert result.items[0].suggested_points==2 and result.items[1].suggested_points is None
    trace=secondary.artifact_trace(result)
    assert trace["criteria"][0]["validation_status"]=="not_requested"
    assert trace["criteria"][1]["retry_count"]==1 and trace["criteria"][1]["suggested_points"] is None


def test_no_secrets_paths_hashes_or_unnecessary_ids_are_sent(monkeypatch):
    large_integer="1234567890"*8
    assert secondary.redact(large_integer)==large_integer
    assert large_integer not in secondary.redact('sha256='+large_integer)
    p=payload();p["secret"]="do not send";p["problem"]={"statement":"Texto público", "source":"private path"}
    p["pending_criteria"][0].update(internal_id="sensitive-id", source_sha256="a"*64,
        lean_file="artifacts/private.lean", api_key="private key", unused="unnecessary")
    p["solution_text"]+=' token=sk-privatecredential0123 /Users/alice/private'
    seen,_=fake_client(monkeypatch,[lambda call: {"final_answer":dict(selection(payload())["final_answer"])}])
    secondary.adjudicate(p)
    text=seen[0]["input"]
    for excluded in ['sensitive-id','a'*64,'artifacts/private.lean','private key','sk-privatecredential0123','/Users/alice','unnecessary','private path']:
        assert excluded not in text


def primary_context(pid,text):
    from confia_lean_auditor.claims.extract_claims import extract_claims
    from confia_lean_auditor.student_claims.registry import extract_student_claims_for_audit
    from confia_lean_auditor.claims.common.rubric_bridge import RubricClaimContext
    from confia_lean_auditor.rubric.rubric_evaluator import evaluate_rubric
    assets=validate_problem_assets(ROOT/'problems'/pid,pid)
    extraction=extract_claims(pid,text)
    context=RubricClaimContext(problem_id=pid,solution_text=text,extraction=extraction,
        students=extract_student_claims_for_audit(pid,text),checks=(),rubric_config=assets.rubric,
        statement_text=assets.problem.statement,correct_answer=assets.problem.correct_answer)
    rubric=evaluate_rubric(ROOT,pid,extraction,[],assets.rubric,solution_text=text,
        statement_text=assets.problem.statement,claim_context=context)
    return dict(rubric=rubric,solution=text,assets=assets,claim_extraction=extraction,
                microclaims=[],student_claim_checks=[],claim_context=context)


@pytest.mark.parametrize("pid,text,criterion",[
    ("ITA2025F2Q1","Logo a=-1 e b=3.","final_answer"),
    ("ITA2025F2Q5","O primeiro algarismo de 3^100, da esquerda para a direita, é 5.","final_digit")])
def test_actual_primary_f2q1_and_f2q5_are_never_readjudicated(monkeypatch,pid,text,criterion):
    data=primary_context(pid,text)
    final=next(i for i in data["rubric"].items if i.id==criterion)
    assert final.points==2 and final.mathematical_status=="supported"
    seen,_=fake_client(monkeypatch,[lambda call:selection(json.loads(call["input"]),"deny")])
    result=apply_scoring_policy(**data)
    assert seen and criterion not in {c["id"] for c in json.loads(seen[0]["input"])["pending_criteria"]}
    assert final.points==final.suggested_points==2 and final.scoring_basis=="first_pass"
    assert result.coverage==.2 and result.estimated_points==0 and result.needs_review


def test_grounded_canonical_alignment_context_excludes_proof_artifacts(monkeypatch):
    data=primary_context("ITA2025Q1","a^2-2a+5=200. Logo a=15.")
    seen,_=fake_client(monkeypatch,[lambda call:selection(json.loads(call["input"]),"deny")])
    apply_scoring_policy(**data)
    criteria=json.loads(seen[0]["input"])["pending_criteria"]
    equation=next(c for c in criteria if c["id"]=="equation")
    assert equation["required_microclaims"]
    assert all(m["status"]=="unavailable" and m["does_not_prove_student_attribution"]
               for m in equation["required_microclaims"])
    assert equation["candidate_evidence"]
    claim=next(c for c in equation["candidate_evidence"] if c["source_kind"]=="math_claim_record")
    assert data["solution"][claim["source_start"]:claim["source_end"]]==claim["source_text"]
    assert claim["grounding_status"]=="grounded" and claim["verification_status"]=="not_checked"
    serialized=seen[0]["input"]
    for forbidden in ["source_sha256","record_id","lean_statement","lean_file","artifact_ref"]:
        assert forbidden not in serialized


def test_adjudicated_zero_is_not_formal_refutation(monkeypatch):
    from tests.test_score_policy import inputs
    data=inputs(["indeterminate"])
    fake_client(monkeypatch,[lambda call:selection(json.loads(call["input"]),"deny")])
    result=apply_scoring_policy(**data);item=result.items[0]
    assert item.suggested_points==0 and item.points is None and item.verified_points is None
    assert item.mathematical_status=="indeterminate" and item.scoring_basis=="secondary_adjudication"
    assert result.coverage==0 and result.needs_review


def test_deny_cannot_acknowledge_the_criterion_as_satisfied():
    p=payload();d=decision(p,"deny")
    d["final_answer"]["rationale"]=secondary.rationale_options(p["pending_criteria"][0])["award"][0]
    with pytest.raises(secondary.AdjudicationError) as caught:secondary.validate_decisions(d,p)
    assert caught.value.category=="unauthorized_rationale"


def test_installed_sdk_serializes_structured_outputs_with_mock_transport(monkeypatch):
    import httpx,openai
    real_client=openai.OpenAI;p=payload();seen=[]
    def handler(request):
        assert request.url.host=="offline.invalid"
        body=json.loads(request.content);seen.append(body)
        return httpx.Response(200,json={"id":"offline-sdk-response","object":"response",
            "created_at":0,"status":"completed","model":"offline-sdk-model",
            "output":[{"id":"offline-message","type":"message","role":"assistant","status":"completed",
                "content":[{"type":"output_text","text":json.dumps(selection(p)),"annotations":[]}]}]})
    def factory(**kwargs):
        return real_client(api_key="offline-placeholder",base_url="https://offline.invalid/v1",
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),**kwargs)
    monkeypatch.setenv("OPENAI_API_KEY","offline-placeholder")
    monkeypatch.setattr(openai,"OpenAI",factory)
    actual,meta=secondary.adjudicate(p)
    assert {k:{f:v for f,v in d.items() if f!="evidence"} for k,d in actual.items()}==selection(p) and len(seen)==1
    assert seen[0]["text"]["format"]["strict"] is True and seen[0]["store"] is False
    assert meta["resolved_model"]=="offline-sdk-model"
