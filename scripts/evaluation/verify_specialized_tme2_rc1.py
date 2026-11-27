#!/usr/bin/env python3
"""Verify the RC1 inventory and reference bundle without extracting or grading."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--environment', action='store_true', help='Also check Python, packages and local Lean dependencies')
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest or root/'docs/audits/assets/specialized-tme2-rc1/manifest.json'
    expected = manifest.with_suffix('.sha256').read_text().split()[0]
    if sha(manifest) != expected:
        raise ValueError('Manifest checksum mismatch')
    data = json.loads(manifest.read_text())
    for relative, record in data['files'].items():
        path = (root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha(path) != record['sha256']:
            raise ValueError(f'Source/evidence mismatch: {relative}')
    bundle = args.bundle or root/data['reference_bundle']['path']
    if sha(bundle) != data['reference_bundle']['sha256']:
        raise ValueError('Reference bundle checksum mismatch')
    expected_files = data['reference_bundle']['members']
    with tarfile.open(bundle, 'r:gz') as archive:
        members = archive.getmembers()
        if len(members) != len(expected_files) or {m.name for m in members} != set(expected_files):
            raise ValueError('Reference bundle inventory mismatch')
        for member in members:
            record = expected_files[member.name]
            if not member.isfile() or member.size != record['size_bytes']:
                raise ValueError(f'Invalid archive member: {member.name}')
            with archive.extractfile(member) as source:
                if hashlib.sha256(source.read()).hexdigest() != record['sha256']:
                    raise ValueError(f'Historical artifact mismatch: {member.name}')
    # Import only after all source hashes match. No AuditService/provider call.
    sys.path.insert(0, str(root/'app'))
    from confia_lean_auditor.tme.accepted_audit import audit_context
    if audit_context('TME2026P5', True).auditor_version != data['auditor']['fingerprint']:
        raise ValueError('Auditor fingerprint mismatch')
    if args.environment:
        env = data['environment']
        from confia_lean_auditor.semantic_policy.service import configuration
        provider = configuration()
        frozen = data['provider']['observed_configuration']
        if any(provider[key] != frozen[key] for key in ('policy', 'model', 'reasoning_effort')):
            raise ValueError('Semantic provider configuration mismatch')
        if os.environ.get('CONFIA_TME_QUESTION_USE_LEAN', '1') == '0':
            raise ValueError('Exam Lean disabled; candidate requires Lean')
        if '.'.join(map(str, sys.version_info[:3])) != env['python_version']:
            raise ValueError('Python version mismatch')
        for package, version in env['python_packages'].items():
            if importlib.metadata.version(package) != version:
                raise ValueError(f'Python dependency mismatch: {package}')
        for command in ('lean', 'lake'):
            actual = subprocess.check_output([command, '--version'], cwd=root, text=True).strip()
            if actual != env[command + '_version']:
                raise ValueError(f'{command} version/build mismatch')
        for name, record in env['lake_packages'].items():
            folder = root/'.lake/packages'/name
            revision = subprocess.check_output(['git', '-C', str(folder), 'rev-parse', 'HEAD'], text=True).strip()
            dirty = subprocess.check_output(['git', '-C', str(folder), 'status', '--porcelain'], text=True).strip()
            if revision != record['locked_revision'] or dirty:
                raise ValueError(f'Lake dependency mismatch: {name}')
    print(json.dumps(dict(candidate=data['candidate'], files_verified=len(data['files']),
                          historical_members_verified=len(expected_files),
                          auditor_fingerprint=data['auditor']['fingerprint'],
                          environment_checked=args.environment, audits_executed=0, api_calls=0)))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, tarfile.TarError, subprocess.CalledProcessError,
            importlib.metadata.PackageNotFoundError) as error:
        print(f'RC1 verification failed: {error}', file=sys.stderr)
        sys.exit(1)
