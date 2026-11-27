"""Local audit server after probe_school.py; synthetic auth fixture only, providers OFF.
Never point this launcher at operational stores. Stop with Ctrl+C after testing.
"""
import os,json
from pathlib import Path
root=Path(__file__).resolve().parents[4]
for k in list(os.environ):
 if any(x in k for x in ('API_KEY','APP_KEY','AUTH_TOKEN','ACCESS_TOKEN')):os.environ.pop(k,None)
os.environ.update(json.loads((root/'runtime/audit-pre10dez/school-v2/server_config.json').read_text()))
import uvicorn
uvicorn.run('confia_lean_auditor.main:app',host='127.0.0.1',port=8876,access_log=False)
