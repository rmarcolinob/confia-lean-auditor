"""Post-evaluation dependency gates. No inferred zero or cascade penalty."""
from decimal import Decimal

VERSION = 'dynamic-dependencies.v1'


def assess_dependencies(rubric, snapshots):
    """Evaluate the approved DAG in dependency order, independently of display order.

    snapshots are private to each evaluator. Reconciliation uses its own settled
    rows, so disputed upstream credit cannot silently authorize downstream credit.
    """
    criteria={c.criterion_id:c for c in rubric.criteria};done={}
    def visit(cid):
        if cid in done:return done[cid]
        c=criteria[cid];own=snapshots.get(cid,{})
        for dep in c.dependencies:visit(dep)
        rules={r.criterion_id:r for r in c.dependency_rules}
        rows=[]
        for dep in c.dependencies:
            prior=snapshots.get(dep,{})
            rule=rules.get(dep)
            status='unknown';reason='Dependência histórica sem significado explícito; revisão humana necessária.'
            if rule:
                opinion=own.get('opinions',{}).get(dep,{})
                status=opinion.get('status','unknown')
                reason=opinion.get('justification','Condição da dependência não avaliada.')
                if rule.kind=='MATHEMATICAL':
                    sufficient=(prior.get('points') is not None and (
                        Decimal(str(prior['points']))>=rule.minimum_points if rule.minimum_points is not None
                        else prior.get('sufficiency')=='COMPLETE'))
                    if not prior.get('conclusive') or done[dep]['status'] in {'unknown','violated'}:
                        status='unknown';reason='Pré-requisito matemático ainda indeterminado.'
                    elif not sufficient:
                        status='violated';reason='Pré-requisito abaixo do atendimento expressamente exigido.'
                    elif own.get('exact'):
                        status='satisfied';reason='Crédito exato e pré-requisito matemático determinado preservados.'
                # PROCEDURAL/CARRY_FORWARD use their own grounded condition,
                # never the prerequisite's score as a substitute for that condition.
            rows.append(dict(criterion_id=dep,kind=rule.kind if rule else 'UNSPECIFIED',
                condition=rule.condition if rule else None,status=status,reason=reason,
                prerequisite_points=str(prior['points']) if prior.get('points') is not None else None))
        applicable=own.get('points') is not None and own['points']>0
        state=('violated' if any(r['status']=='violated' for r in rows) else
               'unknown' if any(r['status']=='unknown' for r in rows) else 'satisfied') if applicable else 'not_applicable'
        done[cid]=dict(schema_version=VERSION,status=state,dependencies=rows)
        return done[cid]
    for c in rubric.criteria:visit(c.criterion_id)
    return done


def blocked(assessment):
    return bool(assessment and assessment['status'] in {'unknown','violated'})


def opinions(trace):
    return {r['criterion_id']:r for r in (trace or {}).get('dependency_opinions',[])}
