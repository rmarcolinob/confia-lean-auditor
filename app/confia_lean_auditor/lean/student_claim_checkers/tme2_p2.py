"""P2 deterministic diagram reasoning and grounded text mathematics. No points."""
import hashlib
import re
import uuid
from dataclasses import asdict
from fractions import Fraction

from confia_lean_auditor.claims.common.fact_results import FactResultsBuilder
from confia_lean_auditor.core.math_canonical import equivalent,parse_math
from confia_lean_auditor.core.math_canonical.rational import rational_value
from confia_lean_auditor.core.math_canonical.combinatorial import lean_combinatorial_expression,two_count_factors
from confia_lean_auditor.student_claims.tme2_p2_digital import PROBLEM_ID,collect_tme2_p2_text
from confia_lean_auditor.tme.p2_diagram import TME2P2DiagramState,inspect_diagram,admissible_cases,feasible_pairs,diagram_record
from .real_algebra import check_real_record,lean_real_expression

VERSION='tme2-p2-check.v1'
CASES=admissible_cases()


def expr(r):return r.canonical_form.value['expression']
def eq(a,b):return equivalent(a,b).status=='equivalent'
def compare(a,b):return {'equivalent':'verified','not_equivalent':'refuted'}.get(equivalent(a,b).status,'unverified')
def structure(r):return r.canonical_form.value['structure']
def conjunction(states):
    if 'technical_error' in states:return 'technical_error'
    if 'refuted' in states:return 'refuted'
    return 'verified' if states and all(s=='verified' for s in states) else 'unverified'
def render(s,domain='Z'):return lean_real_expression(s,number_domain=domain,variables=('x','S'))


def inspect_pairs(pairs,center,common):
    values=[n for p in pairs for n in p]
    return (len(pairs)==4 and sorted(values+[center])==list(range(1,10))
            and all(a+b+center==common for a,b in pairs))


def modular_candidates(data):
    forms=[parse_math(data[k]).canonical_form for k in ('left','right')]
    if any(f is None or f.affine is None or not set(f.variables)<={'x'} for f in forms):return None
    result=[]
    for x in range(1,10):
        values=[sum(Fraction(v)*(x if k=='x' else 1) for k,v in f.affine) for f in forms]
        if any(v.denominator!=1 for v in values):return None
        if (values[0]-values[1])%data['modulus']==0:result.append(x)
    return set(result)


class P2Checks(FactResultsBuilder):
    def __init__(self,digital,solution_id,use_lean,run_id):
        super().__init__(digital,solution_id,problem_id=PROBLEM_ID,checker_version=VERSION)
        if run_id is not None and not re.fullmatch(r'[A-Za-z0-9_-]{1,120}',run_id):raise ValueError('Unsafe run ID')
        self.run_id=(run_id or 'tme2-p2')+'-'+uuid.uuid4().hex
        self.use_lean=use_lean

    def select(self,item,key):
        return [r for r in self.digital.records if r.rubric_links==(item,) and r.source.attributable
            and r.source.grounding_status=='grounded' and r.canonical_form
            and r.canonical_form.family=='named_quantity' and r.canonical_form.subject==key]

    def state(self,fact):
        states={p['verification'].status for p in self.pending if p['fact_id']==fact}
        if 'technical_error' in states:return 'technical_error'
        return next(iter(states)) if len(states)==1 else 'unverified'

    def refs(self,facts):
        return list(dict.fromkeys(i for p in self.pending if p['fact_id'] in facts for i in p['source_claim_ids']))

    def observe(self,fact,record,status,*,formal=None,mechanism='canonical_equivalence',**metadata):
        refs=[record];check=None
        if self.use_lean and formal:
            statement,proof,negative,context,domain=formal
            result=check_real_record(record,self.digital,collect=collect_tme2_p2_text,
                statement=statement,proof=proof,refutation=negative,context=context,
                run_id=self.run_id,index=len(self.pending),number_domain=domain)
            if result:
                projected,checked=result;self.records[projected.record_id]=projected
                refs.append(projected);check=asdict(checked);status,mechanism=checked.status,'student_lean'
                metadata.update(formal_statement=statement,formal_context=context)
        self.add(fact,refs,status,mechanism=mechanism,check=check,metadata={'student_asserted':[record.record_id],**metadata})

    def value(self,item,key,expected):
        for r in self.select(item,key):
            values=[rational_value(p) for p in expr(r).split('=')]
            state='unverified' if None in values else 'verified' if all(v==expected for v in values) else 'refuted'
            self.observe(item+'.'+key,r,state)

    def pair_facts(self,item,record,center,common):
        pairs=structure(record)
        valid=inspect_pairs(pairs,center,common)
        self.observe(item+'.pairs',record,valid,mechanism='deterministic',opposite_pairs=pairs,orientation_ignored=True)
        if item=='a' and len(pairs)==4 and all(a+b==10 for a,b in pairs):
            self.observe('a.pair_sum',record,True,mechanism='deterministic',engine_derived='All four explicitly supplied pairs sum to 10')

    def configuration(self,item,record,state):
        required=5 if item=='a' else None
        result=inspect_diagram(state,required_center=required)
        mechanism=dict(mechanism='deterministic',verification_kind='deterministic_diagram' if record.claim_type=='diagram_state' else 'deterministic_explicit_placement',
            diagram_metrics=result,source_ref=getattr(record.source,'source_ref',None),global_geometry_formalized=False)
        complete_status=result['valid'] if result['complete'] else 'unverified'
        if item=='a':
            self.observe('a.complete_configuration',record,complete_status,**mechanism)
            self.observe('a.placement',record,complete_status,**mechanism)
            if result['complete']:
                pairs=result['opposite_pairs']
                self.observe('a.pairs',record,inspect_pairs(pairs,5,15) and state.center==5,**mechanism)
                self.observe('a.pair_sum',record,state.center==5 and all(a+b==10 for a,b in pairs),**mechanism)
        elif item=='b':
            if state.center in {1,5,9}:
                self.observe(f'b.realizable_{state.center}',record,complete_status,**mechanism)
        elif item=='c' and result['complete']:
            self.observe('c.max_center',record,state.center==9,**mechanism)
            self.observe('c.max_sum',record,result['common_line_sum']==18,**mechanism)
            self.observe('c.pairs',record,state.center==9 and inspect_pairs(result['opposite_pairs'],9,18),**mechanism)

    def diagrams(self,diagrams):
        digest=hashlib.sha256(self.digital.source_text.encode()).hexdigest()
        for item,entries in diagrams.items():
            for index,entry in enumerate(entries):
                r=diagram_record(entry,item,digest,index);self.records[r.record_id]=r
                if r.source.attributable:self.configuration(item,r,TME2P2DiagramState.model_validate(r.source.payload))

    def a(self):
        self.value('a','pair_sum',10);self.value('a','line_sum',15)
        for r in self.select('a','pairs'):self.pair_facts('a',r,5,15)
        for r in self.select('a','placement'):
            mapping=structure(r)
            try:
                state=TME2P2DiagramState(center=mapping.get('center'),positions={k:v for k,v in mapping.items() if k!='center'})
            except ValueError:
                self.observe('a.placement',r,'unverified');continue
            self.configuration('a',r,state)

    def b(self):
        for r in self.select('b','balance_relation'):
            self.observe('b.balance_relation',r,compare(expr(r),'4*S=45+3*x'),
                mechanism='deterministic',engine_derived_context='sum(1..9)=45; center occurs four times, others once')
        for r in self.select('b','sum_formula'):
            parts=expr(r).split('=');rhs=parts[-1]
            parsed=parse_math(rhs).canonical_form
            scope=len(parts)==1 or len(parts)==2 and eq(parts[0],'S')
            scope=scope and parsed is not None and set(parsed.variables)<={'x'}
            state=compare(rhs,'(45+3*x)/4') if scope else 'unverified'
            formal=None;right=render(rhs,'R') if scope else None
            if right and state in {'verified','refuted'} and self.state('b.balance_relation')=='verified':
                formal=(f'∀ x S : ℝ, 4*S=45+3*x → S={right}',
                    'intro x S hs\n  try linarith',
                    'push_neg\n  first | (solve | refine ⟨5, 15, ?_, ?_⟩ <;> norm_num) | (solve | refine ⟨1, 12, ?_, ?_⟩ <;> norm_num)',
                    {'student_premise_refs':self.refs(('b.balance_relation',)),'scope':'algebraic isolation of common sum'},'R')
            self.observe('b.sum_formula',r,state,formal=formal)
        for r in self.select('b','integral_sum'):self.observe('b.integral_sum',r,True,mechanism='deterministic')
        for r in self.select('b','modular_condition'):
            candidates=modular_candidates(structure(r))
            self.observe('b.modular_condition',r,'unverified' if candidates is None else candidates=={x for x,_ in CASES},
                mechanism='deterministic',finite_domain=list(range(1,10)))
        for r in self.select('b','centers'):
            actual=set(r.canonical_form.value['value']);expected={x for x,_ in CASES}
            basis=['b.modular_condition'] if self.state('b.modular_condition')=='verified' else ['b.integral_sum',
                'b.balance_relation' if self.state('b.balance_relation')=='verified' else 'b.sum_formula']
            justified=all(self.state(f)=='verified' for f in basis)
            state=('verified' if actual==expected else 'refuted') if justified else 'unverified'
            formal=None
            if state=='verified':
                choices=' ∨ '.join(f'x={n}' for n in sorted(actual))
                formal=(f'∀ x S : ℤ, 1≤x → x≤9 → 4*S=45+3*x → ({choices})',
                    'intro x S hlo hhi hs\n  try omega',
                    'push_neg\n  first | (solve | refine ⟨1, 12, ?_, ?_, ?_, ?_⟩ <;> norm_num) | (solve | refine ⟨9, 18, ?_, ?_, ?_, ?_⟩ <;> norm_num)',
                    {'scope':'necessary center alternatives; completeness and realizability checked separately',
                     'student_argument_refs':self.refs(basis),'problem_domain':'integers 1 through 9'},'Z')
            self.observe('b.centers',r,state,formal=formal,engine_checked_exact_set=sorted(expected),argument_refs=self.refs(basis))
        for r in self.select('b','admissible_center'):
            n=rational_value(expr(r))
            if n is None or n.denominator!=1 or abs(n)>10000:self.observe('b.admissible_center',r,'unverified');continue
            n=int(n);witness=(45+3*n)//4
            statement=f'∃ S : ℤ, (1≤({n}:ℤ) ∧ ({n}:ℤ)≤9) ∧ 4*S=45+3*({n}:ℤ)'
            formal=(statement,f'refine ⟨{witness}, ?_, ?_⟩ <;> norm_num',
                'rintro ⟨S, hb, hs⟩\n  omega',{'scope':'admissibility of this asserted center only'},'Z')
            self.observe('b.admissible_center',r,n in {x for x,_ in CASES},formal=formal)
        for r in self.select('b','center_sums'):
            pairs=structure(r);state=set(map(tuple,pairs))==set(CASES) and len(pairs)==3
            formal=None
            if len(pairs)==3 and {p[0] for p in pairs}=={1,5,9}:
                implications=' ∧ '.join(f'(x={x} → S={s})' for x,s in pairs)
                formal=(f'∀ x S : ℤ, 4*S=45+3*x → ({implications})',
                    "intro x S hs\n  repeat' constructor\n  all_goals intro hx\n  all_goals try omega",
                    'push_neg\n  first | (solve | refine ⟨1, 12, ?_, ?_⟩ <;> norm_num) | (solve | refine ⟨5, 15, ?_, ?_⟩ <;> norm_num) | (solve | refine ⟨9, 18, ?_, ?_⟩ <;> norm_num)',
                    {'scope':'three asserted center/common-sum implications; not diagram recognition'},'Z')
            self.observe('b.center_sums',r,state,formal=formal)
        for r in self.select('b','sum_at_five'):
            value=rational_value(expr(r))
            if value is None or value.denominator!=1:self.observe('b.sum_at_five',r,'unverified');continue
            formal=(f'∀ S : ℤ, 4*S=60 → S={int(value)}','intro S hs\n  try omega',
                    'push_neg\n  refine ⟨15, ?_, ?_⟩ <;> norm_num',{'scope':'asserted sum for center five'},'Z')
            self.observe('b.sum_at_five',r,value==15,formal=formal)
        for center,common in CASES:
            for r in self.select('b',f'realizable_{center}'):
                self.observe(f'b.realizable_{center}',r,inspect_pairs(structure(r),center,common),
                    mechanism='deterministic',engine_derived='These four explicit opposite pairs construct a realization')

    def counting(self,key,expected):
        for r in self.select('c',key):
            form=structure(r);values=[rational_value(p) for p in form['expanded_parts']]
            state='unverified' if None in values else 'verified' if all(v==expected for v in values) else 'refuted'
            formal=None;rendered=[lean_combinatorial_expression(p) for p in form['original_parts']]
            # A true equality with an unrelated count is not a formal proof of this obligation.
            if len(values)>1 and expected in values and all(rendered):
                statement=' ∧ '.join(f'({a}={b})' for a,b in zip(rendered,rendered[1:]))
                formal=(statement,'norm_num','norm_num',{'scope':'exact written arithmetic, including Nat.factorial'},'Z')
            self.observe('c.'+key,r,state,formal=formal)

    def c(self):
        self.value('c','max_center',9);self.value('c','max_sum',18)
        for r in self.select('c','pairs'):self.pair_facts('c',r,9,18)
        self.counting('pair_permutations',24);self.counting('pair_orientations',16);self.counting('total',384)
        for r in self.select('c','counting_product'):
            form=structure(r);values=[rational_value(p) for p in form['expanded_parts']]
            construction=two_count_factors(form['original_parts'][0])
            state=('verified' if all(v==384 for v in values) else 'refuted') if construction and None not in values else 'unverified'
            formal=None;rendered=[lean_combinatorial_expression(p) for p in form['original_parts']]
            if construction and len(values)>1 and all(rendered):
                formal=(' ∧ '.join(f'({a}={b})' for a,b in zip(rendered,rendered[1:])),
                    'norm_num','norm_num',{'scope':'written product of pair-distribution and orientation counts'},'Z')
            self.observe('c.counting_product',r,state,formal=formal,
                deterministic_combinatorics={'four_distinct_lines':24,'four_independent_orientations':16})


def verify_tme2_p2(digital,diagrams,solution_id,*,use_lean=True,run_id=None):
    texts={k:digital.source_text[a:b] for k,(a,b) in digital.item_ranges.items()}
    if collect_tme2_p2_text(texts)!=digital:raise ValueError('Digital source/claim projection changed')
    checks=P2Checks(digital,solution_id,use_lean,run_id)
    checks.a();checks.b();checks.c();checks.diagrams(diagrams)
    return checks.finish()
