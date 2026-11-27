import hashlib, json, pathlib, re, subprocess, tarfile, datetime
ROOT=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
OUT=ROOT/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
BASE=pathlib.Path('/private/tmp/confia-r1-attribution-baseline-5aa7344')
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b): return hashlib.sha256(b).hexdigest()
assert git('rev-parse','HEAD').decode().strip()=='5aa7344e5904305a414688741f83aafc7d610200'
assert not OUT.exists()
paths=sorted(set(p.decode() for p in git('ls-files','-z','--cached','--others','--exclude-standard').split(b'\0') if p))
hashes={p:sha((ROOT/p).read_bytes()) for p in paths if (ROOT/p).is_file()}
dirty=sorted(set(p.decode() for p in (git('diff','--name-only','-z')+git('ls-files','-z','--others','--exclude-standard')).split(b'\0') if p))
status=git('status','--short').decode()
log=ROOT/'docs/audits/assets/confia-dynamic-r1-dev-v2/regression-python.log'
nodes=re.findall(r'^FAILED (\S+)',log.read_text(),re.M)
assert len(nodes)==len(set(nodes))==105
OUT.mkdir(parents=True)
(OUT/'source-preservation.json').write_text(json.dumps({'schema':'r1-source-preservation.v1','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':git('rev-parse','HEAD').decode().strip(),'branch':git('branch','--show-current').decode().strip(),'status_before':status,'files':hashes,'dirty_files':dirty,'original_failure_log_sha256':sha(log.read_bytes())},indent=2)+'\n')
(OUT/'r1-before.patch').write_bytes(git('diff','--binary','HEAD'))
with tarfile.open(OUT/'r1-before.tar.gz','w:gz') as t:
    for p in dirty:
        if (ROOT/p).is_file(): t.add(ROOT/p,arcname=p,recursive=False)
(OUT/'failure-nodeids.json').write_text(json.dumps(nodes,indent=2)+'\n')
(OUT/'status-before.txt').write_text(status)
subprocess.run(['git','worktree','add','--detach',str(BASE),'5aa7344e5904305a414688741f83aafc7d610200'],cwd=ROOT,check=True)
(BASE/'.lake').symlink_to(ROOT/'.lake',target_is_directory=True)
same={p:sha((BASE/p).read_bytes())==hashes[p] for p in sorted({n.split('::')[0] for n in nodes}|{'tests/conftest.py','lakefile.toml','lake-manifest.json','lean-toolchain'})}
assert all(same.values())
(OUT/'baseline-setup.json').write_text(json.dumps({'baseline_path':str(BASE),'baseline_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),'shared_lake':str((BASE/'.lake').resolve()),'same_input_hashes':same,'test_file_sha256':{p:hashes[p] for p in same},'baseline_status':subprocess.check_output(['git','status','--short'],cwd=BASE,text=True)},indent=2)+'\n')
print(json.dumps({'baseline':str(BASE),'preserved_files':len(hashes),'backed_up_dirty_files':len(dirty),'failed_nodes':len(nodes),'identical_test_and_lean_inputs':all(same.values())}))
