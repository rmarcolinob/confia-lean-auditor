import hashlib,json,pathlib,subprocess,sys
R=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
B=pathlib.Path('/private/tmp/confia-r1-attribution-baseline-5aa7344')
O=R/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
probe='''import sys,json,pathlib
root=pathlib.Path(sys.argv[1]);sys.path[:0]=[str(root/'app'),str(root)]
from benchmarks.handwriting_recognition.schema import RecognitionSample
from confia_lean_auditor.submissions.schemas import MAX_SOURCE_PAGES
stored=json.loads((root/'benchmarks/handwriting_recognition/sample.schema.json').read_text())
actual=RecognitionSample.model_json_schema()
def walk(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  for k in sorted(a.keys()|b.keys()):
   if k not in a or k not in b: yield {'path':path+'/'+k,'stored':a.get(k),'runtime':b.get(k)}
   else: yield from walk(a[k],b[k],path+'/'+k)
 elif a!=b: yield {'path':path,'stored':a,'runtime':b}
print(json.dumps({'max_source_pages':MAX_SOURCE_PAGES,'schema_differences':list(walk(stored,actual))}))
'''
paths=['benchmarks/handwriting_recognition/schema.py','benchmarks/handwriting_recognition/sample.schema.json','app/confia_lean_auditor/recognition/schemas.py','app/confia_lean_auditor/submissions/schemas.py','app/confia_lean_auditor/static/app.js','app/confia_lean_auditor/static/submissions/teacher.js','app/confia_lean_auditor/static/capture/tablet.js','app/confia_lean_auditor/static/capture/tablet.css']
data={}
for label,root in [('baseline',B),('r1',R)]:
    row=json.loads(subprocess.check_output([str(R/'.venv/bin/python'),'-c',probe,str(root)],cwd=root,text=True))
    static=root/'app/confia_lean_auditor/static'
    text='\n'.join((static/p).read_text() for p in ('app.js','submissions/teacher.js','capture/tablet.js'))
    row['missing_ui_phrase']='Verificação formal com Lean'
    row['required_phrase_present']=row['missing_ui_phrase'] in text
    css=(static/'capture/tablet.css').read_text()
    row['sticky_occurrences_after_embedded_marker']=css.split('/* Embedded mode')[1].count('position: sticky')
    row['sticky_lines']=[i for i,line in enumerate(css.splitlines(),1) if 'position: sticky' in line]
    row['source_sha256']={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
    data[label]=row
data['identical_baseline_and_r1']=data['baseline']==data['r1']
(O/'nonformal-evidence.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'identical':data['identical_baseline_and_r1'],'schema_difference':data['r1']['schema_differences'],'required_phrase_present':data['r1']['required_phrase_present'],'sticky_occurrences_after_embedded_marker':data['r1']['sticky_occurrences_after_embedded_marker']}))
