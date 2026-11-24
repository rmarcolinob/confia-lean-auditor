#!/usr/bin/env python3
"""Start the integrated local pilot without modifying other worktree stores."""
import argparse
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))


def configure(data, legacy=False):
    if os.getenv('CONFIA_ENV','development')=='production':
        raise SystemExit('This local demo launcher is not a production server.')
    data=data.resolve()
    data.mkdir(parents=True,exist_ok=True)
    os.environ.update(CONFIA_ENV='development',CONFIA_AUTH_ENABLED='0',
        CONFIA_TME_DEMO_NO_AUTH='1',CONFIA_DYNAMIC_DEMO_ENABLED='1',CONFIA_LEAN_AUDITOR_ROOT=str(ROOT))
    for name in ('AUTH','INSTITUTIONAL','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TME_EXAMS','TME_CASES',
                 'SUBMISSIONS','SUBMISSION_AUDITS','DYNAMIC','TEACHER_DECISIONS'):
        os.environ['CONFIA_'+name+'_DIR']=str(data/name.lower())
    os.environ['CONFIA_SPECIALIZED_POLICY']='legacy' if legacy else 'semantic-b-minimal.v1'
    os.environ['CONFIA_DYNAMIC_POLICY']='legacy' if legacy else 'dynamic-semantic.v1'
    # Inference stays opt-in; this launcher never enables paid providers.
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=ROOT/'runtime/pilot-dec10')
    parser.add_argument('--port',type=int,default=8010)
    parser.add_argument('--legacy',action='store_true',help='Use previous policies for new corrections; retain saved history.')
    args=parser.parse_args()
    data=configure(args.data_dir,args.legacy)
    print('Data:',data,'\nSPECIALIZED / DYNAMIC: http://127.0.0.1:'+str(args.port)+'/tme',flush=True)
    print('ITA workspace: http://127.0.0.1:'+str(args.port)+'/\nPaid providers are not enabled by this launcher.',flush=True)
    import uvicorn
    uvicorn.run('confia_lean_auditor.main:app',host='127.0.0.1',port=args.port)

if __name__=='__main__':main()
