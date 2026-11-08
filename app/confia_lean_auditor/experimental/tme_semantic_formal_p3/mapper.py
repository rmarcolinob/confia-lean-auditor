"""Bounded source normalization and local context, without mathematical verdicts."""
import re
from confia_lean_auditor.experimental.tme_semantic_formal.obligation_mapper import SourceDocument as BaseDocument
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims.named_math import extract_named_math
from confia_lean_auditor.student_claims.tme2_p3_digital import VOCABULARY
from .registry import REGISTRY, PROBLEM_ID, route_for_expression

class SourceDocument:
    @staticmethod
    def parse(text):
        document=BaseDocument.parse(text)
        if not set(document.items)<={'a','b','c'}: raise ValueError('P3_only_items_abc')
        return document

ORDINALS={'primeiro':'1','primeira':'1','segundo':'2','segunda':'2','terceiro':'3',
          'terceira':'3','quarto':'4','quarta':'4','quinto':'5','quinta':'5','sexto':'6','sexta':'6'}

def source_view(text):
    text=legacy.normalized(text)
    for word,value in ORDINALS.items(): text=re.sub(r'\b'+word+r'\b',value,text)
    for word,value in legacy.WORDS.items(): text=re.sub(r'\b'+legacy.normalized(word)+r'\b',str(value),text)
    return text

def local_context(document,e):
    """A rejected span cannot veto unrelated assertions in another source unit.

    Qualifying headers carry within their paragraph until an explicit assertion
    reset. Mathematical case conditions are not discarded hypotheses by default.
    """
    raw=legacy.normalized(e.source_span)
    if re.search(r'\b(?:nao|nunca|jamais|supondo|fosse|seria)\b',raw): return False
    reject=r'\b(?:suponha|suponhamos|hipotese|hipotetic\w*|descart\w*|abandon\w*|citacao|enunciado|segundo\s+(?:joao|maria|o autor)|nao\s+(?:e|vale|funciona|sei)|talvez|tentativa|ignore.*instru|desconsidere.*instru)\b'
    if re.search(reject,raw) or '"' in raw or '“' in raw: return False
    if re.search(r'\bsegundo\s+(?!(?:compartimento|caso|ramo|sorteio|acionamento)\b)\w+|\b(?:disse|afirmou|calculou|de acordo com)\b',raw): return False
    if re.search(r'\b(?:solucao de|afirmacao de|outra pessoa)\b',raw): return False
    if re.match(r'\s*(?:afirmo|concluo|minha resposta|resposta final)\b',raw): return True
    start=document.ranges.get(e.item_id,(0,0))[0]
    prefix=document.text[start:e.source_start].rsplit('\n\n',1)[-1]
    active=False
    for line in prefix.splitlines():
        line=legacy.normalized(line).strip()
        if re.match(r'(?:afirmo|concluo|minha resposta|resposta final)\b',line): active=False
        elif line.endswith(':') and re.search(reject,line): active=True
    return not active

def _anchor(e,document):
    subject=e.subject; raw=source_view(e.source_span)
    if re.search(r'\b'+re.escape(subject)+r'\s*:',raw):return True
    if subject=='inferiores_brancas': return bool(re.search('branc',raw) and re.search('inferior|embaixo|base',raw))
    if subject in {'primeira_branca','segunda_branca'}:
        index='1' if subject=='primeira_branca' else '2'
        return bool(re.search(r'\b'+index+r'\s+(?:bola|branca|retirada|extracao|escolha|acionamento|sorteio)\b',raw) and 'branc' in raw) or (
            document.items.get(e.item_id,'').strip()==e.source_span.strip() and
            legacy.notation_view(e.source_span)==legacy.notation_view(e.normalized_claim))
    if subject=='pares_ordenados': return bool(re.search(r'pares? ordenados?|espaco amostral',raw))
    if subject=='favoraveis_distintos': return bool(re.search(r'favorave|branc',raw) and re.search(r'diferent|distint',raw))
    if subject=='repeticao_branca': return bool(re.search(r'repet|mesmo compartimento',raw) and re.search(r'branc|funciona',raw))
    if subject=='continuar': return bool(re.search(r'continu',raw))
    if subject=='total': return bool(re.search(r'ganh|vitoria|probabilidade total',raw))
    if subject=='arvore_total': return bool(re.search(r'arvore|ramos',raw) and re.search(r'total|som',raw))
    if subject.startswith(('estrategia_','contagem_','condicional_','ramo_')):
        index=subject.rsplit('_',1)[1]
        bound=bool(re.search(r'(?:compartimento|caso|ramo)\s*(?:numero\s*)?'+index+r'\b',raw)
                   or re.search(r'\b'+index+r'\s+compartimento',raw))
        if subject.startswith(('estrategia_','contagem_')): return bound and bool(re.search('branc|pret|cinza|black|white|gray',raw))
        return bound and bool(re.search('probabilidade|chance|condicional|ramo',raw))
    return False

def representation(e,document):
    # A typed assertion keeps its own lexical field even when sentence context
    # contains a different probability/quantity. Never borrow the neighbor.
    if e.asserted_content in e.source_span and re.search(r'\b'+re.escape(e.subject)+r'\s*:',e.asserted_content):
        e=e.model_copy(update={'source_span':e.asserted_content})
    if e.subject not in VOCABULARY: raise ValueError('no_checker_representation')
    if e.claim_type!=VOCABULARY[e.subject]['kind']: raise ValueError('claim_type_subject_mismatch')
    if '\n' in e.normalized_claim: raise ValueError('multiline_payload_not_supported')
    parsed=extract_named_math(PROBLEM_ID,e.subject+': '+e.normalized_claim,VOCABULARY)
    if len(parsed)!=1: raise ValueError('unsupported_checker_payload')
    native=extract_named_math(PROBLEM_ID,e.source_span,VOCABULARY)
    if native:
        if not any(r.canonical_form.subject==e.subject and
                   (legacy.notation_view(r.canonical_form.value.get('expression',''))==legacy.notation_view(e.normalized_claim)
                    or e.claim_type=='enum' and r.canonical_form.value.get('value')==parsed[0].canonical_form.value.get('value')) for r in native):
            raise ValueError('typed_source_payload_changed')
        return parsed[0]
    clauses=[s.strip() for s in re.split(r';|\n|(?<!\d)\.|\.(?!\d)',e.source_span) if s.strip()]
    anchored=[s for s in clauses if _anchor(e.model_copy(update={'source_span':s}),document)]
    if len(anchored)!=1: raise ValueError('subject_not_uniquely_bound_to_source_clause')
    raw=source_view(anchored[0]); expr=legacy.notation_view(e.normalized_claim)
    if e.subject in {'primeira_branca','segunda_branca'} and re.search(r'\b1\s+(?:bola|branca|retirada)',raw) and re.search(r'\b2\s+(?:bola|branca|retirada)',raw):
        raise ValueError('mixed_probability_roles')
    if e.subject=='inferiores_brancas' and not (re.search(r'(?<!\d)'+re.escape(expr)+r'\s+(?:bolas?\s+)?branc\w*\b',raw) or
            re.search(r'branc\w*\s+(?:inferiores|na base|embaixo)\s+(?:e|sao|:|=)\s*'+re.escape(expr)+r'(?!\d)',raw)):
        raise ValueError('white_count_not_bound_to_written_quantity')
    if e.subject.startswith('contagem_'):
        counts=re.findall(r'\b(?:aparece|aparecem|ocorre|ocorrem)\s+(\d+)\s+vez',raw)
        if not counts or any(n!=expr for n in counts): raise ValueError('color_count_not_bound_to_written_quantity')
    if e.subject=='inferiores_brancas' and re.search(r'\bsuperior\w*|no alto|em cima',raw):
        # Multiple locations require their own explicit assertion, rather than
        # associating every number with any occurrence of 'inferiores'.
        raise ValueError('mixed_quantity_locations')
    if e.subject.startswith(('estrategia_','contagem_','condicional_','ramo_')):
        cases=set(re.findall(r'(?:compartimento|caso|ramo)\s*(?:numero\s*)?([1-6])\b',raw))
        if len(cases)>1:raise ValueError('mixed_case_roles')
    if re.search(r'\b(?:pagina|exercicio|questao|ano|telefone|matricula|idade)\s*(?:numero|:)?\s*\d+',raw): raise ValueError('incidental_number_context')
    if e.claim_type=='enum':
        target=parsed[0].canonical_form.value.get('value')
        if not any(v==target and re.search(r'\b'+re.escape(k)+r'\b',raw) for k,v in VOCABULARY[e.subject]['values'].items()):
            raise ValueError('color_not_written')
    elif e.claim_type=='integer_set':
        # Membership/examples do not assert a complete favorable set.
        if re.search(r'por exemplo|tais como|inclui|incluem|tambem',raw):
            raise ValueError('partial_membership_not_complete_set')
        if e.subject=='repeticao_branca' and not re.search(r'\{|somente|apenas|unicamente|unico|lista fechada|\bso\b',raw):
            raise ValueError('partial_membership_not_complete_set')
        # Enumeration must be explicit; no completing sets from the machine.
        members=re.fullmatch(r'\{(\d+(?:,\d+)*)\}',expr)
        if not members: raise ValueError('explicit_integer_set_required')
        listed=members[1].split(',')
        joined=r'\s*(?:,|e)\s*'.join(re.escape(x) for x in listed)
        if not re.search(r'(?<!\d)'+joined+r'(?!\d)',raw): raise ValueError('set_members_not_written')
        # A complete exclusive list cannot be shortened to a true subset.
        all_numbers=re.findall(r'\d+',raw)
        if all_numbers!=listed: raise ValueError('set_payload_omits_source_members')
    else:
        view=legacy.notation_view(raw)
        matches=list(re.finditer(re.escape(expr),view))
        def whole(m):
            before=view[:m.start()].rstrip('('); after=view[m.end():].lstrip(')')
            return (not before or before[-1] not in '=+-*/^!0123456789') and (not after or after[0] not in '=+-*/^!0123456789')
        if not expr or not any(whole(m) for m in matches): raise ValueError('representation_not_written_or_truncated')
    return parsed[0]

class ObligationMapper:
    def map(self,document,evidence):
        interpretations={}
        for e in evidence:
            key=(e.source_start,e.source_end,e.subject)
            interpretations.setdefault(key,set()).add((e.normalized_claim,e.assertion_status,e.polarity,e.hypothetical,e.abandoned,e.attributed_to_student))
        rows=[]
        for e in evidence:
            for oid in e.obligation_candidates:
                spec=REGISTRY.get(oid)
                row=dict(evidence_id=e.evidence_id,obligation_id=oid,accepted=False,context_valid=False,
                         reason=None,suggested_route=e.route_candidate,effective_route=spec.route if spec else None,route_override_reason=None)
                try:
                    if not spec: raise ValueError('unknown_obligation')
                    if document.text[e.source_start:e.source_end]!=e.source_span or e.metadata.get('source_sha256')!=legacy.sha(document.text): raise ValueError('source_binding_changed')
                    discourse=e.metadata.get('discourse_decision')
                    if discourse and not discourse['positive_credit_eligibility']: raise ValueError('discourse_'+discourse['resolved_discourse_state'].lower())
                    if not discourse and len(interpretations[(e.source_start,e.source_end,e.subject)])>1: raise ValueError('conflicting_extractor_interpretation')
                    if not (e.assertion_status=='asserted' and e.polarity=='positive' and e.attributed_to_student and not e.hypothetical and not e.abandoned and e.scope in {'main_argument','final_conclusion'}): raise ValueError('nonasserted_or_unattributed_context')
                    owner=[k for k,(a,b) in document.ranges.items() if a<=e.source_start<e.source_end<=b]
                    if owner!=[spec.rubric_item] or e.item_id!=spec.rubric_item: raise ValueError('same_item_required')
                    if not discourse and not local_context(document,e): raise ValueError('source_context_rejected')
                    if e.subject not in spec.subjects or e.claim_type not in spec.claim_types: raise ValueError('obligation_subject_type_mismatch')
                    if discourse and e.claim_type=='integer_set':
                        from .source_adapter import member_atom
                        if member_atom(e): raise ValueError('partial_membership_not_complete_set')
                    representation(e,document)
                    contract=e.metadata.get('representation_receipt')
                    binding=next((b for b in e.metadata.get('binding_receipts',[]) if b['obligation_id']==oid),None)
                    if discourse:
                        from .semantic_contracts import SAFE_FIDELITY,SAFE_BINDING
                        if not contract or contract['representation_fidelity'] not in SAFE_FIDELITY:raise ValueError('insufficient_representation_fidelity')
                        if not binding or binding['binding_status'] not in SAFE_BINDING:raise ValueError('binding_not_authorized')
                    row.update(representation_receipt=contract,binding_receipt=binding,segment=e.metadata.get('discourse_segment'))
                    route=route_for_expression(oid,e.normalized_claim)
                    row.update(accepted=True,context_valid=True,reason='compatible_pending_checker',effective_route=route,
                               route_override_reason='obligation_registry' if route!=e.route_candidate else None)
                except ValueError as error: row['reason']=str(error)
                row.setdefault('representation_receipt',e.metadata.get('representation_receipt'))
                row.setdefault('binding_receipt',next((b for b in e.metadata.get('binding_receipts',[]) if b['obligation_id']==oid),None))
                row.setdefault('segment',e.metadata.get('discourse_segment'))
                rows.append(row)
        return rows
