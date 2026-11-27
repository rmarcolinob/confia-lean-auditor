#!/usr/bin/env python3
"""Prepare/verify a content manifest without auditing solutions or contacting APIs."""
import argparse
import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE='fc6f271ab4f484f48609ddde67faa84b0ac690ca'
ASSETS=Path('docs/audits/assets/dynamic-rc1')
TAG='SPECIALIZED-TME2-RC1'
TAG_OBJECT='0c64e318a26e21f71fe3097c66ee17a5206dd8a3'
TAG_COMMIT='c03403fe5b83d9db9df172882bd69af3dfa2d027'
MODULES=['dynamic.models','dynamic.preparation_models','dynamic.grading_models','dynamic.review_models',
 'dynamic.reconciliation_models','dynamic.study_models','dynamic.school_contracts','dynamic.adjudication',
 'recognition.schemas','submissions.schemas','capture.schemas','assessments.models']


def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def record(path):
    raw=(ROOT/path).read_bytes();return dict(sha256=digest(raw),size_bytes=len(raw))
def write(path,value):
    (ROOT/path).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def packages():return dict(sorted({d.metadata['Name'].lower().replace('_','-'):d.version for d in metadata.distributions() if d.metadata['Name']}.items()))


def source_paths():
    return sorted(p for p in git('ls-files').splitlines() if p.startswith(('app/','tests/','ConfiaLeanAuditor/'))
        or p in {'pyproject.toml','lean-toolchain','lake-manifest.json','lakefile.lean','scripts/create_demo_users.py','scripts/create_demo_institutional_data.py'})


def policy_snapshot():
    sys.path.insert(0,str(ROOT/'app'))
    from confia_lean_auditor.dynamic import provider,review_provider,semantic_credit,versions,study_feedback
    from confia_lean_auditor.semantic_policy import minimal_review
    prompts={**provider.PROMPTS,'semantic_binary':minimal_review.PROMPT,'semantic_credit':semantic_credit.PROMPT_CREDIT,'legacy_blind_review':review_provider.PROMPT}
    from pydantic import BaseModel
    schemas={}
    for name in MODULES:
        mod=importlib.import_module('confia_lean_auditor.'+name)
        for k,v in vars(mod).items():
            if isinstance(v,type) and issubclass(v,BaseModel) and v.__module__==mod.__name__:
                schemas[name+'.'+k]=v.model_json_schema()
    schemas['semantic_binary.wire']=minimal_review.SCHEMA
    schemas['dynamic_credit.wire']=semantic_credit.SCHEMA
    for name,cls in [('PreparationProposal',importlib.import_module('confia_lean_auditor.dynamic.preparation_models').PreparationProposal),
       ('SuggestedRubric',importlib.import_module('confia_lean_auditor.dynamic.models').SuggestedRubric),
       ('ControlledHelpProposal',importlib.import_module('confia_lean_auditor.dynamic.study_models').ControlledHelpProposal)]:
        schemas[name+'.provider_wire']=provider.generation_schema(cls.model_json_schema())
    versions_data={k:v for k,v in vars(versions).items() if k.endswith('_VERSION')}
    for module,attr in [('dynamic.verification','VERSION'),('dynamic.dependencies','VERSION'),('dynamic.semantic_credit','VERSION'),
       ('dynamic.review_models','VERSION'),('dynamic.reconciliation_models','VERSION'),('dynamic.reconciliation_models','POLICY_VERSION'),
       ('dynamic.provider','PROMPT_VERSION'),('dynamic.review_provider','PROMPT_VERSION'),('dynamic.study_feedback','POLICY'),
       ('semantic_policy.service','DYNAMIC_VERSION'),('capture.schemas','SCHEMA_VERSION')]:
        versions_data[module+'.'+attr]=getattr(importlib.import_module('confia_lean_auditor.'+module),attr)
    return prompts,schemas,versions_data


def collect_environment():
    allowed=['CONFIA_DYNAMIC_POLICY','CONFIA_DYNAMIC_MODEL','CONFIA_DYNAMIC_REASONING_EFFORT','CONFIA_DYNAMIC_LLM_ENABLED',
      'CONFIA_SEMANTIC_MODEL','CONFIA_SEMANTIC_REASONING_EFFORT','CONFIA_SEMANTIC_LLM_ENABLED',
      'CONFIA_DYNAMIC_REVIEWER_MODEL','CONFIA_DYNAMIC_REVIEWER_REASONING_EFFORT','CONFIA_DYNAMIC_REVIEWER_ENABLED','CONFIA_RECOGNITION_TIMEOUT_SECONDS']
    # Exact allowlist: no env dump, credentials, headers, user stores or .env reads.
    env=dict(python_version=platform.python_version(),implementation=platform.python_implementation(),
       observation_scope='This process only; no .env or running server inspection',executable=sys.executable,platform=platform.platform(),machine=platform.machine(),python_packages=packages(),
       observed_configuration={k:os.environ.get(k) for k in allowed},
       lean_executed_by_dynamic=False,lake_packages={})
    for cmd in ('lean','lake','node'):
        try:env[cmd+'_version']=subprocess.check_output([cmd,'--version'],cwd=ROOT,text=True,timeout=20).strip()
        except (OSError,subprocess.SubprocessError):env[cmd+'_version']=None
    lock=json.loads((ROOT/'lake-manifest.json').read_text())
    for p in lock['packages']:
        folder=ROOT/'.lake/packages'/p['name'];row=dict(locked_revision=p['rev'],available=folder.exists())
        if row['available']:
            row.update(actual_revision=subprocess.check_output(['git','-C',str(folder),'rev-parse','HEAD'],text=True).strip(),
                dirty=bool(subprocess.check_output(['git','-C',str(folder),'status','--porcelain'],text=True).strip()))
        env['lake_packages'][p['name']]=row
    return env


def build():
    if git('branch','--show-current')!='codex/dynamic-development' or git('rev-parse','HEAD')!=BASE:
        raise ValueError('Unexpected source branch/commit')
    if git('diff','--name-only',BASE,'--','app','tests','ConfiaLeanAuditor','pyproject.toml','lean-toolchain','lake-manifest.json'):
        raise ValueError('Existing source/test files changed')
    (ROOT/ASSETS).mkdir(parents=True,exist_ok=True)
    prompts,schemas,versions=policy_snapshot()
    write(ASSETS/'prompts.json',prompts);write(ASSETS/'schemas.json',schemas)
    env=collect_environment();write(ASSETS/'environment.json',env)
    (ROOT/ASSETS/'python-constraints.txt').write_text(''.join(f'{name}=={version}\n' for name,version in env['python_packages'].items() if name!='confia-lean-auditor'))
    sources={p:record(Path(p)) for p in source_paths()}
    content={p:v['sha256'] for p,v in sources.items() if p.startswith('app/')}
    fingerprint='dynamic-candidate-content.v1:'+digest(canonical(content))
    extra=[p for p in (ROOT/ASSETS).rglob('*') if p.is_file() and p.name not in {'manifest.json','manifest.sha256'}]
    extra += [ROOT/p for p in ['scripts/evaluation/dynamic_rc1_manifest.py','scripts/evaluation/dynamic_rc1_smoke.py',
       'tests/test_rc1_smoke_budget.py','docs/audits/DYNAMIC_RC1_CANDIDATE.md','docs/audits/DYNAMIC_RC1_SMOKE.md',
       'docs/audits/CONFIA_DYNAMIC_INTERVENCOES_6_6B_CONSOLIDACAO.md','docs/audits/CONFIA_DYNAMIC_INTERVENCAO_6B_FEEDBACK.md',
       'docs/audits/CONFIA_DYNAMIC_INTERVENCAO_6_ESTUDO_AUTONOMO.md','docs/audits/CONFIA_DYNAMIC_INTERVENCAO_6_REVISAO.md']]
    prepared={str(p.relative_to(ROOT)):record(p.relative_to(ROOT)) for p in sorted(set(extra))}
    data=dict(manifest_schema='dynamic-rc1-candidate-manifest.v1',candidate='DYNAMIC-RC1',status='PREPARATION_ONLY_NOT_TAGGED',date='2026-11-26',
       source_commit=BASE,source_branch='codex/dynamic-development',initial_worktree_clean=True,
       pending_preparation=git('status','--porcelain').splitlines(),source_files=sources,preparation_files=prepared,
       fingerprint=fingerprint,fingerprint_definition='SHA256 of canonical JSON mapping sorted app/ tracked paths to SHA256 of exact bytes; manifest-only identity, not legacy auditor_version.',
       legacy_runtime_auditor_version='dynamic-grader.r1',versions=versions,
       prompt_version_labels={k:('self-study-feedback.v2' if k=='study_feedback' else 'dynamic-dy2.v1:'+k+(':credit-v1' if k=='rubric' else '')) for k in ('prepare','rubric','review_rubric','study_prepare','study_rubric','study_feedback')},
       prompt_hashes={k:digest(v.encode()) for k,v in prompts.items()},schema_hashes={k:digest(canonical(v)) for k,v in schemas.items()},
       protected_specialized=dict(tag=TAG,tag_object=TAG_OBJECT,commit=TAG_COMMIT,fingerprint='tme-integration.v1:2da7a5bd4d0cd615fd06993b9e7e45fa86c27b6778476724882d65342526b9da'),
       dynamic_execution=dict(lean=False,pauta_engine=False,exact_scope='dynamic-exact-polynomial.v1 and source-bound local checks',
          semantic_policy='dynamic-semantic.v1',reviewer='semantic.review_phase per criterion, blind_input; shared semantic model',
          legacy_reviewer='OpenAIIndependentReviewProvider configured separately; bypassed by dynamic-semantic.v1',
          reconciliation='semantic.reconcile for dynamic-semantic.v1; no extra LLM call; exact decisions preserved',
          institutional_rubric='versioned approved package',self_study_rubric='PROVISIONAL_FORMATIVE, internal max 3; no official grade',
          public_feedback='self-study-feedback.v2',human_decisions='separate immutable decision and adjudication records'),
       configuration_defaults=dict(preparation_model='gpt-4.1',preparation_reasoning=None,preparation_output=10000,preparation_timeout_seconds=90,
          semantic_model='gpt-6.1-sol',semantic_reasoning='medium',semantic_output=4000,semantic_timeout_seconds=60,
          openai_retries=0,ocr_provider='mathpix_image',ocr_adapter='confia_mathpix_image:1.0.0',ocr_model=None,ocr_deadline_seconds=30,
          providers_enabled_by_default=False,credentials_in_manifest=False),
       tests=json.loads((ROOT/ASSETS/'test-results.json').read_text()),
       paid_smoke=dict(executed=False,plan='docs/audits/DYNAMIC_RC1_SMOKE.md',cap_usd='6.00',max_calls=22,gold_sent=False))
    write(ASSETS/'manifest.json',data)
    (ROOT/ASSETS/'manifest.sha256').write_text(digest((ROOT/ASSETS/'manifest.json').read_bytes())+'  manifest.json\n')
    print(json.dumps(dict(candidate=data['candidate'],fingerprint=fingerprint,source_files=len(sources),preparation_files=len(prepared),paid_calls=0)))


def verify(environment=False):
    path=ROOT/ASSETS/'manifest.json'
    if digest(path.read_bytes())!=(ROOT/ASSETS/'manifest.sha256').read_text().split()[0]:raise ValueError('Manifest checksum mismatch')
    data=json.loads(path.read_text())
    subprocess.run(['git','merge-base','--is-ancestor',data['source_commit'],'HEAD'],cwd=ROOT,check=True)
    if git('ls-files','--others','--exclude-standard','--','app'):raise ValueError('Uninventoried application source')
    known=set(data['source_files'])|set(data['preparation_files'])
    if set(source_paths())-known:raise ValueError('New tracked source omitted from manifest')
    if git('rev-parse','refs/tags/'+TAG)!=TAG_OBJECT or git('rev-parse','refs/tags/'+TAG+'^{}')!=TAG_COMMIT:raise ValueError('Protected SPECIALIZED reference changed')
    for name,expected in {**data['source_files'],**data['preparation_files']}.items():
        p=(ROOT/name).resolve()
        if not p.is_relative_to(ROOT) or record(Path(name))!=expected:raise ValueError('File mismatch: '+name)
    content={p:r['sha256'] for p,r in data['source_files'].items() if p.startswith('app/')}
    if 'dynamic-candidate-content.v1:'+digest(canonical(content))!=data['fingerprint']:raise ValueError('Fingerprint mismatch')
    if environment:
        expected=json.loads((ROOT/ASSETS/'environment.json').read_text());actual=collect_environment()
        for k in ('python_version','python_packages','lean_version','lake_version','node_version','lake_packages','observed_configuration'):
            if actual[k]!=expected[k]:raise ValueError('Environment mismatch: '+k)
    print(json.dumps(dict(candidate=data['candidate'],verified_files=len(data['source_files'])+len(data['preparation_files']),fingerprint=data['fingerprint'],environment_checked=environment,audits_executed=0,api_calls=0)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');p.add_argument('--environment',action='store_true');a=p.parse_args()
    try:build() if a.write else verify(a.environment)
    except (ValueError,OSError,subprocess.SubprocessError) as e:raise SystemExit('Candidate verification failed: '+str(e))
