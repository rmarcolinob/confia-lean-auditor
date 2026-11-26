"""Explicit DEV experiment entry point. Default shadow never scores semantic facts.

No HTTP/accepted-transcription/UI/default feature flag is changed. The primary
path is verified first. The shadow path stops at the existing bridge and never
calls PautaEngine with its facts. Activation is a separate, authorized operation.
"""
from dataclasses import dataclass
from importlib import import_module
import json
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims import obligation_semantic as semantic
from confia_lean_auditor.student_claims.obligation_catalog import mathematical_obligations, internal_id
from .registry import ROOT, TME_PROBLEMS, audit_tme
from confia_lean_auditor.rubric.pauta import load_pauta


def deterministic_only(problem_id,source,ranges,records,*,observe=True):
    return tuple(records),None


def primary_audit(problem_id,items,*,solution_id,use_lean=True):
    with legacy.supplement_scope(deterministic_only):
        return audit_tme(problem_id,items,solution_id=solution_id,use_lean=use_lean)


def unresolved_targets(problem_id,primary_bridge):
    settled={e.obligation_id for e in primary_bridge.evidence.obligations if e.status in {'supported','refuted'}}
    return tuple(t for t in mathematical_obligations(problem_id) if t['obligation_id'] not in settled)


def verify_without_scoring(problem_id,items,solution_id,*,use_lean=True):
    """Reuse unchanged collectors, checkers/Lean and bridge; deliberately no engine."""
    problem_id=internal_id(problem_id);n='1' if problem_id=='TME2_P1_PILOT' else problem_id[-1]
    config=load_pauta(ROOT/'examples/pautas'/TME_PROBLEMS[problem_id])
    digital_module=import_module(f'confia_lean_auditor.student_claims.tme2_p{n}_digital')
    checker=import_module(f'confia_lean_auditor.lean.student_claim_checkers.tme2_p{n}')
    bridge_module=import_module(f'confia_lean_auditor.rubric.pauta.tme2_p{n}')
    if n=='2':
        texts,diagrams=digital_module.split_p2_input(items)
        bundle=checker.verify_tme2_p2(digital_module.collect_tme2_p2_text(texts),diagrams,solution_id,use_lean=use_lean)
    else:
        digital=getattr(digital_module,f'collect_tme2_p{n}_digital')(items)
        if n=='3':
            from .p3_machine import load_machine
            machine=load_machine(ROOT/'examples/pautas/tme2_problem3.machine.v1.json')
            bundle=checker.verify_tme2_p3_digital(digital,solution_id,machine,use_lean=use_lean)
        else:bundle=getattr(checker,f'verify_tme2_p{n}_digital')(digital,solution_id,use_lean=use_lean)
    return getattr(bridge_module,f'bridge_tme2_p{n}')(config,bundle)


@dataclass(frozen=True)
class ShadowAudit:
    problem_id: str
    primary_bridge: object
    assessment: object
    potential_bridge: object
    telemetry: dict
    configuration: dict
    semantic_shadow: bool = True


def run_shadow(problem_id,items,full_text,*,solution_id,use_lean=True,provider=None,primary=None):
    problem_id=internal_id(problem_id)
    primary_bridge,assessment=primary or primary_audit(problem_id,items,solution_id=solution_id,use_lean=use_lean)
    targets=unresolved_targets(problem_id,primary_bridge)
    config=semantic.configuration()
    request=provider or semantic.request_candidates
    if targets:
        candidates,metadata=request(problem_id,full_text,json.dumps(targets,ensure_ascii=False,sort_keys=True),json.dumps(config,sort_keys=True))
    else:candidates,metadata=(),dict(status='skipped_no_unresolved_obligations')
    # Provider injection/replay obeys the exact same schema/target validation.
    candidates=semantic.validate_response(json.dumps({'candidates':[c.model_dump() for c in candidates]},ensure_ascii=False),targets)
    session=semantic.ProjectionSession(problem_id,full_text,targets,candidates,metadata)
    with legacy.supplement_scope(session):
        potential_bridge=verify_without_scoring(problem_id,items,solution_id,use_lean=use_lean)
    return ShadowAudit(problem_id,primary_bridge,assessment,potential_bridge,session.telemetry,config)


def activate_shadow(shadow,*,gate_passed=False):
    """Only the experiment gate authorizes this separate scoring step."""
    if gate_passed is not True:
        raise ValueError('Active scoring requires a passed shadow gate')
    from confia_lean_auditor.rubric.pauta.engine import PautaEngine
    config=load_pauta(ROOT/'examples/pautas'/TME_PROBLEMS[shadow.problem_id])
    return PautaEngine().evaluate(config,shadow.potential_bridge.evidence)
