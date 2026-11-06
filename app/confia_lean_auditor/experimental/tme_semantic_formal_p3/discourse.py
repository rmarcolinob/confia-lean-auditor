"""Source-validated discourse graph, independent of mathematical correctness."""
from dataclasses import dataclass
from enum import Enum
import json
import re
from confia_lean_auditor.student_claims.semantic import normalized, sha
from .source_adapter import clause_view, adapt_payload, literal_property
from .mapper import local_context, _anchor

VERSION='p3-discourse-v1'

class DiscourseState(str,Enum):
    ACTIVE='ACTIVE'
    SUPERSEDED='SUPERSEDED'
    NON_ADOPTED='NON_ADOPTED'
    AMBIGUOUS='AMBIGUOUS'

@dataclass(frozen=True)
class DiscourseDecision:
    evidence_id: str
    canonical_id: str
    state: str
    binding_valid: bool
    reason: str
    source_range: tuple
    assertion_range: tuple
    property_key: tuple
    model_signals_json: str
    supporting_spans: tuple = ()
    supersedes: tuple = ()
    superseded_by: tuple = ()

    @property
    def positive_credit_eligible(self):return self.binding_valid and self.state=='ACTIVE'

    @property
    def conflict_visible(self):return self.binding_valid and self.state in {'ACTIVE','AMBIGUOUS'}

    def as_dict(self):
        return dict(evidence_id=self.evidence_id,canonical_id=self.canonical_id,resolved_discourse_state=self.state,
            binding_valid=self.binding_valid,reason=self.reason,source_range=self.source_range,
            assertion_range=self.assertion_range,property_key=self.property_key,
            original_model_signals=json.loads(self.model_signals_json),supporting_spans=[json.loads(s) for s in self.supporting_spans],
            supersedes=self.supersedes,superseded_by=self.superseded_by,
            positive_credit_eligibility=self.positive_credit_eligible,conflict_visible=self.conflict_visible,
            policy_version=VERSION)

@dataclass(frozen=True)
class DiscourseSnapshot:
    source_sha256: str
    ledger_revision: str
    decisions: tuple

    def get(self,eid):return next((d for d in self.decisions if d.evidence_id==eid),None)
    def valid(self):return self.ledger_revision==sha([VERSION,self.source_sha256,[d.as_dict() for d in self.decisions]])


def _context(document,e):
    raw=normalized(e.source_span)
    # These patterns describe actual source scope; model flags are not consulted.
    if re.search(r'\b(?:talvez|nao sei|possivelmente)\b',raw):return 'AMBIGUOUS','uncertain_written_assertion'
    if re.search(r'\b(?:suponha|suponhamos|supondo|hipotese|hipotetic\w*|tentativa\s+(?:explicitamente\s+)?(?:abandonada|descartada)|citacao|enunciado|fosse|seria)\b',raw):
        return 'NON_ADOPTED','written_unadopted_scope'
    if re.search(r'\b(?:disse|afirmou|de acordo com|solucao de|afirmacao de|outra pessoa)\b|\bsegundo\s+(?!(?:compartimento|caso|ramo|sorteio|acionamento)\b)\w+',raw) or any(c in raw for c in '"“”'):
        return 'NON_ADOPTED','written_third_party_or_quotation'
    start=document.ranges[e.item_id][0]
    prefix=document.text[start:e.source_start].rsplit('\n\n',1)[-1]
    scope=False
    for line in prefix.splitlines():
        line=normalized(line).strip()
        if re.match(r'(?:afirmo|concluo|minha resposta|resposta final)',line):scope=False
        elif line.endswith(':') and re.search(r'hipotese|suponha|tentativa.*(?:abandon|descart)|citacao|enunciado|transcricao|nao e verdade|disse|afirmou|de acordo com|solucao de|segundo\s+(?!(?:compartimento|caso|ramo)\b)\w+',line):scope=True
    if scope:return 'NON_ADOPTED','written_nonadopted_header'
    return 'ACTIVE','literal_own_assertion'


def _incompatible(old,new):
    if not old or not new or old['property']!=new['property']:return False
    if old['kind']=='member' and new['kind']=='exact_set':return not set(old['members'])<=set(new['members'])
    if old['kind']=='exact_set' and new['kind']=='member':return not set(new['members'])<=set(old['members'])
    if old['kind']=='exact_set' and new['kind']=='exact_set':return set(old['members'])!=set(new['members'])
    if old['kind']==new['kind']=='math':
        # Canonical numeric value, not textual difference (6*6=36 vs 36).
        from confia_lean_auditor.core.math_canonical import parse_math
        def value(p):
            s=str(p.get('expression') or p.get('value')).split('=')[-1]
            f=parse_math(s)
            return f.canonical_form.to_dict() if f.status=='parsed' else None
        a,b=value(old),value(new)
        return a is not None and b is not None and a!=b
    # A revised choice of color is a change in the written selection, not a
    # claim that the machine has exactly one optimum.
    return old['kind']==new['kind']=='enum' and old['value']!=new['value']


def _written_range(text,match,base):
    """Translate normalized matching offsets back to original codepoint offsets.

    Normalization can expand Greek letters/superscripts; its offsets must never
    be added directly to original source coordinates.
    """
    def boundary(target):
        lo,hi=0,len(text)
        while lo<hi:
            mid=(lo+hi)//2
            if len(normalized(text[:mid]))<target:lo=mid+1
            else:hi=mid
        import unicodedata
        while lo<len(text) and unicodedata.combining(text[lo]):lo+=1
        return base+lo
    return (boundary(match.start()),boundary(match.end()))


class DiscourseStateResolver:
    def resolve(self,document,evidence):
        entries={}; views={}; adaptations=[]
        for e in sorted(evidence,key=lambda e:e.evidence_id):
            signals={k:getattr(e,k) for k in ('assertion_status','polarity','scope','hypothetical','abandoned','attributed_to_student','confidence')}
            try:
                v=clause_view(document,e);v,adaptation=adapt_payload(document,v);adaptations.append(adaptation)
                prop=literal_property(document,v)
                state,reason=_context(document,v)
                # Adoption needs a recognizable assertion/property, not just the
                # absence of a retraction marker or a model's subject label.
                anchored=prop is not None or _anchor(v,document) or bool(re.search(r'\b'+re.escape(v.subject)+r'\s*:',v.source_span))
                if state=='ACTIVE' and not anchored:state,reason='AMBIGUOUS','unresolved_property_binding'
                binding=True
            except ValueError as error:
                v=e;prop=None;state,reason='AMBIGUOUS',str(error);binding=False
            key=(e.item_id,prop['property'] if prop else e.subject)
            canonical=sha([sha(document.text),v.source_start,v.source_end,key,prop])
            entries[e.evidence_id]=dict(evidence_id=e.evidence_id,canonical_id=canonical,state=state,binding_valid=binding,
                reason=reason,source_range=(v.source_start,v.source_end),assertion_range=tuple(v.metadata.get('assertion_range',(v.source_start,v.source_end))),
                property_key=key,model_signals_json=json.dumps(signals,sort_keys=True),supporting_spans=(),supersedes=(),superseded_by=())
            views[e.evidence_id]=(v,prop)
        # Group source aliases before linking revisions. The native record must
        # inherit the very same graph, not a nearby semantic flag.
        groups={}
        for eid,d in entries.items():groups.setdefault(d['canonical_id'],[]).append(eid)
        ordered=sorted(groups,key=lambda c:(entries[groups[c][0]]['source_range'],c))
        for new_id in ordered:
            nid=groups[new_id][0];new=entries[nid];nv,np=views[nid]
            if new['state']!='ACTIVE' or not np:continue
            prior=[cid for cid in ordered if entries[groups[cid][0]]['source_range'][0]<new['source_range'][0]
                   and entries[groups[cid][0]]['property_key']==new['property_key']
                   and entries[groups[cid][0]]['state']=='ACTIVE']
            if not prior:continue
            old_id=prior[-1];oid=groups[old_id][0];old=entries[oid];ov,op=views[oid]
            between=document.text[old['source_range'][1]:new['source_range'][1]]
            raw=normalized(between)
            explicit=re.search(r'corrigindo|substitu\w*|retiro|(?:isso|isto) (?:esta|estava) errado|desconsidere\s+(?:a\s+(?:minha\s+)?afirmacao anterior|o que acabei de afirmar)|nao,\s*o correto',raw)
            implicit=re.search(r'na verdade',normalized(nv.source_span))
            immediate=document.text[old['source_range'][1]:new['source_range'][0]].strip(' \n\t\r.;')==''
            if re.search(r'\b(?:disse|afirmou|citacao|hipotese)\b',raw):continue
            if explicit:
                explicit_range=_written_range(between,explicit,old['source_range'][1])
                before_marker=raw[:explicit.start()].strip(' \n\r\t.;')
                marker_tail=raw[explicit.start():].split('\n',1)[0]
                before_marker=re.sub(r'^(?:pensando melhor|reconsiderando|apos a revisao)[,:\s]*','',before_marker)
                subject=new['property_key'][1]
                if subject.startswith(('estrategia_','contagem_')):
                    # A strategy revision can explicitly withdraw its color and
                    # count together. Ignore only bound companion clauses from
                    # that same case, never arbitrary intervening prose.
                    for companion in entries.values():
                        key=companion['property_key']
                        if (key[0]==new['property_key'][0] and key[1].startswith(('estrategia_','contagem_'))
                            and key[1].rsplit('_',1)[-1]==subject.rsplit('_',1)[-1]
                            and old['source_range'][1]<=companion['source_range'][0]
                            and companion['source_range'][1]<=explicit_range[0]):
                            a,b=companion['source_range']
                            before_marker=before_marker.replace(normalized(document.text[a:b]),'').strip(' \n\r\t.;')
                named_target=(subject in marker_tail or
                    subject=='inferiores_brancas' and bool(re.search(r'contagem.*inferior',marker_tail)))
                # A distant revision must identify its target. An indefinite
                # 'correcting a calculation' cannot silently replace whichever
                # previous value happens to have the same model subject.
                if (before_marker and not named_target or
                    re.search(r'nao (?:identifico|indico|especifico)|sem (?:identificar|indicar|especificar)',marker_tail)):
                    explicit=None
            if explicit:
                marker_end=explicit_range[1]
                # A marker followed by a separate, differently targeted claim
                # cannot silently withdraw this older property. Shared color +
                # count revisions remain a single strategy context.
                intervening=[entries[groups[c][0]] for c in ordered
                    if marker_end < entries[groups[c][0]]['source_range'][0] < new['source_range'][0]]
                def same_revision_family(key):
                    if key==new['property_key']:return True
                    old_subject,new_subject=key[1],new['property_key'][1]
                    return (old_subject.startswith(('estrategia_','contagem_'))
                        and new_subject.startswith(('estrategia_','contagem_'))
                        and old_subject.rsplit('_',1)[-1]==new_subject.rsplit('_',1)[-1])
                if any(not same_revision_family(d['property_key']) for d in intervening):explicit=None
            valid=bool(op and (explicit or implicit and immediate and _incompatible(op,np)))
            if not valid:continue
            marker=explicit or implicit
            marker_range=explicit_range if explicit else _written_range(nv.source_span,implicit,nv.source_start)
            support=(json.dumps(dict(old_range=old['source_range'],new_range=new['source_range'],
                          marker=marker[0],marker_range=marker_range,marker_source=document.text[marker_range[0]:marker_range[1]],relation='explicit_replacement' if explicit else 'incompatible_local_correction',
                          property_key=new['property_key'],direction='forward'),sort_keys=True),)
            for eid in groups[old_id]:entries[eid].update(state='SUPERSEDED',reason='validated_local_replacement',superseded_by=tuple(groups[new_id]),supporting_spans=support)
            for eid in groups[new_id]:entries[eid].update(supersedes=tuple(groups[old_id]),supporting_spans=support)
        # Explicit local withdrawal needs no invented replacement. It is
        # historical/non-adopted rather than false or superseded by a phantom.
        for eid,d in entries.items():
            if d['state']!='ACTIVE' or not d['binding_valid']:continue
            tail=document.text[d['source_range'][1]:document.ranges[d['property_key'][0]][1]]
            marker=re.match(r'^[\s.;]*(isso esta errado\b|retiro (?:essa|esta|a minha) (?:afirmacao|resposta|escolha)\b|desconsidere (?:a minha|a) afirmacao anterior\b)',normalized(tail))
            if marker:
                d.update(state='NON_ADOPTED',reason='explicit_local_withdrawal_without_replacement',
                    supporting_spans=(json.dumps(dict(marker=marker[0],after_range=d['source_range']),sort_keys=True),))
        decisions=tuple(DiscourseDecision(**entries[eid]) for eid in sorted(entries))
        snap=DiscourseSnapshot(sha(document.text),sha([VERSION,sha(document.text),[d.as_dict() for d in decisions]]),decisions)
        # A projection is derived locally; originals (including flags) remain in
        # the immutable ledger trace. The mapper receives the resolver receipt.
        projected=[]
        for e in evidence:
            d=snap.get(e.evidence_id);v=views[e.evidence_id][0]
            projected.append(v.model_copy(update=dict(assertion_status='asserted',hypothetical=False,abandoned=False,
                attributed_to_student=True,scope='main_argument',polarity='negative' if re.search(r'\b(?:nao|nunca|jamais)\s+(?:escolho|libera|produz|fornece|e|vale)',normalized(v.source_span)) else 'positive',
                metadata=dict(v.metadata,discourse_decision=d.as_dict(),ledger_revision=snap.ledger_revision))))
        ledger=[dict(original=e.model_dump(mode='json'),decision=snap.get(e.evidence_id).as_dict(),
                     adapted=next(v for v in projected if v.evidence_id==e.evidence_id).model_dump(mode='json')) for e in sorted(evidence,key=lambda e:e.evidence_id)]
        return snap,tuple(projected),ledger,adaptations
