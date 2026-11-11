"""Operational launcher safeguards; no scoring expectations changed."""
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def launcher():
    spec=importlib.util.spec_from_file_location('december_launcher',ROOT/'scripts/demo_december.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_production_refuses_before_creating_storage(launcher,tmp_path,monkeypatch):
    monkeypatch.setenv('CONFIA_ENV','PRODUCTION')
    with pytest.raises(SystemExit,match='production'):launcher.configure(tmp_path/'store',True)
    assert not (tmp_path/'store').exists()


def test_preflight_missing_cache_never_invokes_lake(launcher,tmp_path,monkeypatch):
    import shutil
    monkeypatch.setattr(launcher,'ROOT',tmp_path)
    for name in ['app/confia_lean_auditor/static/tme/index.html','app/confia_lean_auditor/static/tme/full-exam.js','examples/demo_december/prova-demo.pdf','lake-manifest.json']:
        target=tmp_path/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    calls=[];monkeypatch.setattr(launcher.subprocess,'run',lambda *a,**k:calls.append(a))
    with pytest.raises(SystemExit,match='Cache Lean ausente'):launcher.preflight(True)
    assert calls==[]


def test_seed_idempotent_preserves_definition(launcher,tmp_path,monkeypatch):
    monkeypatch.setenv('CONFIA_ENV','development')
    for name in ['AUTH','INSTITUTIONAL','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TME_EXAMS','TME_CASES','SUBMISSIONS','SUBMISSION_AUDITS']:
        monkeypatch.setenv('CONFIA_'+name+'_DIR',str(tmp_path/name.lower()))
    launcher.seed()
    files={p:p.read_bytes() for p in tmp_path.rglob('*.json')}
    launcher.seed()
    assert files=={p:p.read_bytes() for p in tmp_path.rglob('*.json')}


def test_inputs_have_four_pages_and_explicit_reading_correction():
    import pypdfium2
    folder=ROOT/'examples/demo_december'
    pdf=pypdfium2.PdfDocument(folder/'prova-demo.pdf');assert len(pdf)==4
    old=(folder/'q1-inicial.txt').read_text();new=(folder/'q1-corrigida.txt').read_text()
    assert old.replace('731-137=584','731-137=594')==new
    assert '2/6=1/2' in (folder/'q3-erro.txt').read_text()


from test_tme_full_exam import demo

def test_certification_flag_does_not_bypass_authentication(demo,monkeypatch):
    client,_=demo
    monkeypatch.setenv('CONFIA_TME_CERTIFICATION_ENABLED','1')
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','0')
    base='/tme/assessments/asmt_dec20260000000000000000000000001/certification'
    for suffix in ['', '/gold', '/export.csv', '/export.json']:
        assert client.get(base+suffix).status_code==401
    assert client.post(base+'/gold',json={}).status_code==401
