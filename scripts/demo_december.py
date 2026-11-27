#!/usr/bin/env python3
"""Local rehearsal setup/startup. No grading code or score fixtures are injected."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
ASSESSMENT='asmt_dec20260000000000000000000000001'
TITLE='Dezembro - ensaio controlado Q1-Q3'


def configure(data,lean):
    if os.environ.get('CONFIA_ENV','development').strip().lower()=='production':
        raise SystemExit('Demo recusada: CONFIA_ENV=production.')
    if data.is_symlink():raise SystemExit('Use um diretório de dados local, sem symlink.')
    data.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.environ.update(CONFIA_ENV='development',CONFIA_AUTH_ENABLED='1',CONFIA_TME_DEMO_NO_AUTH='1',
        CONFIA_TME_CERTIFICATION_ENABLED='1',CONFIA_TME_QUESTION_USE_LEAN='1' if lean else '0',CONFIA_LEAN_AUDITOR_ROOT=str(ROOT))
    for name in ('AUTH','INSTITUTIONAL','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TME_EXAMS','TME_CASES','SUBMISSIONS','SUBMISSION_AUDITS'):
        os.environ['CONFIA_'+name+'_DIR']=str(data/name.lower())
    sys.path.insert(0,str(ROOT/'app'))


def preflight(lean):
    import fastapi,uvicorn,pydantic,pypdfium2,PIL
    for path in ('app/confia_lean_auditor/static/tme/index.html','app/confia_lean_auditor/static/tme/full-exam.js','examples/demo_december/prova-demo.pdf'):
        if not (ROOT/path).is_file():raise SystemExit('Arquivo ausente: '+path)
    print('Python:',sys.executable,sys.version.split()[0],flush=True)
    if not lean:
        print('PLANO B explícito: Lean desativado; não apresentar certificação formal.',flush=True);return
    # Validate every pinned repository before invoking Lake, so startup cannot clone.
    manifest=json.loads((ROOT/'lake-manifest.json').read_text())
    for package in manifest['packages']:
        path=ROOT/'.lake/packages'/package['name']
        if not (path/'.git').exists():raise SystemExit('Cache Lean ausente: '+str(path)+'; prepare antes da reunião.')
        revision=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        if revision!=package['rev']:raise SystemExit('Revisão Lean incompatível: '+package['name'])
    if not (ROOT/'.lake/packages/mathlib/.lake/build/lib/lean/Mathlib.olean').is_file():
        raise SystemExit('Mathlib não compilado; prepare o cache antes da reunião.')
    if not (ROOT/'.lake/build/lib/lean/ConfiaLeanAuditor.olean').is_file():
        raise SystemExit('Módulos Lean locais ausentes; execute lake build ConfiaLeanAuditor antes da reunião.')
    subprocess.run(['lake','env','lean','--version'],cwd=ROOT,check=True,timeout=30)
    with tempfile.TemporaryDirectory(prefix='confia-demo-preflight-') as temp:
        path=Path(temp)/'Smoke.lean'
        path.write_text('import Mathlib\nimport ConfiaLeanAuditor\nexample : (2 : Nat) + 2 = 4 := by norm_num\n')
        subprocess.run(['lake','env','lean',str(path)],cwd=ROOT,check=True,timeout=60)
    print('Mathlib fixado + prova formal local: OK',flush=True)


def seed():
    from confia_lean_auditor.tme.exam_router import create_assessment
    from confia_lean_auditor.tme.exam_models import TMEAssessmentCreate
    from confia_lean_auditor.tme.auth import TMEEvaluator,DEMO_EVALUATOR_ID
    from confia_lean_auditor.assessments.store import assessment_store
    body=TMEAssessmentCreate(title=TITLE,instructions='Dados sintéticos de ensaio. Não é correção oficial TME.',academic_year=2026,
        items=[dict(problem_id=f'TME2026P{i}',points=20) for i in (1,2,3)])
    try:doc=assessment_store().get(ASSESSMENT)
    except FileNotFoundError:doc=create_assessment(body,TMEEvaluator(DEMO_EVALUATOR_ID),ASSESSMENT)
    if (doc.assessment.title!=TITLE or doc.assessment.teacher_user_id!=DEMO_EVALUATOR_ID or
            [(i.problem_id,float(i.points)) for i in doc.items]!=[(f'TME2026P{i}',20) for i in (1,2,3)]):
        raise SystemExit('Assessment de ensaio divergiu; nenhum dado foi sobrescrito.')
    print('Assessment:',ASSESSMENT,TITLE,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['check','start'])
    parser.add_argument('--data-dir',type=Path,default=ROOT/'runtime/demo_december')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--without-lean',action='store_true')
    args=parser.parse_args()
    if not 1024<=args.port<=65535:parser.error('porta deve estar entre 1024 e 65535')
    configure(args.data_dir.absolute(),not args.without_lean)
    preflight(not args.without_lean)
    if args.command=='check':return
    with socket.socket() as probe:
        # Permit immediate restart after a clean shutdown (TIME_WAIT), while
        # still refusing a port with a live listening process.
        probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        try:probe.bind(('127.0.0.1',args.port))
        except OSError:raise SystemExit(f'Porta {args.port} indisponível; encerre a instância anterior ou use --port.')
    seed()
    print('Storage:',args.data_dir.absolute(),'\nURL: http://127.0.0.1:'+str(args.port)+'/tme',flush=True)
    import uvicorn
    uvicorn.run('confia_lean_auditor.main:app',host='127.0.0.1',port=args.port)

if __name__=='__main__':
    try:main()
    except (OSError,subprocess.SubprocessError) as exc:
        raise SystemExit('Preflight/startup falhou: '+str(exc)+'; prepare o ambiente antes da reunião.') from None
