"""P5 grounded replacement certificates, compact products and explicit carry-forward.

Only FactResults: the producer has no points. Independently known maxima never
supply a missing student argument. Global integer break is deterministic, not Lean.
"""
import re
import uuid
from dataclasses import asdict
from math import prod

from confia_lean_auditor.claims.common.fact_results import FactResultsBuilder
from confia_lean_auditor.core.math_canonical import equivalent, parse_math
from confia_lean_auditor.core.math_canonical.development import sum_development
from confia_lean_auditor.core.math_canonical.integer_structures import positive_multiset, multiset_product, product_form, written_factors
from confia_lean_auditor.core.math_canonical.rational import rational_value
from confia_lean_auditor.rubric.pauta.models import ConditionalContext
from confia_lean_auditor.student_claims.tme2_p5_digital import PROBLEM_ID, collect_tme2_p5_digital
from confia_lean_auditor.tme.p5_integer_break import partitions, sum11_maximum, normal_counts, optimal_forms, list_sum, list_size
from .real_algebra import check_real_record, lean_real_expression

VERSION='tme2-p5-check.v1'
REWRITES=('one_domain','one_sum','one_gain','domain','sum_preserved','increase','four_sum','four_product','twos_sum','twos_gain')


def expr(record): return record.canonical_form.value['expression']
def structure(record): return record.canonical_form.value['structure']
def equal(a,b): return equivalent(a,b).status=='equivalent'
def compare(a,b): return {'equivalent':'verified','not_equivalent':'refuted'}.get(equivalent(a,b).status,'unverified')


def conjunction(states):
    if 'technical_error' in states:return 'technical_error'
    if 'refuted' in states:return 'refuted'
    return 'verified' if states and all(s=='verified' for s in states) else 'unverified'


def relation_parts(text):
    parts=re.split(r'(<=|>=|=|<|>|≤|≥)',text)
    return tuple(p.strip() for p in parts) if len(parts)==3 else None


def render_relation(text):
    parts=relation_parts(text)
    if not parts:return None
    left,op,right=parts
    left=lean_real_expression(left,number_domain='Z',variables=('n','m','q'))
    right=lean_real_expression(right,number_domain='Z',variables=('n','m','q'))
    return f'{left} {dict(zip(("<=",">="),("≤","≥"))).get(op,op)} {right}' if left and right else None


def closed_relation_status(text):
    parts=relation_parts(text)
    if not parts:return 'unverified'
    a,op,b=parts; a,b=rational_value(a),rational_value(b)
    if a is None or b is None:return 'unverified'
    return 'verified' if {'=':a==b,'<':a<b,'>':a>b,'<=':a<=b,'>=':a>=b,'≤':a<=b,'≥':a>=b}[op] else 'refuted'


def relation_sides_match(text,left,right):
    parts=relation_parts(text)
    return bool(parts and ((equal(parts[0],left) and equal(parts[2],right)) or
                           (equal(parts[0],right) and equal(parts[2],left))))


class P5Checks(FactResultsBuilder):
    def __init__(self,digital,solution_id,use_lean,run_id):
        super().__init__(digital,solution_id,problem_id=PROBLEM_ID,checker_version=VERSION)
        if run_id is not None and not re.fullmatch(r'[A-Za-z0-9_-]{1,120}',run_id):
            raise ValueError('Unsafe run ID')
        self.run_id=(run_id or 'tme2-p5')+'-'+uuid.uuid4().hex
        self.use_lean=use_lean

    def select(self,item,key):
        return [r for r in self.digital.records if r.rubric_links==(item,) and r.source.attributable
                and r.source.grounding_status=='grounded' and r.canonical_form
                and r.canonical_form.family=='named_quantity' and r.canonical_form.subject==key]

    def state(self,fact):
        states={p['verification'].status for p in self.pending if p['fact_id']==fact}
        if 'technical_error' in states:return 'technical_error'
        if len(states)!=1:return 'unverified'
        return next(iter(states))

    def references(self,facts):
        ids=dict.fromkeys(i for p in self.pending if p['fact_id'] in facts for i in p['source_claim_ids'])
        return [self.records[i] for i in ids]

    def observe(self,fact,record,status,*,formal=None,mechanism='canonical_equivalence',**metadata):
        records=[record];check=None
        if self.use_lean and formal:
            statement,proof,negative,context=formal
            result=check_real_record(record,self.digital,collect=collect_tme2_p5_digital,
                statement=statement,proof=proof,refutation=negative,context=context,
                run_id=self.run_id,index=len(self.pending),number_domain='Z')
            if result:
                projected,checked=result;self.records[projected.record_id]=projected
                records.append(projected);check=asdict(checked)
                status,mechanism=checked.status,'student_lean'
                metadata.update(formal_context=context,formal_statement=statement)
        self.add(fact,records,status,mechanism=mechanism,check=check,
                 metadata={'student_asserted':[record.record_id],**metadata})

    def composite(self,fact,dependencies,*,extra=(),status=None,**metadata):
        records=self.references(dependencies)+list(extra)
        if not records:return
        state=conjunction([self.state(f) for f in dependencies])
        if status is not None:state=conjunction([state,status])
        self.add(fact,records,state,metadata={'student_argument_refs':[r.record_id for r in records],
            'engine_derived':True,'dependency_fact_ids':list(dependencies),**metadata})

    def closed(self,item,key,left,right,*,development=None,strict_gain=False):
        """Formalize exactly the written local relation, including false signs."""
        for r in self.select(item,key):
            text=expr(r);parts=relation_parts(text)
            if not relation_sides_match(text,left,right):
                self.observe(item+'.'+key,r,'unverified');continue
            if development and not development(parts):
                self.observe(item+'.'+key,r,'unverified',reason='No written replacement');continue
            status=closed_relation_status(text)
            if status=='verified' and parts[1] not in ({'<','>'} if strict_gain else {'='}):
                self.observe(item+'.'+key,r,'unverified',reason='Required relation not asserted');continue
            rendered=render_relation(text)
            formal=(rendered,'norm_num','norm_num',{'scope':'exact written local integer relation'}) if rendered else None
            self.observe(item+'.'+key,r,status,formal=formal)

    def number(self,item,key,expected,*,formal=False):
        for r in self.select(item,key):
            parts=expr(r).split('=');values=[rational_value(p) for p in parts]
            status='unverified' if None in values else 'verified' if all(v==expected for v in values) else 'refuted'
            cert=None;rendered=render_relation(expr(r))
            if formal and len(values)==2 and expected in values and rendered:
                cert=(rendered,'norm_num','norm_num',{'scope':'exact written count arithmetic','expected_count':expected})
            self.observe(item+'.'+key,r,status,formal=cert,expected_value=expected)

    def n_relations(self,item):
        for r in self.select(item,'domain'):
            self.observe(item+'.domain',r,'verified' if equal(expr(r),'n>=5') else 'unverified')
        for r in self.select(item,'sum_preserved'):
            parts=relation_parts(expr(r));valid=False
            if parts and parts[1]=='=':
                valid=any(equal(endpoint,'n') and sum_development(other,['3','n-3'])
                          for endpoint,other in ((parts[0],parts[2]),(parts[2],parts[0])))
            status='verified' if valid else 'unverified'
            formal=None;rendered=render_relation(expr(r))
            if valid and rendered:
                formal=(f'∀ n : ℤ, {rendered}','intro n\n  ring',
                        'push_neg\n  refine ⟨5, ?_⟩\n  norm_num',{'scope':'written sum-preserving split'})
            self.observe(item+'.sum_preserved',r,status,formal=formal)
        for r in self.select(item,'increase'):
            positive=equal(expr(r),'3*(n-3)>n')
            negative=any(equal(expr(r),p) for p in ('3*(n-3)<n','3*(n-3)<=n'))
            state='verified' if positive else 'refuted' if negative else 'unverified'
            if self.state(item+'.domain')!='verified':state='unverified'
            formal=None;rendered=render_relation(expr(r))
            if self.state(item+'.domain')=='verified' and (positive or negative) and rendered:
                formal=(f'∀ n : ℤ, n ≥ 5 → {rendered}','intro n hn\n  try omega',
                    'push_neg\n  refine ⟨5, ?_, ?_⟩ <;> norm_num',
                    {'scope':'local replacement inequality; not global integer break',
                     'domain_source_ids':[r.record_id for r in self.select(item,'domain')]})
            self.observe(item+'.increase',r,state,formal=formal)
        # Modular difference proof is an alternative to the direct inequality.
        for r in self.select(item,'difference'):
            parts=relation_parts(expr(r))
            valid=bool(parts and parts[1]=='=' and relation_sides_match(expr(r),'3*(n-3)-n','2*n-9'))
            if not valid:continue
            positives=self.select(item,'positive_difference')
            for p in positives:
                state='verified' if equal(expr(p),'2*n-9>0') else 'unverified'
                state=conjunction([state,self.state(item+'.domain')])
                self.add(item+'.increase',[r,p,*self.select(item,'domain')],state,
                    metadata={'student_asserted':[r.record_id,p.record_id],
                              'engine_derived':'difference equality plus explicit positivity under n>=5'})

    def replacements(self,item):
        self.n_relations(item)
        for r in self.select(item,'one_domain'):
            self.observe(item+'.one_domain',r,'verified' if equal(expr(r),'m>=1') else 'unverified')
        for r in self.select(item,'one_sum'):
            parts=relation_parts(expr(r))
            valid=bool(parts and parts[1]=='=' and relation_sides_match(expr(r),'1+m','m+1')
                       and any(sum_development(p,['1','m']) for p in (parts[0],parts[2])))
            self.observe(item+'.one_sum',r,'verified' if valid else 'unverified')
        for r in self.select(item,'one_gain'):
            # Do not promote a particular true inequality (2>1) to the
            # quantified merge argument merely because both normalize to true.
            status='verified' if (equal(expr(r),'m+1>m') and
                relation_sides_match(expr(r),'m+1','m')) else 'unverified'
            self.observe(item+'.one_gain',r,status)
        self.closed(item,'four_sum','4','2+2',development=lambda p:any(positive_multiset(s)=={'2':2} for s in (p[0],p[2])))
        self.closed(item,'four_product','4','2*2',development=lambda p:any(written_factors(s)=={'2':2} for s in (p[0],p[2])))
        self.closed(item,'twos_sum','2+2+2','3+3',development=lambda p:
            {tuple((positive_multiset(s) or {}).items()) for s in (p[0],p[2])}=={(('2',3),),(('3',2),)})
        self.closed(item,'twos_gain','2*2*2','3*3',strict_gain=True)

    def a(self):
        for r in self.select('a','candidate'):
            counts=structure(r)
            value=prod(int(k)**v for k,v in counts.items()) if list_sum(counts)==11 else None
            self.observe('a.candidate',r,value==sum11_maximum(),mechanism='deterministic',
                engine_derived_maximum=sum11_maximum(),student_maximality_argument=False)
        for r in self.select('a','product'):
            parts=expr(r).split('=')
            factors=written_factors(parts[0]) or {}
            # Accept genuine regrouping, e.g. (2*3)*(3*3) or 6*9, while
            # keeping a bare value or 54*1 from fabricating a calculation.
            valid=(len(parts)==2 and sum(v for k,v in factors.items() if k!='1')>=2
                   and product_form(parts[0])==multiset_product(normal_counts(11)))
            status=closed_relation_status(expr(r)) if valid else 'unverified'
            rendered=render_relation(expr(r))
            formal=(rendered,'norm_num','norm_num',{'scope':'student candidate product only'}) if valid and rendered else None
            self.observe('a.product',r,status,formal=formal)
        for table in self.select('a','enumeration'):
            observed={tuple((int(k),v) for k,v in counts.items()) for counts in structure(table)}
            expected={tuple((int(k),v) for k,v in positive_multiset(str(p)).items()) for p in partitions(11)}
            for conclusion in self.select('a','enum_max'):
                value=rational_value(expr(conclusion))
                if value is None:state='unverified'
                else:state='verified' if observed==expected and value==sum11_maximum() else 'refuted'
                self.add('a.enumeration',[table,conclusion],state,metadata={
                    'student_supplied_enumeration':True,'partitions_checked':len(expected),
                    'engine_derived_maximum':sum11_maximum(),'global_formalized':False})
        self.replacements('a')
        for r in self.select('a','normal_list'):
            self.observe('a.normal_list',r,structure(r)==normal_counts(11),mechanism='deterministic')
        self.composite('a.structural_max',tuple('a.'+k for k in (*REWRITES,'normal_list')),
            global_formalized=False,argument='Finite improving replacements and sum-11 normal form')

    def b(self):
        self.n_relations('b')
        for key,expected in [('old_contribution','n'),('new_contribution','3*(n-3)')]:
            for r in self.select('b',key):self.observe('b.'+key,r,compare(expr(r),expected))
        self.composite('b.comparison',('b.old_contribution','b.new_contribution'))

    def c(self):
        self.replacements('c')
        self.composite('c.no_ones',('c.one_domain','c.one_sum','c.one_gain'),
            argument='Merge 1 with another positive entry; preserves sum and increases product')
        self.composite('c.no_ge5',('c.domain','c.sum_preserved','c.increase'),
            argument='Replace n>=5 by 3 and n-3, both positive')
        self.number('c','threes_count',674);self.number('c','twos_count',2)
        for r in self.select('c','decomposition'):
            parts=relation_parts(expr(r));status='unverified'
            if parts and parts[1]=='=':
                developed=any(equal(a,'2026') and (sum_development(b,['3*674','2','2']) or sum_development(b,['3*674','4'])) for a,b in ((parts[0],parts[2]),(parts[2],parts[0])))
                status=closed_relation_status(expr(r)) if developed else ('refuted' if closed_relation_status(expr(r))=='refuted' else 'unverified')
            rendered=render_relation(expr(r))
            formal=(rendered,'norm_num','norm_num',{'scope':'written 2026 decomposition'}) if rendered and status!='unverified' else None
            self.observe('c.decomposition',r,status,formal=formal)
        for r in self.select('c','max_product'):
            self.observe('c.max_product',r,structure(r)==multiset_product(normal_counts(2026)),
                mechanism='canonical_equivalence',global_formalized=False,canonical_method='prime-exponent map')
        for residue,twos,threes in ((0,'0','q'),(1,'2','q-1'),(2,'1','q')):
            for suffix,expected in (('twos',twos),('threes',threes)):
                for r in self.select('c',f'residue{residue}_{suffix}'):
                    self.observe(f'c.residue{residue}_{suffix}',r,compare(expr(r),expected))
        residue_facts=tuple(f'c.residue{r}_{s}' for r in range(3) for s in ('twos','threes'))
        self.composite('c.general_rule',residue_facts,argument='Exhaustive residues of s=3q+r after justified normal form')
        for r in self.select('c','quotient'):
            parts=relation_parts(expr(r));valid=bool(parts and parts[1]=='=' and any(equal(a,'2026') and sum_development(b,['3*675','1']) for a,b in ((parts[0],parts[2]),(parts[2],parts[0]))))
            self.observe('c.quotient',r,'verified' if valid else 'unverified')
        self.composite('c.general_complete',('c.no_ones','c.no_ge5','c.four_sum','c.four_product',
            'c.twos_sum','c.twos_gain','c.general_rule','c.quotient','c.max_product'),
            global_formalized=False,argument='Justified integer-break normal form + exhaustive residue rule + application to 2026')

    def d(self):
        forms=optimal_forms(2026)
        for key,expected in zip(('list_twos','list_four'),forms):
            for r in self.select('d',key):self.observe('d.'+key,r,structure(r)==expected,
                mechanism='deterministic',engine_derived_optimal_forms= forms)
        self.closed('d','four_sum','4','2+2',development=lambda p:any(positive_multiset(s)=={'2':2} for s in (p[0],p[2])))
        self.closed('d','four_product','4','2*2',development=lambda p:any(written_factors(s)=={'2':2} for s in (p[0],p[2])))
        for r in self.select('d','only_forms'):
            self.composite('d.uniqueness',('d.list_twos','d.list_four','d.four_sum','d.four_product'),extra=(r,),
                argument='Only one pair of twos in the normal maximizer can merge to a four',global_formalized=False)
        self.number('d','size_twos',list_size(forms[0]),formal=True)
        self.number('d','size_four',list_size(forms[1]),formal=True)
        for r in self.select('d','different_sizes'):
            status=closed_relation_status(expr(r)) if relation_sides_match(expr(r),'676','675') else 'unverified'
            parts=relation_parts(expr(r))
            if parts and parts[1] not in {'<','>'}:status='refuted' if parts[1]=='=' else 'unverified'
            self.observe('d.different_sizes',r,status)
        self.composite('d.sizes',('d.size_twos','d.size_four','d.different_sizes'))
        self.carry_forward()

    def carry_forward(self):
        prior=self.select('c','threes_count')
        adopted=self.select('d','cf_adopt_threes')
        if len(prior)!=1 or len(adopted)!=1 or self.state('c.threes_count')!='refuted':return
        value=rational_value(expr(prior[0]));adoption=rational_value(expr(adopted[0]))
        if value is None or value.denominator!=1 or not 1<=value<=10000 or adoption!=value:return
        ctx=ConditionalContext(rule_id='d.sizes_cf',prior_obligation_id='c.threes_count',adopted_result_ref=prior[0].record_id)
        def add(fact,records,status,**metadata):
            self.add(fact,records,status,metadata={'explicit_conditional_context':ctx.model_dump(),**metadata})
            self.pending[-1]['conditional_on']=ctx
        add('d.cf_adoption',[prior[0],adopted[0]],True)
        dependencies=self.select('d','cf_dependency')
        if len(dependencies)!=1:return
        add('d.cf_dependency',[adopted[0],dependencies[0]],True)
        twos,four,different=(self.select('d',k) for k in ('cf_size_twos','cf_size_four','cf_different_sizes'))
        if len(twos)!=1 or len(four)!=1 or len(different)!=1:return
        valid=True
        for record,offset in ((twos[0],2),(four[0],1)):
            parts=relation_parts(expr(record))
            valid=valid and bool(parts and parts[1]=='=' and closed_relation_status(expr(record))=='verified'
                and rational_value(parts[2])==value+offset and sum_development(parts[0],[str(int(value)),str(offset)]))
        parts=relation_parts(expr(different[0]))
        valid=valid and bool(parts and parts[1] in {'>','<'} and closed_relation_status(expr(different[0]))=='verified'
            and relation_sides_match(expr(different[0]),str(int(value+2)),str(int(value+1))))
        add('d.cf_coherence',[adopted[0],dependencies[0],twos[0],four[0],different[0]],valid,
            adopted_threes=int(value),absolute_counts_correct=False)


def verify_tme2_p5_digital(digital,solution_id,*,use_lean=True,run_id=None):
    items={k:digital.source_text[a:b] for k,(a,b) in digital.item_ranges.items()}
    if collect_tme2_p5_digital(items)!=digital:raise ValueError('Digital source/claim projection changed')
    checks=P5Checks(digital,solution_id,use_lean,run_id)
    checks.a();checks.b();checks.c();checks.d()
    return checks.finish()
