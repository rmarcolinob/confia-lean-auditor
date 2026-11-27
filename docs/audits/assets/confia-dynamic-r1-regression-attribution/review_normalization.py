"""Audit the four strict fingerprint differences without discarding raw data."""
import ast,hashlib,json,pathlib,re
R=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
B=pathlib.Path('/private/tmp/confia-r1-attribution-baseline-5aa7344')
O=R/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
def load(n):return json.loads((O/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=(O/'compare.py').read_text();namespace=dict(re=re,digest=lambda b:hashlib.sha256(b).hexdigest())
tree=ast.parse(source)
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in ('failed','attribution_trace'):
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(O/'compare.py'),'exec'),namespace)
normal=namespace['attribution_trace'];failure=namespace['failed']
runs={label:{t['nodeid']:t for t in load(label+'-results.json')['tests']} for label in ('baseline','r1','baseline-semantic-repeat')}
paths={'random_solution_id':'app/confia_lean_auditor/tme/registry.py','verification_token_hash':'app/confia_lean_auditor/claims/common/fact_results.py','random_lean_directory':'app/confia_lean_auditor/lean/student_claim_checkers/tme2_p4.py'}
sources={purpose:{'path':path,'baseline_sha256':sha(B/path),'r1_sha256':sha(R/path),'identical':sha(B/path)==sha(R/path)} for purpose,path in paths.items()}
rows=[]
for pair in load('paired-comparison.json')['rows']:
    if pair['same_full_traceback_fingerprint']:continue
    n=pair['nodeid'];b=runs['baseline'][n];r=runs['r1'][n]
    raw={label:failure(runs[label][n])['normalized_longrepr'] for label in ('baseline','r1')}
    tokens={label:list(dict.fromkeys(re.findall(r'(?:tme2-p4-check\.v1:|check:)([0-9a-f]{20})',s))) for label,s in raw.items()}
    row={'nodeid':n,'strict_traceback_equal':False,'normalized_traceback_equal':normal(b)==normal(r),'verification_tokens_in_first_occurrence_order':tokens,'reason':'runtime timestamps and reproducibility manifest identities' if not tokens['baseline'] else 'random TME solution_id is hashed by FactResultsBuilder; random UUID also names the Lean directory; consistent token renaming retains all reference relationships','raw_evidence':['baseline-results.json','r1-results.json','traceback-differences.diff']}
    if n in runs['baseline-semantic-repeat']:
        repeat=runs['baseline-semantic-repeat'][n]
        row['same_baseline_repeat']={'status':repeat['status'],'strict_traceback_changed_again':failure(b)['traceback_fingerprint']!=failure(repeat)['traceback_fingerprint'],'normalized_traceback_equal':normal(b)==normal(repeat),'evidence':'baseline-semantic-repeat-results.json'}
    rows.append(row)
data={'schema':'r1-normalization-review.v1','sources':sources,'cases':rows,'raw_artifacts_unchanged':True,'scope':'Only analysis fingerprints are normalized. Source hashes, mathematical expressions, assertions, scores, statuses and reference relationships are retained.'}
assert len(rows)==4 and all(r['normalized_traceback_equal'] for r in rows)
assert all(s['identical'] for s in sources.values())
repeats=[r['same_baseline_repeat'] for r in rows if 'same_baseline_repeat' in r]
assert len(repeats)==2 and all(r['strict_traceback_changed_again'] and r['normalized_traceback_equal'] and r['status']=='FAIL' for r in repeats)
(O/'normalization-review.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print('4 strict differences reviewed; 2 reproduced as nondeterminism within the same baseline; normalized traces equal.')
