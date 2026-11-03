#!/usr/bin/env python3
"""Explicit manual execution of Experiment B. No gold, no automatic benchmark."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app"))
from confia_lean_auditor.semantic.semantic_student_claim import PROBLEMS
from confia_lean_auditor.evaluation.formal_award_gate import EXPERIMENT_DESIGN, AWARD_POLICY
from confia_lean_auditor.evaluation.structural_metrics import aggregate_metrics

BASE_SHA = "8f50835f939110105eb20b8ae6fd6a78bbaa2649"
FIXTURES = Path(__file__).parent / "fixtures"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def forbidden_path(path):
    for candidate in (Path(path), Path(path).resolve()):
        name = candidate.name.lower()
        if "gold" in name or name.startswith(("notas_", "grades", "reference_score")):
            return True
    return False


def safe_path(path):
    path = Path(path).expanduser()
    if forbidden_path(path):
        raise ValueError("Gold/grade file access forbidden")
    return path.resolve(strict=True)


def install_guards(offline):
    def guard(event, args):
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            if forbidden_path(os.fsdecode(args[0])):
                raise PermissionError("Gold/grade file access forbidden")
        if offline and event in {"socket.connect", "socket.connect_ex", "socket.getaddrinfo", "socket.sendto"}:
            raise PermissionError("Network forbidden in FORMAL_OFFLINE")
    sys.addaudithook(guard)


def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def load_dataset(path):
    path = safe_path(path)
    cases = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        if path.suffix.lower() == ".csv":
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["id", "qid", "texto"]:
                raise ValueError("CSV schema must be exactly id,qid,texto; no grade columns")
            for row in reader:
                if set(row) != {"id", "qid", "texto"}:
                    raise ValueError("Malformed CSV row")
                cases.append(dict(solution_id=row["id"], problem_id=row["qid"], text=row["texto"]))
        elif path.suffix.lower() == ".jsonl":
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict) or set(row) != {"solution_id", "problem_id", "text"}:
                    raise ValueError("JSONL schema must be exactly solution_id,problem_id,text")
                cases.append(row)
        else:
            raise ValueError("Dataset must be CSV or JSONL")
    seen = set()
    for case in cases:
        if any(not isinstance(v, str) for v in case.values()) or not case["solution_id"]:
            raise ValueError("Dataset fields must be strings and IDs nonempty")
        if case["solution_id"] in seen:
            raise ValueError("Duplicate solution_id")
        seen.add(case["solution_id"])
    return cases


def select_cases(cases, population, problem_id=None, ids=None, limit=None):
    frozen = {r["solution_id"]: r for r in population}
    if len(frozen) != len(population):
        raise ValueError("Duplicate population ID")
    if ids is not None and (not ids or len(ids) != len(set(ids)) or set(ids) - set(frozen)):
        raise ValueError("IDs must be nonempty, unique and part of frozen population")
    selected = []
    wanted = set(ids) if ids is not None else set(frozen)
    if problem_id:
        wanted = {sid for sid in wanted if frozen[sid]["problem_id"] == problem_id}
    for case in cases:
        if case["solution_id"] not in wanted:
            continue
        reference = frozen[case["solution_id"]]
        if (case["problem_id"] not in PROBLEMS or case["problem_id"] != reference["problem_id"]
            or digest(case["text"].encode()) != reference["source_sha256"]):
            raise ValueError("Dataset does not match frozen population")
        selected.append(case)
    if {c["solution_id"] for c in selected} != wanted:
        raise ValueError("Missing population IDs in dataset")
    selected.sort(key=lambda c: (c["problem_id"], c["solution_id"]))
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        selected = selected[:limit]
    if not selected:
        raise ValueError("Empty selection")
    return selected


def uniform_pilot(population):
    selected = []
    for pid in PROBLEMS:
        ids = sorted(r["solution_id"] for r in population if r["problem_id"] == pid)
        if len(ids) < 6:
            raise ValueError("Need at least six IDs per problem")
        selected.extend(ids[(i * (len(ids) - 1)) // 5] for i in range(6))
    return selected


def provenance():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    # Verify *every* frozen core file, not merely HEAD. New experimental files allowed.
    files = git("ls-tree", "-r", "--name-only", BASE_SHA).splitlines()
    protected = [p for p in files if p.startswith(("app/", "problems/", "ConfiaLeanAuditor/"))
                 or p in {"lakefile.toml", "lake-manifest.json", "lean-toolchain", "ConfiaLeanAuditor.lean"}]
    current = {}
    for relative in protected:
        path = ROOT / relative
        # git hash-object is read-only unless -w is supplied.
        actual = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
        expected = git("rev-parse", f"{BASE_SHA}:{relative}")
        if actual != expected:
            raise ValueError("Frozen historical file modified: " + relative)
        current[relative] = actual
    experimental = {}
    for directory in (ROOT / "app/confia_lean_auditor/semantic", ROOT / "app/confia_lean_auditor/evaluation", ROOT / "scripts/evaluation"):
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix in {".py", ".json", ".sh"}:
                experimental[str(path.relative_to(ROOT))] = digest(path.read_bytes())
    return {"code_sha": git("rev-parse", "HEAD"), "historical_base_sha": BASE_SHA,
            "historical_core_verified": True, "historical_blob_ids": current,
            "experimental_file_sha256": experimental,
            "code_dirty": bool(git("status", "--porcelain"))}


def prepare_runtime(output, cache):
    if cache is None:
        raise ValueError("A prebuilt historical .lake cache is required; pass --lean-cache (no automatic downloads)")
    runtime = output / "execution"
    runtime.mkdir()
    for name in ("ConfiaLeanAuditor", "problems"):
        shutil.copytree(ROOT / name, runtime / name)
    for name in ("ConfiaLeanAuditor.lean", "lakefile.toml", "lake-manifest.json", "lean-toolchain"):
        shutil.copy2(ROOT / name, runtime / name)
    # Cache source is never written; clone to this new evaluation directory.
    if cache is not None:
        cache = safe_path(cache)
        origin = cache.parent
        for name in ("lake-manifest.json", "lean-toolchain"):
            if (origin / name).read_bytes() != (ROOT / name).read_bytes():
                raise ValueError("Lean cache uses different pinned dependencies")
        for path in (ROOT / "ConfiaLeanAuditor").rglob("*.lean"):
            if (origin / path.relative_to(ROOT)).read_bytes() != path.read_bytes():
                raise ValueError("Lean cache source mismatch")
        if sys.platform == "darwin":
            subprocess.run(["cp", "-cR", str(cache), str(runtime / ".lake")], check=True)
        else:
            shutil.copytree(cache, runtime / ".lake", symlinks=True)
    return runtime


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--problem-id", choices=PROBLEMS)
    parser.add_argument("--mode", choices=("formal_offline", "semantic_formal"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ids-file", type=Path)
    parser.add_argument("--lean-cache", type=Path, help="Existing .lake cache, cloned into new output")
    args = parser.parse_args(argv)
    sys.dont_write_bytecode = True
    os.environ["CONFIA_ENABLE_LLM_FORMAL_STEPS"] = "0"
    install_guards(args.mode == "formal_offline")
    prov = provenance()
    population = json.loads((FIXTURES / "population_b.json").read_text())["cases"]
    ids = json.loads(safe_path(args.ids_file).read_text()) if args.ids_file else None
    if ids is not None and (not isinstance(ids, list) or not all(isinstance(s, str) for s in ids)):
        raise ValueError("ids-file must be a JSON array of strings")
    cases = select_cases(load_dataset(args.dataset), population, args.problem_id, ids, args.limit)
    output = args.output_dir.expanduser().resolve()
    if any(output == ROOT / p or ROOT / p in output.parents for p in ("app", "problems", "ConfiaLeanAuditor", "scripts", "tests", "docs", ".git")):
        raise ValueError("Output must be a new evaluation directory")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "environment.json", dict(prov, created_at=datetime.now(timezone.utc).isoformat(),
        dataset=str(safe_path(args.dataset)), dataset_sha256=digest(safe_path(args.dataset).read_bytes()),
        model=args.model, reasoning_effort=args.reasoning_effort, mode=args.mode,
        experiment_design=EXPERIMENT_DESIGN, award_policy=AWARD_POLICY, gold_used=False, python=sys.version))
    write_json(output / "selection.json", [{k: v for k, v in c.items() if k != "text"} for c in cases])
    cache = args.lean_cache or (ROOT / ".lake" if (ROOT / ".lake").exists() else None)
    runtime = prepare_runtime(output, cache)
    from confia_lean_auditor.evaluation.semantic_formal_b import evaluate_case
    rows = []
    with (output / "results.jsonl").open("x", encoding="utf-8") as handle:
        for index, case in enumerate(cases):
            case_dir = output / "cases" / f"{index:04d}"
            case_dir.mkdir(parents=True, exist_ok=False)
            row = evaluate_case(runtime, case_dir, case, args.mode,
                                args.model, args.reasoning_effort)
            row.update(code_sha=prov["code_sha"], historical_base_sha=BASE_SHA,
                       source_sha256=digest(case["text"].encode()),
                       experimental_file_sha256=prov["experimental_file_sha256"])
            write_json(output / "cases" / f"{index:04d}" / "result.json", row)
            handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
            handle.flush()
            rows.append(row)
            print(f'{index + 1}/{len(cases)} {case["solution_id"]}: {row["score"]} ({row["mode_effective"]})', flush=True)
    write_json(output / "summary.json", {"cases": len(rows), **aggregate_metrics(rows),
        "mean_score": sum(r["score"] for r in rows) / len(rows),
        "lean_status_counts": dict(Counter(r["lean_status"] for r in rows)),
        "api_status_counts": dict(Counter(r["api_status"] for r in rows)),
        "by_problem": {p: {"cases": sum(r["problem_id"] == p for r in rows),
            "mean_score": sum(r["score"] for r in rows if r["problem_id"] == p) / sum(r["problem_id"] == p for r in rows),
            **aggregate_metrics([r for r in rows if r["problem_id"] == p])}
            for p in sorted({r["problem_id"] for r in rows})},
        "experiment_design": EXPERIMENT_DESIGN, "award_policy": AWARD_POLICY, "gold_used": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
