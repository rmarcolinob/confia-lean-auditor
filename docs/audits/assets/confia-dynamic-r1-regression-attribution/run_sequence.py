import json,os,pathlib,subprocess,time
R=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
O=R/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
deadline=time.monotonic()+3600
while not (O/'baseline-environment-after.json').exists():
    if time.monotonic()>deadline: raise SystemExit('Baseline did not finish; no later tests started')
    time.sleep(5)
baseline=json.loads((O/'baseline-results.json').read_text())
assert len(baseline['collected'])==105 and not baseline['collection_errors']
env=dict(os.environ,PYTHONHASHSEED='0')
for label,selection in [('r1',None),('baseline-contracts','baseline-contract-selection.json'),('r1-contracts','r1-contract-selection.json')]:
    args=[str(R/'.venv/bin/python'),str(O/'runner.py'),label]
    if selection: args.append(selection)
    print('START '+label,flush=True)
    with (O/(label+'.log')).open('x') as log:
        result=subprocess.run(args,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert result.returncode in (0,1), 'Infrastructure error: '+label
    data=json.loads((O/(label+'-results.json')).read_text())
    assert not data['collection_errors'], 'Collection errors: '+label
    print('DONE '+label+' '+json.dumps(data['counts']),flush=True)
