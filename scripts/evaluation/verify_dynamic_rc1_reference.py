#!/usr/bin/env python3
"""Verify the archived DYNAMIC candidate at its Git source commit, not HEAD.

Preparation files remain byte-identical in the integrated tree. No environment
claim, audit, provider call, repository mutation or tag creation is performed.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path('docs/audits/assets/dynamic-rc1')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(root=ROOT):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root)

    raw = (root / ASSETS / 'manifest.json').read_bytes()
    if sha(raw) != (root / ASSETS / 'manifest.sha256').read_text().split()[0]:
        raise ValueError('Manifest checksum mismatch')
    manifest = json.loads(raw)
    base = manifest['source_commit']
    git('merge-base', '--is-ancestor', base, 'HEAD')
    protected = manifest['protected_specialized']
    for suffix, expected in [('', protected['tag_object']), ('^{}', protected['commit'])]:
        if git('rev-parse', 'refs/tags/' + protected['tag'] + suffix).decode().strip() != expected:
            raise ValueError('Protected SPECIALIZED tag changed')
    for group in ('source_files', 'preparation_files'):
        for name, expected in manifest[group].items():
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError('Unsafe manifest path: ' + name)
            data = git('show', base + ':' + name) if group == 'source_files' else path.read_bytes()
            if {'sha256': sha(data), 'size_bytes': len(data)} != expected:
                raise ValueError('Reference mismatch: ' + name)
    content = {p: v['sha256'] for p, v in manifest['source_files'].items() if p.startswith('app/')}
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    if 'dynamic-candidate-content.v1:' + sha(canonical) != manifest['fingerprint']:
        raise ValueError('Candidate fingerprint mismatch')
    return dict(source_commit=base, source_files=len(manifest['source_files']),
                preparation_files=len(manifest['preparation_files']),
                fingerprint=manifest['fingerprint'], scope='ARCHIVED_REFERENCE_NOT_CURRENT_CHECKOUT',
                protected_specialized_intact=True, environment_checked=False, api_calls=0)


if __name__ == '__main__':
    try:
        print(json.dumps(verify(), indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        raise SystemExit('Archived candidate verification failed: ' + str(error))
