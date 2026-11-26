import json,os,pathlib,subprocess,time
R=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
O=R/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
nodes=[n for n in json.loads((O/'failure-nodeids.json').read_text()) if n.startswith('tests/test_semantic_claims.py::test_semantic_math_is_checked_by_real_lean')]
assert len(nodes)==2
(O/'semantic-repeat-selection.json').write_text(json.dumps(nodes,indent=2)+'\n')
deadline=time.monotonic()+1800
while not (O/'r1-contracts-environment-after.json').exists():
    if time.monotonic()>deadline:raise SystemExit('Contracts did not finish')
    time.sleep(5)
label='baseline-semantic-repeat'
with (O/(label+'.log')).open('x') as log:
    p=subprocess.run([str(R/'.venv/bin/python'),str(O/'runner.py'),label,'semantic-repeat-selection.json'],cwd=R,env=dict(os.environ,PYTHONHASHSEED='0'),stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==1
data=json.loads((O/(label+'-results.json')).read_text())
assert data['counts']=={'PASS':0,'FAIL':2,'SKIP':0,'ERROR':0,'INCOMPLETE':0}
print('Same-baseline nondeterminism probe finished: 2 failed, no product change.',flush=True)
