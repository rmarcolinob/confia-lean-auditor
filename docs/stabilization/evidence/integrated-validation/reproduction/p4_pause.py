"""Diagnostic pytest plugin: run the unchanged original test with one real pause.

CONFIA_P4_CONTROL=original selects only the pre-PR7 Budget class in memory.
No assertions, scores, source files or production limits are changed.
"""
import importlib.util
import os
from pathlib import Path
import subprocess
import time
import pytest

@pytest.fixture(autouse=True)
def real_reextraction_pause(monkeypatch):
    from confia_lean_auditor.core.math_canonical import parser
    from confia_lean_auditor.student_claims import tme2_p4_digital as p4
    if os.environ.get('CONFIA_P4_CONTROL') == 'original':
        path = Path(__file__).with_name('original_parser.py')
        path.write_bytes(subprocess.check_output(['git','show','923bf3a:app/confia_lean_auditor/core/math_canonical/parser.py']))
        spec = importlib.util.spec_from_file_location('confia_lean_auditor.core.math_canonical.parser_control',path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        monkeypatch.setattr(parser,'Budget',module.Budget)
    original = p4.extract_p4_quantities
    tick = parser.Budget.tick
    count = [0]
    pause = [False]
    def extract(*args,**kwargs):
        count[0] += 1
        if count[0] == 2:
            pause[0] = True
        return original(*args,**kwargs)
    def delayed(self,depth=0):
        if pause[0]:
            pause[0] = False
            time.sleep(.1)
        return tick(self,depth)
    monkeypatch.setattr(p4,'extract_p4_quantities',extract)
    monkeypatch.setattr(parser.Budget,'tick',delayed)
