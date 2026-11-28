"""Local synthetic teacher demo. Real auth; no credentials/providers inherited."""
import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
safe = {key: value for key, value in os.environ.items()
        if key in ('PATH', 'HOME', 'TMPDIR', 'LANG', 'LC_ALL', 'TZ')}
os.environ.clear()
os.environ.update(safe)
DATA = ROOT / 'artifacts' / 'teacher-direct-demo'
os.environ.update(CONFIA_LEAN_AUDITOR_ROOT=str(ROOT), CONFIA_AUTH_ENABLED='1',
    CONFIA_ENV='test', CONFIA_COOKIE_SECURE='0', CONFIA_TME_DEMO_NO_AUTH='0',
    CONFIA_DYNAMIC_DEMO_ENABLED='0', CONFIA_ENABLE_LLM_FORMAL_STEPS='0',
    CONFIA_DYNAMIC_LLM_ENABLED='0', CONFIA_SEMANTIC_LLM_ENABLED='0',
    CONFIA_DYNAMIC_POLICY='dynamic-semantic.v1', CONFIA_SPECIALIZED_POLICY='semantic-b-minimal.v1')
for name in ('AUTH', 'INSTITUTIONAL', 'SUBMISSIONS', 'SUBMISSION_AUDITS', 'DYNAMIC',
             'TME_CASES', 'TME_EXAMS', 'ASSESSMENTS', 'ASSESSMENT_PARTICIPANTS',
             'TEACHER_DECISIONS', 'SELF_STUDY'):
    os.environ['CONFIA_' + name + '_DIR'] = str(DATA / name.lower())
sys.path.insert(0, str(ROOT / 'app'))
os.chdir(ROOT)
from confia_lean_auditor.auth.store import AuthStore
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.main import app

DATA.mkdir(parents=True, exist_ok=True)
credentials = DATA / 'local-login.json'
store = AuthStore(DATA / 'auth')
if not credentials.exists():
    password = secrets.token_urlsafe(18)
    store.create_user(login='professor.direto', display_name='Professor · demonstração sintética',
        role=Role.TEACHER, password=password, tenant_id='demo-direta', classroom_ids=[])
    fd = os.open(credentials, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump({'login': 'professor.direto', 'password': password}, handle)
account = json.loads(credentials.read_text())
if '--check' in sys.argv:
    from fastapi.testclient import TestClient
    client = TestClient(app, headers={'Origin': 'http://testserver'})
    assert client.post('/auth/login', json=account).status_code == 200
    assert client.get('/auth/me').json()['role'] == 'TEACHER'
    caps = client.get('/dynamic/capabilities').json()
    assert not any(caps[k] for k in ('rubric_suggestion_configured',
        'handwriting_recognition_configured', 'semantic_evaluation_configured'))
    assert client.get('/tme').status_code == 200
    assert client.get('/static/teacher-direct.js').status_code == 200
    print('Preflight HTTP aprovado; login real, providers desligados. Não é teste visual.')
else:
    import uvicorn
    print('Demonstração local sintética: http://127.0.0.1:8888/ · providers desligados', flush=True)
    print('Login:', account['login'], '\nSenha local:', account['password'], flush=True)
    uvicorn.run(app, host='127.0.0.1', port=8888)
