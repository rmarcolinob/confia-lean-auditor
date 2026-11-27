"""Read-only verification of this audit bundle; does not rerun an audit/provider."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
summary=json.loads((HERE/'summary.json').read_text())
for relative,expected in summary['evidence_sha256'].items():
    path=ROOT/relative
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise SystemExit('Audit evidence mismatch: '+relative)
for relative,expected in json.loads((HERE/'source-hashes.json').read_text()).items():
    path=ROOT/relative
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise SystemExit('Audited source differs from baseline: '+relative)
assert summary['paid_calls']==0
assert summary['baseline']=='923bf3acbd9994af9662bcdff6b18eac1b6d4df9'
routing=json.loads((HERE/'ita-routing.json').read_text())
assert routing['source_record_unchanged'] and routing['score'] is None
assert routing['remainder_decision']['reason']=='no_eligible_evidence'
assert 'reduced_polynomial_form' not in routing['provider_called_for']
print('PASS: evidence hashes and audited sources match; this is integrity verification, not mathematical validation.')
