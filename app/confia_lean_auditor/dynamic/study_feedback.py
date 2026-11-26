"""Restricted pedagogical projection. Never change the mathematical decisions."""
import re
from types import SimpleNamespace
from .study_models import LearningFinding, LearningReport, ControlledHelpProposal, StudyRubric
from .grading_models import DynamicAuditResult
from .reconciliation_models import CriterionReconciliation
from confia_lean_auditor.submissions.integrity import canonical_sha256

POLICY = 'self-study-feedback.v2'
GUIDANCE = {
 'SUPPORTED':'Este passo tem apoio na análise. Preserve a justificativa ao revisar sua solução.',
 'PARTIAL':'Há desenvolvimento aproveitável, mas este objetivo ainda precisa ser completado ou explicado.',
 'MATHEMATICAL_ERROR':'Os avaliadores identificaram um possível erro no trecho citado. Confira a operação e as condições do problema.',
 'NEEDS_EXPLANATION':'A conclusão ainda precisa de uma justificativa. Escreva como você chegou a ela.',
 'UNCERTAIN':'Não há verificação suficiente para concluir. Explique melhor o trecho; incerteza não significa erro.',
 'TECHNICAL_ERROR':'Não foi possível analisar este objetivo por uma falha técnica. Isso não indica erro na sua matemática.'}
# Provider chooses a concept, never supplies public prose at levels 2/3.
TOPICS = {
 'EQUALITY':('Qual operação deve ser aplicada aos dois membros para preservar a igualdade?', 'Uma igualdade permanece equivalente quando você aplica a mesma operação válida aos dois membros. Antes de dividir, confira se o divisor pode ser zero.'),
 'FACTORIZATION':('Você consegue escrever a expressão como um produto e conferir expandindo?', 'Fatorar é reescrever uma expressão como produto. A expansão permite conferir a equivalência; um produto nulo exige examinar seus fatores.'),
 'PROPORTION':('Qual razão ou valor por unidade permanece constante neste problema?', 'Na proporcionalidade direta, a razão entre as grandezas é constante. Na inversa, o produto é constante. Verifique qual relação os dados permitem afirmar.'),
 'FUNCTION':('Que relação entre entrada e saída deve valer para os dados do enunciado?', 'Uma função associa uma saída a cada entrada do domínio. Substitua os dados nas condições e explique como sua expressão respeita essa associação.'),
 'GEOMETRY':('Que medidas e propriedades da figura são necessárias para justificar seu passo?', 'Medidas de comprimento, área e volume têm unidades distintas. Uma propriedade geométrica precisa das hipóteses correspondentes; a aparência do desenho não basta.'),
 'CHECK_CONDITIONS':('Seu passo respeita todas as condições e restrições do enunciado?', 'Uma transformação pode introduzir ou perder possibilidades quando suas condições não são respeitadas. Confira as restrições e teste suas conclusões no enunciado original.'),
 'EXPLAIN_STEP':('Qual regra permite passar do trecho citado para a próxima etapa?', 'Uma justificativa liga uma afirmação à seguinte por uma regra válida e explicita as condições para usá-la. Retome o trecho e explique essa ligação com suas palavras.')}
RULES = {**{k:'Retome o conceito e confira esta etapa proposta.' for k in TOPICS},
 'SIMPLIFY':'Simplificação proposta: confira cada operação.',
 'SUBSTITUTE':'Substituição proposta: confira os dados e as condições.',
 'CONCLUDE':'Conclusão proposta: confira no enunciado original.'}
LIMIT = 'Orientação automática, sem certificação formal. A escolha do conceito e o desenvolvimento proposto podem precisar de revisão.'


def public_id(identifier): return 'objective_' + canonical_sha256(identifier)[:16]
def label(criterion): return 'Objetivo ' + str(criterion.order)
def interpretation_allowed(pack):
    # No unrestricted model prose is released in preparation either. Rephrasing
    # beyond whitespace requires clarification, not an unreviewed disclosure.
    normalize=lambda text:' '.join(text.split())
    return normalize(pack.get('interpretation','')) == normalize(pack['statement']['statement'])


def trace_finding(trace): return (trace or {}).get('finding') or (trace or {}).get('response',{}).get('finding')


def project(grader, rows, source, rubric, previous=None, reviewer_traces=None):
    findings=[]; by_id={r.criterion_id:r for r in rows}; reviewer_traces=reviewer_traces or {}
    for d in grader.decisions:
        r=by_id[d.criterion_id]; trace=d.semantic_trace or {}; finding=trace_finding(trace)
        other=trace_finding(reviewer_traces.get(d.criterion_id))
        conclusive=r.status in {'AGREEMENT_SUPPORTED','AGREEMENT_UNVERIFIED'}
        evidence=[]
        for c in grader.analysis.claims:
            if c.claim_id in d.claim_ids and source.solution_text[c.start:c.end]==c.text:
                evidence.append(dict(text=c.text,start=c.start,end=c.end,source_sha256=source.source_hash))
        error_conflict=bool(trace and (finding=='MATHEMATICAL_ERROR') != (other=='MATHEMATICAL_ERROR'))
        state='TECHNICAL_ERROR' if r.technical_uncertainty else 'UNCERTAIN' if not conclusive or error_conflict else {
            'COMPLETE':'SUPPORTED','PARTIAL':'PARTIAL','INSUFFICIENT':'NEEDS_EXPLANATION',
            'NOT_SATISFIED':'MATHEMATICAL_ERROR' if finding==other=='MATHEMATICAL_ERROR' or not trace and d.automation=='AUTO_VETO' else 'NEEDS_EXPLANATION'}.get(d.sufficiency,'UNCERTAIN')
        if state in {'SUPPORTED','PARTIAL','MATHEMATICAL_ERROR'} and not evidence: state='UNCERTAIN'
        kind='UNCERTAIN'
        if state not in {'UNCERTAIN','TECHNICAL_ERROR'}:
            if evidence and (finding==other=='MATHEMATICAL_ERROR' or not trace and d.automation=='AUTO_VETO'): kind='MATHEMATICAL_ERROR'
            elif state=='SUPPORTED': kind='VALID_ARGUMENT'
            elif state=='PARTIAL': kind='INCOMPLETE'
            else: kind='INSUFFICIENT_EVIDENCE'
        guidance=GUIDANCE[state]
        if state=='PARTIAL' and kind=='MATHEMATICAL_ERROR':
            guidance='Há desenvolvimento aproveitável e os avaliadores identificaram um possível erro matemático no trecho citado. Revise essa passagem, preservando as etapas válidas.'
        if error_conflict and state!='TECHNICAL_ERROR': guidance='Os avaliadores divergem sobre a existência de um erro neste trecho. A evidência não permite afirmar esse erro com segurança; explique a passagem.'
        criterion=next(c for c in rubric.criteria if c.criterion_id==d.criterion_id)
        findings.append(LearningFinding(criterion_id=public_id(d.criterion_id),objective=label(criterion),state=state,
            mathematical_finding=kind,verification='UNDETERMINED' if state in {'TECHNICAL_ERROR','UNCERTAIN'} else 'SEMANTIC_NOT_FORMAL' if trace else 'EXACT_WITHIN_SCOPE',
            evidence=evidence,guidance=guidance))
    comparison=[]; old={f['criterion_id']:f for f in (previous or {}).get('findings',[])}
    for f in findings:
        p=old.get(f.criterion_id)
        if not p: continue
        before={e['text'] for e in p['evidence']}; after={e['text'] for e in f.evidence}
        change='NEW_EXPLANATION' if before!=after else 'UNCHANGED'
        was_error=p.get('mathematical_finding')=='MATHEMATICAL_ERROR' or p['state']=='MATHEMATICAL_ERROR'
        if was_error and f.state=='SUPPORTED': change='ERROR_REVISED'
        elif was_error and f.mathematical_finding=='MATHEMATICAL_ERROR' or p['state'] in {'PARTIAL','NEEDS_EXPLANATION'} and f.state==p['state']: change='STILL_NEEDS_ATTENTION'
        comparison.append(dict(criterion_id=f.criterion_id,change=change,previous_state=p['state'],current_state=f.state,
            new_evidence=[e for e in f.evidence if e['text'] not in before],interpretation='Comparação qualitativa entre análises automáticas, não certificação de aprendizagem.'))
    technical=any(f.state=='TECHNICAL_ERROR' for f in findings); pending=any(f.state=='UNCERTAIN' for f in findings)
    return LearningReport(status='TECHNICAL_ERROR' if technical else 'REVIEW_PENDING' if pending else 'FEEDBACK_AVAILABLE', findings=findings,
        uncertainties=['Critérios provisórios; avaliações semânticas podem divergir ou estar equivocadas. Não houve execução Lean.']+(['Há objetivos sem conclusão suficiente.'] if pending or technical else []),comparison=comparison)


def public_report(record, package, previous=None):
    """Reproject historical records read-only; never trust previously saved prose."""
    if not all(k in record for k in ('grader','reconciliation','reviewer')):
        return LearningReport(status='TECHNICAL_ERROR',findings=[],comparison=[],uncertainties=[GUIDANCE['TECHNICAL_ERROR']]).model_dump(mode='json')
    return project(DynamicAuditResult.model_validate(record['grader']),
        [CriterionReconciliation.model_validate(r) for r in record['reconciliation']],
        SimpleNamespace(solution_text=record['solution_text'],source_hash=record['source_hash']),StudyRubric.model_validate(package['rubric']),
        previous,(record['reviewer'].get('semantic_reviews') or {})).model_dump(mode='json')


def help_payload(package, attempt, report, level):
    return dict(context='SELF_STUDY',policy_version=POLICY,grade_year=package['grade_year'],
        statement=package['statement']['statement'],solution=attempt['solution_text'],level=level,
        findings=report['findings'],complete_solution_requested=level==4,
        reference_candidates=package['preparation']['proposal']['candidate_reference_solutions'] if level==4 else [])


class HelpRejected(ValueError):
    def __init__(self, raw, provenance):
        super().__init__('INVALID_PEDAGOGICAL_OUTPUT'); self.raw=raw; self.provenance=provenance


def validate_expression(expression):
    # Syntax restriction only, not a mathematical verifier. No prose, labels,
    # arbitrary identifiers, HTML or score metadata can become a guided step.
    tokens=re.findall(r'[A-Za-zΑ-ω_]+|\d+(?:[.,]\d+)?|[^\s]',expression)
    words={'sqrt','sin','cos','tan','log','ln','abs'}
    for token in tokens:
        if re.fullmatch(r'[A-Za-zΑ-ω_]+',token):
            if token not in words and not re.fullmatch(r'[A-Za-zΑ-ω]',token): raise ValueError('unsupported expression identifier')
        elif not re.fullmatch(r'\d+(?:[.,]\d+)?',token) and token not in '+-−*/×÷=<>≤≥≠^()[]{}.,:|√²³π∞∈ℝℤℕ':
            raise ValueError('unsupported expression token')
    if not tokens: raise ValueError('empty expression')


def validate_help(raw, payload):
    if payload['level'] not in {2,3,4}: raise ValueError('unsupported help level')
    proposal=ControlledHelpProposal.model_validate(raw)
    findings={f['criterion_id']:f for f in payload['findings']}
    if len({i.criterion_id for i in proposal.items})!=len(proposal.items): raise ValueError('duplicate feedback')
    for item in proposal.items:
        if item.criterion_id not in findings: raise ValueError('unknown objective')
        available={e['text'] for e in findings[item.criterion_id]['evidence']}
        if any(q not in available or q not in payload['solution'] for q in item.quotes): raise ValueError('unbound feedback evidence')
        if payload['level']<4 and item.steps: raise ValueError('steps require explicit complete-development request')
        if payload['level']==4:
            if not payload['complete_solution_requested']: raise ValueError('consent required')
            if findings[item.criterion_id]['state'] in {'UNCERTAIN','TECHNICAL_ERROR'}: raise ValueError('unresolved finding cannot support a proposed solution')
            for step in item.steps: validate_expression(step.expression)
    return proposal


def render_help(proposal, level):
    items=[]
    for item in proposal.items:
        message=TOPICS[item.topic][0 if level==2 else 1]
        if level==4:
            message='Desenvolvimento proposto para você conferir, não uma conclusão certificada.'
            if not item.steps: message+=' '+TOPICS[item.topic][1]
            for step in item.steps: message+='\n'+RULES[step.rule]+' '+step.expression
        items.append(dict(criterion_id=item.criterion_id,message=message,quotes=item.quotes))
    return dict(items=items,limitations=[LIMIT])


def safe_help(report):
    return dict(items=[dict(criterion_id=f['criterion_id'],message='A orientação solicitada não pôde ser disponibilizada com segurança. Retome o trecho citado e explique a regra usada, sem alterar sua conclusão apenas por esta indisponibilidade.',quotes=[e['text'] for e in f['evidence']]) for f in report['findings'] if f['evidence']],
        limitations=['Nenhum novo julgamento matemático foi produzido. Você pode rever sua solução ou registrar outra tentativa.'])


def generate_help(provider, payload):
    proposal,provenance=provider.generate('study_feedback',payload,ControlledHelpProposal)
    raw=proposal.model_dump(mode='json')
    try: return validate_help(raw,payload),provenance
    except ValueError as exc: raise HelpRejected(raw,provenance) from exc


def public_help(saved, payload, report):
    if saved.get('policy_version')!=POLICY or saved.get('status')!='ACCEPTED': return safe_help(report),'SAFE_FALLBACK'
    if payload['level']==4 and not saved.get('complete_solution_requested'): return safe_help(report),'SAFE_FALLBACK'
    try: proposal=validate_help(saved['content'],payload)
    except (ValueError,KeyError,TypeError): return safe_help(report),'SAFE_FALLBACK'
    return render_help(proposal,payload['level']),'AVAILABLE'
