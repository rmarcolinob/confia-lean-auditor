#!/usr/bin/env python3
"""Sequential, checkpointed smoke test of exactly 18 synthetic ITA cases.

Dataset annotations select strata only; no score accuracy or error metric.
First run with --max-cases 1, inspect it, then use the same --output with --resume.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "dataset_1000_v1.2"
PROBLEMS = ("ITA2025Q1", "ITA2025Q3", "ITA2025Q4", "ITA2025F2Q1", "ITA2025F2Q5", "ITA2025F2Q6")
STRATA = (("alto", "correta"), ("parcial", "parcialmente_correta"), ("baixo", "incorreta"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "app"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(args):
    try:
        p = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=30,
                           env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
        return {"returncode": p.returncode, "stdout": p.stdout.decode("utf-8", "replace"),
                "stderr": p.stderr.decode("utf-8", "replace")}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": None, "stdout": "", "stderr": type(exc).__name__}


def write_json(path, data):
    raw = (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temp.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def source_hashes():
    # Explicit source/config allowlist: no .env, credentials, runtime or data copies.
    files = set()
    for folder, extensions in (("app", {".py"}), ("problems", {".json", ".lean"}),
                               ("ConfiaLeanAuditor", {".lean"}), ("scripts/evaluation", {".py"})):
        files.update(p for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix in extensions)
    files.update(ROOT / name for name in ("pyproject.toml", "lean-toolchain", "lakefile.toml", "lake-manifest.json", "ConfiaLeanAuditor.lean"))
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(files) if p.is_file()}


def snapshot():
    diff = subprocess.check_output(["git", "diff", "--no-ext-diff", "--no-textconv", "--binary"], cwd=ROOT)
    staged = subprocess.check_output(["git", "diff", "--cached", "--no-ext-diff", "--no-textconv", "--binary"], cwd=ROOT)
    hashes = source_hashes()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    return {"captured_at_utc": datetime.now(timezone.utc).isoformat(),
            "branch": command(["git", "branch", "--show-current"])["stdout"].strip(),
            "head": command(["git", "rev-parse", "HEAD"])["stdout"].strip(),
            "git_status_short": command(["git", "status", "--short"])["stdout"],
            "git_diff_check": command(["git", "diff", "--check"]),
            "git_diff_sha256": digest(diff), "git_staged_diff_sha256": digest(staged),
            "source_sha256": hashes,
            "relevant_untracked_sha256": {p: hashes[p] for p in untracked if p in hashes},
            "dataset_metadata_sha256": digest((DATASET / "metadados.jsonl").read_bytes()),
            "python": command([sys.executable, "--version"]), "python_executable": sys.executable,
            "lean": command(["lean", "--version"]), "lake": command(["lake", "--version"]),
            "execution_settings": {k: os.environ.get(k) for k in
                ("CONFIA_ENABLE_LLM_FORMAL_STEPS", "CONFIA_LLM_MODEL", "CONFIA_LEAN_AUDITOR_ROOT", "CONFIA_SECONDARY_MODEL")}}


def select_cases():
    rows = [json.loads(line) for line in (DATASET / "metadados.jsonl").read_text().splitlines()]
    if len(rows) != 1000 or len({r["id"] for r in rows}) != 1000:
        raise ValueError("Expected 1000 records with unique id")
    selected = []
    for problem in PROBLEMS:
        for label, situation in STRATA:
            candidates = [r for r in rows if r["qid"] == problem and r["situacao_global_final"] == situation]
            if label == "alto":
                candidates = [r for r in candidates if r["nota_final"] == r["nota_maxima"]]
            elif label == "parcial":
                candidates = [r for r in candidates if 0 < r["nota_final"] < r["nota_maxima"]]
            else:
                candidates = [r for r in candidates if r["nota_final"] <= r["nota_maxima"] / 2]
            if not candidates:
                raise ValueError(f"No candidate for {problem}/{label}; inspect selection before running")
            r = min(candidates, key=lambda item: item["id"])
            if not re.fullmatch(r"[A-Za-z0-9_]+", r["id"]):
                raise ValueError("Unsafe dataset id")
            text_hash = digest((DATASET / "respostas" / (r["id"] + ".txt")).read_bytes())
            if text_hash != r["texto_sha256"]:
                raise ValueError("Dataset text hash mismatch")
            selected.append({"dataset_id": r["id"], "problem_id": problem, "stratum": label,
                "categoria_final": r["categoria_final"], "situacao_global_final": situation,
                "nota_final": r["nota_final"], "nota_maxima": r["nota_maxima"], "text_sha256": text_hash})
    assert len(selected) == len({c["dataset_id"] for c in selected}) == 18
    return {"policy": "For each qid: correta and full nota_final; parcialmente_correta and 0<nota_final<nota_maxima; incorreta and nota_final<=nota_maxima/2. First id in each stratum. Synthetic labels only.",
            "cases": selected}


def safe_error(exc):
    value = str(exc) or str(getattr(exc, "detail", "")) or type(exc).__name__
    for key, secret in os.environ.items():
        if re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", key, re.I) and len(secret) >= 6:
            value = value.replace(secret, "[REDACTED]")
    return re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", value)[:2000]


def summarize(case, raw, elapsed, error=None):
    row = {"dataset_id": case["dataset_id"], "problem_id": case["problem_id"],
           "execution_status": "error" if error else "completed", "elapsed_seconds": elapsed,
           "synthetic_categoria_final": case["categoria_final"],
           "synthetic_situacao_global_final": case["situacao_global_final"],
           "synthetic_nota_final": case["nota_final"], "synthetic_nota_maxima": case["nota_maxima"],
           "warnings": [], "error_type": type(error).__name__ if error else None,
           "error_message": safe_error(error) if error else None}
    fields = ("confia_score confia_max_score confia_verdict claims_total formal_steps_total rubric_items_total "
              "rubric_supported rubric_refuted rubric_indeterminate rubric_decided student_claims_total "
              "student_claim_checks_total student_claim_verified student_claim_refuted student_claim_unverified "
              "student_claim_technical_error lean_used lean_status_summary run_id artifact_dir "
              "technical_error lean_failure_events lean_timeout").split()
    row.update(dict.fromkeys(fields))
    if raw is None:
        return row
    items = raw["rubric_assessment"]["items"]
    checks, steps, cert = raw["student_claim_checks"], raw["formal_steps"], raw["lean_certificate"]
    math = Counter(i.get("mathematical_status") for i in items)
    statuses = Counter(c["status"] for c in checks)
    failure_categories = Counter(c["failure_category"] for c in checks if c.get("failure_category"))
    # Count non-successful positive proof checks; refuted has a successful separate negation proof.
    failures = int(cert["status"] != "verified") + sum(s["status"] != "verified" for s in steps)
    failures += sum(bool(c.get("lean_file")) and c["status"] != "verified" for c in checks)
    diagnostics = "\n".join(str(x.get(k, "")) for x in [cert] + steps + checks
                            for k in ("stdout", "stderr", "refutation_stdout", "refutation_stderr")).lower()
    timeout = cert["exit_code"] == 124 or any(s["exit_code"] == 124 for s in steps) or "TIMEOUT" in failure_categories
    technical = any(x.get("verification_status") == "technical_error" for x in items + raw["microclaims"])
    technical = technical or statuses["technical_error"] > 0 or timeout or cert["exit_code"] == -1
    folder = raw.get("artifact_dir")
    row.update(confia_score=raw["score"], confia_max_score=raw["max_score"], confia_verdict=raw["verdict"],
        claims_total=len(raw["extracted_claims"]["claims"]), formal_steps_total=len(steps),
        rubric_items_total=len(items), rubric_supported=math["supported"], rubric_refuted=math["refuted"],
        rubric_indeterminate=math["indeterminate"], rubric_decided=sum(i["points"] is not None for i in items),
        student_claims_total=len(raw["student_claims"]), student_claim_checks_total=len(checks),
        student_claim_verified=statuses["verified"], student_claim_refuted=statuses["refuted"],
        student_claim_unverified=statuses["unverified"], student_claim_technical_error=statuses["technical_error"],
        lean_used=True, lean_status_summary={"certificate": cert["status"],
            "formal_steps": dict(Counter(s["status"] for s in steps)), "student_checks": dict(statuses),
            "failure_categories": dict(failure_categories), "timeout": timeout,
            "unknown_identifier": "unknown identifier" in diagnostics or "UNKNOWN_IDENTIFIER" in failure_categories,
            "unsolved_goals": "unsolved goals" in diagnostics or "UNSOLVED_GOALS" in failure_categories},
        run_id=Path(folder).name if folder else None, artifact_dir=folder,
        technical_error=technical, lean_failure_events=failures, lean_timeout=timeout)
    for key in ("scoring_policy", "evaluated_score", "evaluated_max_score", "coverage",
                "estimated_points", "needs_review", "unscorable_reason"):
        row[key] = raw.get(key)
    if folder is None or not (Path(folder) / "audit.json").is_file():
        row["warnings"].append("MISSING_AUDIT_ARTIFACT")
    if math[None]:
        row["warnings"].append("RUBRIC_MATHEMATICAL_STATUS_ABSENT")
    if case["problem_id"] == "ITA2025Q4":
        row["warnings"].append("Q4_DATASET_AND_AUDITOR_SCOPE_PARTIALLY_DIFFER")
    return row


def load_checkpoint(output):
    path = output / "smoke_results.jsonl"
    if not path.exists():
        return []
    rows, offset = [], 0
    lines = path.read_bytes().splitlines(keepends=True)
    for index, line in enumerate(lines):
        try:
            row = json.loads(line)
        except ValueError:
            if index != len(lines) - 1 or line.endswith(b"\n"):
                raise ValueError("Corrupt checkpoint")
            with path.open("r+b") as handle:
                handle.truncate(offset)
            break
        rows.append(row)
        offset += len(line)
    if len({r["dataset_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate checkpoint ids")
    return rows


def append_checkpoint(output, row):
    with (output / "smoke_results.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def report(output, state, cases, rows):
    times = [r["elapsed_seconds"] for r in rows]
    completed = [r for r in rows if r["execution_status"] == "completed"]
    dirs = [r["artifact_dir"] for r in rows if r.get("artifact_dir")]
    median = statistics.median(times) if times else 0
    threshold = max(10, 3 * median)
    summary = {"selected": len(cases), "attempted": len(rows), "completed": len(completed),
        "execution_errors": len(rows) - len(completed),
        "inconclusive": sum(r["confia_verdict"] == "inconclusivo" for r in completed),
        "score_null": sum(r["confia_score"] is None for r in completed),
        "zero_claims": sum(r["claims_total"] == 0 for r in completed),
        "zero_decided_criteria": sum(r["rubric_decided"] == 0 for r in completed),
        "cases_with_technical_error": sum(r["technical_error"] is True for r in rows),
        "student_claim_technical_errors": sum(r["student_claim_technical_error"] or 0 for r in rows),
        "cases_with_lean_failures": sum((r["lean_failure_events"] or 0) > 0 for r in rows),
        "lean_failure_events": sum(r["lean_failure_events"] or 0 for r in rows),
        "lean_timeout_cases": sum(r["lean_timeout"] is True for r in rows),
        "total_seconds": sum(times), "median_seconds": median, "max_seconds": max(times, default=0),
        "slow_threshold_seconds": threshold, "distinct_artifact_dirs": len(set(dirs)),
        "artifact_collisions": len(dirs) - len(set(dirs))}
    write_json(output / "summary.json", summary)
    lines = ["# Smoke test ITA1000 v1.2", "", "## Ambiente", "",
        f"Branch: `{state['branch']}`; HEAD: `{state['head']}`; dirty working tree: {bool(state['git_status_short'])}.",
        f"SHA-256 de git diff: `{state['git_diff_sha256']}`.",
        *[f"{k}: {state[k]['stdout'].strip() or state[k]['stderr']}" for k in ("python", "lean", "lake")],
        "", "Estado detalhado e hashes: `environment_snapshot.json`.", "", "## Amostra", "",
        "18 soluções selecionadas; 3 por questão. Execução sequencial, textos UTF-8 decodificados sem normalização.",
        "Labels sintéticas usadas apenas para estratificação; **as escalas/rubricas não são diretamente comparáveis**.",
        "Nenhuma acurácia, MAE ou diferença numérica de notas foi calculada.", "",
        "| problem_id | dataset_id | categoria_final | nota_final | execution_status | ConfIA score | ConfIA verdict | claims | criteria decididos/total | Lean | tempo (s) |",
        "|---|---|---|---:|---|---|---|---:|---|---|---:|"]
    for r in rows:
        score = "null" if r["confia_score"] is None else str(r["confia_score"])
        lean = json.dumps(r["lean_status_summary"], ensure_ascii=False)
        lines.append(f"| {r['problem_id']} | {r['dataset_id']} | {r['synthetic_categoria_final']} | {r['synthetic_nota_final']} | {r['execution_status']} | {score} | {r['confia_verdict']} | {r['claims_total']} | {r['rubric_decided']}/{r['rubric_items_total']} | {lean} | {r['elapsed_seconds']:.3f} |")
    lines += ["", "## Resumo", "", *[f"- {k}: {v}" for k, v in summary.items()], "",
        "Score null conta somente respostas concluídas; ausência de resposta por exceção é execution_error.",
        "Lean failures conta verificações positivas não bem-sucedidas (inclui refuted com prova separada da negação); não significa erro matemático. Status originais permanecem no JSON.",
        "Tempos medem somente a chamada do motor com relógio monotônico; total soma as chamadas, incluindo o caso piloto.",
        "", "## Casos para inspeção", ""]
    for r in rows:
        flags = []
        if r["execution_status"] == "error": flags.append("execution_error: " + str(r["error_type"]))
        if r["execution_status"] == "completed" and r["confia_score"] is None: flags.append("score null")
        if r["claims_total"] == 0: flags.append("zero claims")
        if r["rubric_decided"] == 0: flags.append("zero critérios decididos")
        if r["technical_error"]: flags.append("technical_error")
        if r["lean_timeout"]: flags.append("Lean timeout")
        if r["lean_failure_events"]: flags.append("Lean positive-check failure")
        if r["elapsed_seconds"] > threshold: flags.append("tempo > max(10s, 3×mediana)")
        flags += r["warnings"]
        if flags: lines.append(f"- `{r['dataset_id']}`: " + "; ".join(flags))
    lines += ["", "## Limitações", "", "Q4: o corpus pede identificar e provar a propriedade; o auditor fixa a conclusão e privilegia testemunhas específicas. F2Q6 permanece para observar a fragilidade de extração conhecida. Nenhuma correção do auditor foi feita.",
        "IDs sem resultado ainda estão pendentes. Exceções são checkpoints terminais; --resume não as reexecuta. Uma interrupção dentro do motor pode deixar artifacts órfãos, preservados.", ""]
    (output / "SMOKE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def run(args):
    output = args.output.resolve()
    current = snapshot()
    if args.selection_file:
        selection = json.loads(args.selection_file.read_text())
        cases = selection["cases"]
        if (len(cases) != 18 or len({c["dataset_id"] for c in cases}) != 18 or
                Counter(c["problem_id"] for c in cases) != Counter({p: 3 for p in PROBLEMS}) or
                any(not re.fullmatch(r"[A-Za-z0-9_]+", c["dataset_id"]) for c in cases)):
            raise ValueError("Selection file must contain exactly the 18 compatible cases")
    else:
        selection = select_cases()
    if args.resume:
        state = json.loads((output / "environment_snapshot.json").read_text())
        saved = json.loads((output / "selected_cases.json").read_text())
        for key in ("head", "branch", "git_diff_sha256", "git_staged_diff_sha256", "source_sha256", "dataset_metadata_sha256", "execution_settings", "python", "lean", "lake"):
            if state[key] != current[key]:
                raise ValueError(f"Resume state changed: {key}")
        if saved != selection:
            raise ValueError("Selection changed")
    else:
        if output.exists():
            raise ValueError("Output exists; use --resume")
        output.mkdir(parents=True)
        (output / "results").mkdir()
        (output / "checkpoints").mkdir()
        state = current
        write_json(output / "environment_snapshot.json", state)
        write_json(output / "selected_cases.json", selection)
    with (output / ".runner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        cases = selection["cases"]
        rows = load_checkpoint(output)
        allowed = {c["dataset_id"] for c in cases}
        if any(r["dataset_id"] not in allowed for r in rows):
            raise ValueError("Unexpected checkpoint id")
        done = {r["dataset_id"] for r in rows}
        for c in cases:
            case_id = c["dataset_id"]
            checkpoint = output / "checkpoints" / (case_id + ".json")
            if case_id not in done and checkpoint.exists():
                row = json.loads(checkpoint.read_text())
                append_checkpoint(output, row)
                rows.append(row)
                done.add(case_id)
        for row in rows:
            if row["execution_status"] == "completed":
                raw_path = output / "results" / (row["dataset_id"] + ".json")
                if digest(raw_path.read_bytes()) != row["result_sha256"]:
                    raise ValueError("Saved result integrity mismatch")
        count = 0
        for case in cases:
            if case["dataset_id"] in done or count >= args.max_cases:
                continue
            text_bytes = (DATASET / "respostas" / (case["dataset_id"] + ".txt")).read_bytes()
            if digest(text_bytes) != case["text_sha256"]:
                raise ValueError("Selected text changed")
            solution = text_bytes.decode("utf-8")
            raw, error, elapsed = None, None, 0.0
            started = None
            try:
                from confia_lean_auditor.main import execute_audit
                from confia_lean_auditor.core.schemas import AuditRequest, AuditResponse
                request = AuditRequest(problem_id=case["problem_id"], solution=solution)
                started = time.monotonic()
                response = execute_audit(request)
                elapsed = time.monotonic() - started
                if not isinstance(response, AuditResponse):
                    raise TypeError("Expected AuditResponse")
                raw = response.model_dump(mode="json")
            except Exception as exc:
                if started is not None:
                    elapsed = time.monotonic() - started
                error = exc
            result_path = output / "results" / (case["dataset_id"] + ".json")
            write_json(result_path, raw if raw is not None else {"error_type": type(error).__name__, "error_message": safe_error(error)})
            row = summarize(case, raw, elapsed, error)
            row["result_sha256"] = digest(result_path.read_bytes())
            if row["artifact_dir"] and row["artifact_dir"] in {r["artifact_dir"] for r in rows}:
                row["warnings"].append("ARTIFACT_DIRECTORY_COLLISION")
            write_json(output / "checkpoints" / (case["dataset_id"] + ".json"), row)
            append_checkpoint(output, row)
            rows.append(row)
            done.add(case["dataset_id"])
            count += 1
            report(output, state, cases, rows)
            print(f"[{len(rows)}/18] {case['problem_id']} {case['dataset_id']} ... {row['execution_status']} {elapsed:.2f}s score={json.dumps(row['confia_score'])} verdict={row['confia_verdict']}", flush=True)
        report(output, state, cases, rows)
        print(f"Output: {output}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/evaluations/ita1000_v1_2" / ("smoke_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--selection-file", type=Path, help="Reuse saved IDs verbatim without selecting again")
    parser.add_argument("--max-cases", type=int, choices=range(1, 19), default=18,
                        help="Maximum pending cases in this invocation; selection is always exactly 18")
    run(parser.parse_args())
