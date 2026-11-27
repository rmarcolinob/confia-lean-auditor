import hashlib,json,pathlib,re
R=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
O=R/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
s=(R/'docs/audits/assets/confia-dynamic-r1-dev-v2/regression-python.log').read_text()
nodes=json.loads((O/'failure-nodeids.json').read_text())
h=list(re.finditer(r'^_+ (test.*?) _+[ \t]*$',s,re.M))
assert len(h)==105
rows=[]
for i,(n,header) in enumerate(zip(nodes,h)):
    assert header.group(1)==n.split('::')[-1]
    stop=h[i+1].start() if i+1<len(h) else s.index(' short test summary info ',header.end())
    trace=s[header.end():stop].strip()
    rows.append({'nodeid':n,'original_status':'FAIL','original_traceback':trace,'original_traceback_sha256':hashlib.sha256(trace.encode()).hexdigest(),'assertion_excerpt':'\n'.join(l for l in trace.splitlines() if l.startswith('E ')),'source_file':n.split('::')[0],'preliminary_family':'CAPTURE_SCHEMA' if 'handwriting_recognition_benchmark' in n else 'UI_CONTRACT' if 'test_ui_' in n else 'FORMAL_LEAN'})
(O/'original-inventory.json').write_text(json.dumps({'schema':'r1-original-failures.v1','original_counts':{'passed':3009,'skipped':47,'failed':105},'failures':rows},indent=2,ensure_ascii=False)+'\n')
shared=['assessments','submissions','transcriptions','submission_audits','teacher_decisions','tme_model_compat','tme_full_exam','tme_question_audit','tme_reanalysis','tme_human_confirmation','tme_finalization','tme_hybrid_grader','tme_accepted_integration','tme_certification','tme_review_workspace','tme_audit_view']
shared=['tests/test_'+n+'.py' for n in shared]
dynamic=['tests/test_dynamic_dy'+str(n)+'.py' for n in range(1,8)]
for label,files in [('baseline-contract-selection.json',dynamic+shared),('r1-contract-selection.json',dynamic+['tests/test_dynamic_r1.py']+shared)]:
    assert all((R/p).is_file() for p in files)
    (O/label).write_text(json.dumps(files,indent=2)+'\n')
print('Inventoried',len(rows),'failures; selected',len(dynamic),'existing Dynamic and',len(shared),'shared contract modules plus R1.')
