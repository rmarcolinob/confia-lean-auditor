import datetime,hashlib,json,pathlib,subprocess,tarfile
R=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
B=pathlib.Path('/private/tmp/confia-r1-attribution-baseline-5aa7344')
O=R/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True)
initial=load(O/'source-preservation.json')
modified=[p for p,h in initial['files'].items() if not (R/p).is_file() or sha(R/p)!=h]
historical=load(R/'docs/audits/assets/confia-dynamic-r1-dev-v2/protected-inputs.json')
historical_modified=[p for p,h in historical.items() if not (R/p).is_file() or sha(R/p)!=h]
with tarfile.open(O/'r1-before.tar.gz') as t:
    backup_bad=[m.name for m in t.getmembers() if hashlib.sha256(t.extractfile(m).read()).hexdigest()!=initial['files'][m.name]]
envs={n+'-'+stage:load(O/(n+'-environment-'+stage+'.json')) for n in ('baseline','r1','baseline-contracts','r1-contracts','baseline-semantic-repeat') for stage in ('before','after')}
first=envs['baseline-before']
keys=['python_executable','python_version','path','pythonhashseed','packages','mathlib_head','mathlib_status_sha256','mathlib_diff_sha256','lake_realpath','lean_inputs']
env_comparison={key:all(e[key]==first[key] for e in envs.values()) for key in keys}
package_metadata={'raw_lists_identical':env_comparison['packages'],'unique_name_version_sets_identical':all(set(map(tuple,e['packages']))==set(map(tuple,first['packages'])) for e in envs.values()),'third_party_lists_identical':all([p for p in e['packages'] if p[0]!='confia-lean-auditor']==[p for p in first['packages'] if p[0]!='confia-lean-auditor'] for e in envs.values()),'local_application_metadata_occurrences':{label:sum(p[0]=='confia-lean-auditor' for p in e['packages']) for label,e in envs.items()},'explanation':'importlib.metadata enumerates the same local application egg-info once per matching sys.path entry. Raw lists are retained. Dependency name/version sets and all non-application distribution entries are identical; imported application source is verified separately by path and SHA256.'}
env_comparison['packages']=package_metadata['unique_name_version_sets_identical'] and package_metadata['third_party_lists_identical']
head=git(R,'rev-parse','HEAD').strip()
tracked_patch=subprocess.check_output(['git','diff','--binary','HEAD'],cwd=R)
preserved_patch=hashlib.sha256(tracked_patch).hexdigest()==sha(O/'r1-before.patch')
baseline_status=git(B,'status','--short')
baseline_diff=git(B,'diff','--binary','HEAD')
baseline_head=git(B,'rev-parse','HEAD').strip()
status=git(R,'status','--short')
(O/'status-final.txt').write_text(status)
result={'schema':'r1-attribution-integrity.v1','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head_before':initial['head'],'head_after':head,'same_branch':git(R,'branch','--show-current').strip()==initial['branch'],'original_files_checked':len(initial['files']),'original_files_changed':modified,'historical_protected_files_checked':len(historical),'historical_protected_files_changed':historical_modified,'dirty_backup_files_checked':len(initial['dirty_files']),'backup_hash_mismatches':backup_bad,'original_patch_preserved':preserved_patch,'staged_diff':git(R,'diff','--cached','--name-only'),'baseline_status_after':baseline_status,'environment_comparison':env_comparison,'baseline_grader_sha256':envs['baseline-before']['grader_sha256'],'r1_grader_sha256':envs['r1-before']['grader_sha256'],'same_baseline_grader_between_runs':envs['baseline-before']['grader_sha256']==envs['baseline-contracts-before']['grader_sha256'],'same_r1_grader_between_runs':envs['r1-before']['grader_sha256']==envs['r1-contracts-before']['grader_sha256'],'source_preservation_manifest_sha256':sha(O/'source-preservation.json'),'backup_sha256':sha(O/'r1-before.tar.gz'),'status_final':status}
result['baseline_repeat_grader_matches']=envs['baseline-semantic-repeat-before']['grader_sha256']==envs['baseline-before']['grader_sha256']
result['package_metadata_comparison']=package_metadata
result['baseline_tracked_diff_empty']=not baseline_diff
result['baseline_head_after']=baseline_head
result['baseline_only_extra_is_expected_lake_symlink']=baseline_status=='?? .lake\n' and (B/'.lake').is_symlink() and (B/'.lake').resolve()==R/'.lake'
result['all_checks_passed']=not(modified or historical_modified or backup_bad or baseline_diff or result['staged_diff']) and result['baseline_only_extra_is_expected_lake_symlink'] and baseline_head==head==initial['head'] and result['same_branch'] and preserved_patch and all(env_comparison.values()) and result['same_baseline_grader_between_runs'] and result['same_r1_grader_between_runs'] and result['baseline_repeat_grader_matches']
(O/'integrity.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('status_final','environment_comparison')},indent=2))
