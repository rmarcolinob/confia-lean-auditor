"""Paired attribution, retaining strict fingerprints and raw observations."""
import collections,csv,difflib,hashlib,json,pathlib,re,subprocess
R=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
O=R/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
B=pathlib.Path('/private/tmp/confia-r1-attribution-baseline-5aa7344')
def read(name): return json.loads((O/name).read_text())
def save(name,x): (O/name).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def digest(x): return hashlib.sha256(x).hexdigest()
def loadrun(label):
    run=read(label+'-results.json')
    calls=[json.loads(l) for l in (O/(label+'-lean.jsonl')).read_text().splitlines()] if (O/(label+'-lean.jsonl')).exists() else []
    return run,{r['nodeid']:r for r in run['tests']},calls
def failed(t): return next((p for p in t['phases'] if p['outcome']=='failed'),{})
def attribution_trace(t):
    # Normalize run provenance only. Strict raw observations stay unchanged.
    s=failed(t).get('normalized_longrepr','')
    s=re.sub(r'(?<=artifacts/student_claim_checks/)\d{8}T\d{6}_\d+_student_claims','<RUN>_student_claims',s)
    s=re.sub(r"manifest_id='rep_[0-9a-f]{32}'","manifest_id='<MANIFEST_ID>'",s)
    s=re.sub(r'generated_at=datetime\.datetime\([^)]*\)','generated_at=<GENERATED_AT>',s)
    s=re.sub(r"manifest_sha256='[0-9a-f]{64}'","manifest_sha256='<MANIFEST_SHA256>'",s)
    s=re.sub(r'(?<=artifacts/student_claim_checks/)tme2-p4-[0-9a-f]{32}','tme2-p4-<RUN_UUID>',s)
    # FactResultsBuilder hashes the randomly generated solution_id into these
    # tokens. Consistent alpha-renaming preserves their reference graph.
    tokens={}
    def token(match):
        suffix=match.group(2)
        if suffix not in tokens: tokens[suffix]=len(tokens)
        return match.group(1)+'<VERIFICATION_'+str(tokens[suffix])+'>'
    s=re.sub(r'(tme2-p4-check\.v1:|check:)([0-9a-f]{20})',token,s)
    return s
def compare(b,r):
    bf,rf=failed(b),failed(r)
    same_assertion=bf.get('assertion_fingerprint')==rf.get('assertion_fingerprint')
    same_trace=bf.get('traceback_fingerprint')==rf.get('traceback_fingerprint')
    same_env=b['lean_environment_fingerprints']==r['lean_environment_fingerprints']
    ab,ar=attribution_trace(b),attribution_trace(r)
    same_attribution=ab==ar
    bs,rs=b['status'],r['status']
    if bs=='PASS' and rs in ('FAIL','ERROR'): cls='PASS_BASELINE_FAIL_R1'
    elif bs in ('FAIL','ERROR') and rs=='PASS': cls='FAIL_BASELINE_PASS_R1'
    elif bs==rs=='PASS': cls='PASS_BOTH'
    elif bs==rs=='SKIP': cls='SKIP_BOTH_NOT_EXECUTED'
    elif bs==rs=='FAIL': cls='FAIL_BOTH_SAME_FINGERPRINT' if same_attribution and same_env else 'FAIL_BOTH_DIFFERENT_FINGERPRINT'
    else: cls='NOT_COMPARABLE'
    return {'nodeid':b['nodeid'],'baseline_status':bs,'r1_status':rs,'classification':cls,'same_assertion_fingerprint':same_assertion,'same_full_traceback_fingerprint':same_trace,'same_attribution_traceback_fingerprint':same_attribution,'baseline_attribution_fingerprint':digest(ab.encode()),'r1_attribution_fingerprint':digest(ar.encode()),'same_lean_environment_fingerprints':same_env,'baseline_assertion_fingerprint':bf.get('assertion_fingerprint'),'r1_assertion_fingerprint':rf.get('assertion_fingerprint'),'baseline_traceback_fingerprint':bf.get('traceback_fingerprint'),'r1_traceback_fingerprint':rf.get('traceback_fingerprint'),'baseline_failure_site':{k:v for k,v in (bf.get('crash') or {}).items() if k!='message'},'r1_failure_site':{k:v for k,v in (rf.get('crash') or {}).items() if k!='message'}}

br,bt,bc=loadrun('baseline'); rr,rt,rc=loadrun('r1')
nodes=read('failure-nodeids.json')
assert set(bt)==set(rt)==set(nodes) and br['collected']==rr['collected']==nodes
assert not br['collection_errors'] and not rr['collection_errors']
orig={r['nodeid']:r for r in read('original-inventory.json')['failures']}
rows=[compare(bt[n],rt[n]) for n in nodes]
formal=[]; inventory=[]
mathlib_message="mathlib: checking out revision '8f9d9cff6bd728b17a24e163c9402775d9e6a365'"
for row in rows:
    n=row['nodeid']; family=orig[n]['preliminary_family']
    b_calls=[c for c in bc if c['nodeid']==n and '--version' not in c['command']]
    r_calls=[c for c in rc if c['nodeid']==n and '--version' not in c['command']]
    cause={'CAPTURE_SCHEMA':'PREEXISTING_SCHEMA_PAGE_LIMIT_3_VS_50','UI_CONTRACT':'PREEXISTING_UI_LABEL_EXPECTATION' if 'test_ui_01' in n else 'PREEXISTING_UI_STICKY_EXPECTATION'}.get(family,'UNRESOLVED_FORMAL')
    if family=='FORMAL_LEAN':
        both_environment=bool(b_calls and r_calls) and all(c.get('returncode')==1 and mathlib_message in c.get('stderr','') and "external command 'git' exited with code 1" in c.get('stderr','') for c in b_calls+r_calls)
        if both_environment: cause='PREEXISTING_MATHLIB_CHECKOUT_FAILURE'
        f={'nodeid':n,'both_runs_mathlib_checkout_failure':both_environment,'baseline_verification_calls':len(b_calls),'r1_verification_calls':len(r_calls),'baseline_environment_fingerprints':sorted(set(c['environment_fingerprint'] for c in b_calls)),'r1_environment_fingerprints':sorted(set(c['environment_fingerprint'] for c in r_calls)),'same_verification_source_sequence':[c.get('source_sha256') for c in b_calls]==[c.get('source_sha256') for c in r_calls],'baseline_source_sha256_sequence':[c.get('source_sha256') for c in b_calls],'r1_source_sha256_sequence':[c.get('source_sha256') for c in r_calls],'assertion_fingerprints':{'baseline':row['baseline_assertion_fingerprint'],'r1':row['r1_assertion_fingerprint']},'traceback_fingerprints':{'baseline':row['baseline_traceback_fingerprint'],'r1':row['r1_traceback_fingerprint']}}
        formal.append(f)
        f['attribution_fingerprints']={'baseline':row['baseline_attribution_fingerprint'],'r1':row['r1_attribution_fingerprint']}
    row['cause']=cause
    inventory.append({'nodeid':n,'original_status':'FAIL','family':family,'cause':cause,'baseline_status':bt[n]['status'],'r1_status':rt[n]['status'],'classification':row['classification'],'original_assertion_excerpt':orig[n]['assertion_excerpt'],'baseline_failure_site':row['baseline_failure_site'],'r1_failure_site':row['r1_failure_site'],'evidence':['original-inventory.json','baseline-results.json','r1-results.json']+(['baseline-lean.jsonl','r1-lean.jsonl'] if family=='FORMAL_LEAN' else ['nonformal-evidence.json'])})
save('failure-inventory.json',{'schema':'r1-failure-inventory.v1','count':len(inventory),'failures':inventory})
save('paired-comparison.json',{'schema':'r1-paired-comparison.v1','rows':rows,'counts':dict(collections.Counter(r['classification'] for r in rows)),'PASS_BASELINE_FAIL_R1':[r['nodeid'] for r in rows if r['classification']=='PASS_BASELINE_FAIL_R1']})
save('formal-fingerprints.json',{'schema':'r1-formal-fingerprints.v1','normalization':'Exact raw outputs retained in JSONL. SHA256 of sorted JSON containing returncode, exception, stdout and stderr after path/UUID/address/runtime-filename normalization; see runner.py norm(). Assertion and full traceback fingerprints are separately retained. Version probes are excluded from verification call counts.','rows':formal})
for name,data,fields in [('paired-comparison.csv',rows,['nodeid','baseline_status','r1_status','classification','cause','same_assertion_fingerprint','same_full_traceback_fingerprint','same_attribution_traceback_fingerprint','baseline_attribution_fingerprint','r1_attribution_fingerprint','same_lean_environment_fingerprints']),('failure-inventory.csv',inventory,['nodeid','original_status','family','cause','baseline_status','r1_status','classification'])]:
    with (O/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(data)
diffs=[]
for row in rows:
    if not row['same_full_traceback_fingerprint']:
        b=failed(bt[row['nodeid']]).get('normalized_longrepr','');r=failed(rt[row['nodeid']]).get('normalized_longrepr','')
        diffs.append('\nNODE '+row['nodeid']+'\n'+''.join(difflib.unified_diff(b.splitlines(True),r.splitlines(True),fromfile='baseline',tofile='r1')))
(O/'traceback-differences.diff').write_text('\n'.join(diffs))
save('fingerprint-normalization.json',{'version':'r1-attribution-normalization.v3','base':'runner.py norm()','additional_rules':['artifacts/student_claim_checks/<timestamp>_student_claims directory','manifest_id=rep_<32 hex>','generated_at=datetime.datetime(...)','manifest_sha256=<64 hex>','TME P4 run UUID directory','consistent alpha-renaming of TME P4 verification/check tokens derived from random solution_id; reference graph preserved'],'preserved':['all assertions','mathematical values','scores','statuses','Lean source hashes and source text','Lean stdout/stderr','raw tracebacks and strict fingerprints'],'same_attribution_traceback_count':sum(r['same_attribution_traceback_fingerprint'] for r in rows),'strict_traceback_difference_count':sum(not r['same_full_traceback_fingerprint'] for r in rows)})
result={'baseline_counts':br['counts'],'r1_counts':rr['counts'],'paired_counts':dict(collections.Counter(r['classification'] for r in rows)),'same_traceback':sum(r['same_full_traceback_fingerprint'] for r in rows),'same_assertion':sum(r['same_assertion_fingerprint'] for r in rows),'formal_cases':len(formal),'formal_environment_confirmed':sum(f['both_runs_mathlib_checkout_failure'] for f in formal),'formal_same_source_sequence':sum(f['same_verification_source_sequence'] for f in formal),'formal_baseline_verification_calls':sum(f['baseline_verification_calls'] for f in formal),'formal_r1_verification_calls':sum(f['r1_verification_calls'] for f in formal),'PASS_BASELINE_FAIL_R1':[r['nodeid'] for r in rows if r['classification']=='PASS_BASELINE_FAIL_R1'],'unresolved':[r['nodeid'] for r in rows if r['classification'] in ('FAIL_BOTH_DIFFERENT_FINGERPRINT','NOT_COMPARABLE') or r['cause']=='UNRESOLVED_FORMAL']}
if (O/'r1-contracts-results.json').exists():
    cbr,cbt,_=loadrun('baseline-contracts');crr,crt,_=loadrun('r1-contracts')
    common=sorted(set(cbt)&set(crt)); paired=[compare(cbt[n],crt[n]) for n in common]
    added=sorted(set(crt)-set(cbt)); removed=sorted(set(cbt)-set(crt))
    contracts={'baseline_counts':cbr['counts'],'r1_counts':crr['counts'],'common_node_count':len(common),'paired_counts':dict(collections.Counter(r['classification'] for r in paired)),'paired':paired,'r1_only':[{'nodeid':n,'status':crt[n]['status']} for n in added],'baseline_only':removed,'dynamic_r1_counts':dict(collections.Counter(t['status'] for n,t in crt.items() if n.startswith('tests/test_dynamic_'))),'shared_r1_counts':dict(collections.Counter(t['status'] for n,t in crt.items() if not n.startswith('tests/test_dynamic_')))}
    save('contracts-comparison.json',contracts)
    result['contracts']={k:v for k,v in contracts.items() if k not in ('paired','r1_only')}
    result['contracts']['r1_only_counts']=dict(collections.Counter(crt[n]['status'] for n in added))
    result['PASS_BASELINE_FAIL_R1']=sorted(set(result['PASS_BASELINE_FAIL_R1'])|{r['nodeid'] for r in paired if r['classification']=='PASS_BASELINE_FAIL_R1'})
    result['unresolved']+= [r['nodeid'] for r in paired if r['classification'] in ('FAIL_BOTH_DIFFERENT_FINGERPRINT','NOT_COMPARABLE')]
    result['unresolved']+= [n for n in added if crt[n]['status']!='PASS']+removed
result['NEW_R1_REGRESSIONS']=len(result['PASS_BASELINE_FAIL_R1'])
result['same_attribution_traceback']=sum(r['same_attribution_traceback_fingerprint'] for r in rows)
result['unresolved'] += [f['nodeid'] for f in formal if not f['same_verification_source_sequence']]
result['provisional_verdict']='R1_NEW_REGRESSIONS_FOUND' if result['NEW_R1_REGRESSIONS'] else 'R1_REGRESSION_ATTRIBUTION_INCONCLUSIVE' if result['unresolved'] else 'R1_REGRESSION_ATTRIBUTION_CLEAN'
save('comparison-summary.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='contracts'},indent=2))
