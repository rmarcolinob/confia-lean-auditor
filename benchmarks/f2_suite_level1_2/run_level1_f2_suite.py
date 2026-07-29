from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

from confia_lean_auditor.claims.extract_claims import extract_claims


ROOT = Path(__file__).resolve().parents[2]
BENCH_DIR = ROOT / "benchmarks" / "f2_suite_level1_2"
REPORTS_DIR = BENCH_DIR / "reports"


def parse_set(value: str) -> Set[str]:
    value = (value or "").strip()
    if not value:
        return set()
    return {x.strip() for x in value.split("|") if x.strip()}


def prf(expected: Set[str], got: Set[str]) -> Dict[str, float]:
    tp = len(expected & got)
    fp = len(got - expected)
    fn = len(expected - got)

    precision = tp / (tp + fp) if (tp + fp) else (1.0 if not expected else 0.0)
    recall = tp / (tp + fn) if (tp + fn) else (1.0 if not got else 0.0)
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact": float(expected == got),
    }


def aggregate(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {"precision": precision, "recall": recall, "f1": f1}


def check_assets(problem_id: str) -> Dict[str, bool]:
    problem_dir = ROOT / "problems" / problem_id
    lean_statement = (
        ROOT / "ConfiaLeanAuditor" / "Problems" / problem_id / "Statement.lean"
    )

    return {
        "problem_json": (problem_dir / "problem.json").exists(),
        "rubric_json": (problem_dir / "rubric.json").exists(),
        "microclaims_json": (problem_dir / "microclaims.json").exists(),
        "statement_lean": lean_statement.exists(),
    }


def safe_extract(problem_id: str, solution: str):
    try:
        result = extract_claims(problem_id, solution)
        return result, None
    except Exception as exc:
        return None, repr(exc)


def empty_bucket() -> Dict[str, float | int]:
    return {
        "n": 0,
        "claim_tp": 0,
        "claim_fp": 0,
        "claim_fn": 0,
        "step_tp": 0,
        "step_fp": 0,
        "step_fn": 0,
        "claim_exact": 0.0,
        "step_exact": 0.0,
        "input_valid": 0,
        "load_success": 0,
        "extraction_success": 0,
    }


def update_bucket(
    bucket: Dict[str, float | int],
    claim_metrics: Dict[str, float],
    step_metrics: Dict[str, float],
    input_valid: bool,
    load_success: bool,
    extraction_success: bool,
) -> None:
    bucket["n"] += 1
    bucket["claim_tp"] += int(claim_metrics["tp"])
    bucket["claim_fp"] += int(claim_metrics["fp"])
    bucket["claim_fn"] += int(claim_metrics["fn"])
    bucket["step_tp"] += int(step_metrics["tp"])
    bucket["step_fp"] += int(step_metrics["fp"])
    bucket["step_fn"] += int(step_metrics["fn"])
    bucket["claim_exact"] += claim_metrics["exact"]
    bucket["step_exact"] += step_metrics["exact"]
    bucket["input_valid"] += int(input_valid)
    bucket["load_success"] += int(load_success)
    bucket["extraction_success"] += int(extraction_success)


def summarize_bucket(bucket: Dict[str, float | int]) -> Dict[str, float | int]:
    n = int(bucket["n"])
    claim = aggregate(
        int(bucket["claim_tp"]),
        int(bucket["claim_fp"]),
        int(bucket["claim_fn"]),
    )
    step = aggregate(
        int(bucket["step_tp"]),
        int(bucket["step_fp"]),
        int(bucket["step_fn"]),
    )

    return {
        "n": n,
        "stage_1_input_valid_rate": bucket["input_valid"] / n if n else 0.0,
        "stage_2_load_success_rate": bucket["load_success"] / n if n else 0.0,
        "stage_3_extraction_success_rate": bucket["extraction_success"] / n if n else 0.0,
        "claim_tp": int(bucket["claim_tp"]),
        "claim_fp": int(bucket["claim_fp"]),
        "claim_fn": int(bucket["claim_fn"]),
        "claim_precision": claim["precision"],
        "claim_recall": claim["recall"],
        "claim_f1": claim["f1"],
        "claim_exact_match": bucket["claim_exact"] / n if n else 0.0,
        "formal_step_tp": int(bucket["step_tp"]),
        "formal_step_fp": int(bucket["step_fp"]),
        "formal_step_fn": int(bucket["step_fn"]),
        "formal_step_precision": step["precision"],
        "formal_step_recall": step["recall"],
        "formal_step_f1": step["f1"],
        "formal_step_exact_match": bucket["step_exact"] / n if n else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gold",
        default=str(BENCH_DIR / "gold_500.csv"),
        help="CSV gold file to evaluate.",
    )
    parser.add_argument(
        "--out",
        default=str(REPORTS_DIR / "level1_f2_suite_report_500.json"),
        help="Output JSON report path.",
    )
    args = parser.parse_args()

    gold_path = Path(args.gold)
    out_path = Path(args.out)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with gold_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    detailed = []

    global_bucket = empty_bucket()
    by_problem: Dict[str, Dict[str, float | int]] = {}
    by_category: Dict[str, Dict[str, float | int]] = {}
    by_problem_category: Dict[Tuple[str, str], Dict[str, float | int]] = {}

    for row in rows:
        row_id = row["id"]
        problem_id = row["problem_id"]
        category = row["category"]
        solution = row["solution"]

        input_valid = bool(problem_id and solution)
        assets = check_assets(problem_id)
        load_success = all(assets.values())

        expected_claims = parse_set(row.get("expected_claims", ""))
        expected_steps = parse_set(row.get("expected_formal_steps", ""))

        extraction, error = safe_extract(problem_id, solution)
        extraction_success = extraction is not None

        if extraction_success:
            got_claims = {claim.type for claim in extraction.claims}
            got_steps = {step.type for step in extraction.formal_steps}
        else:
            got_claims = set()
            got_steps = set()

        claim_metrics = prf(expected_claims, got_claims)
        step_metrics = prf(expected_steps, got_steps)

        for bucket in [
            global_bucket,
            by_problem.setdefault(problem_id, empty_bucket()),
            by_category.setdefault(category, empty_bucket()),
            by_problem_category.setdefault((problem_id, category), empty_bucket()),
        ]:
            update_bucket(
                bucket,
                claim_metrics=claim_metrics,
                step_metrics=step_metrics,
                input_valid=input_valid,
                load_success=load_success,
                extraction_success=extraction_success,
            )

        detailed.append(
            {
                "id": row_id,
                "problem_id": problem_id,
                "category": category,
                "solution": solution,
                "input_valid": input_valid,
                "assets": assets,
                "load_success": load_success,
                "extraction_error": error,
                "expected_claims": sorted(expected_claims),
                "got_claims": sorted(got_claims),
                "missing_claims": sorted(expected_claims - got_claims),
                "extra_claims": sorted(got_claims - expected_claims),
                "expected_formal_steps": sorted(expected_steps),
                "got_formal_steps": sorted(got_steps),
                "missing_formal_steps": sorted(expected_steps - got_steps),
                "extra_formal_steps": sorted(got_steps - expected_steps),
                "claim_metrics": claim_metrics,
                "formal_step_metrics": step_metrics,
            }
        )

    summary = {
        "benchmark": "f2_suite_level1",
        "description": (
            "Validação estatística global da 2ª fase — Nível 1: entrada, "
            "carregamento de assets, extração de claims e geração de formal_steps."
        ),
        "gold_path": str(gold_path),
        "n": len(rows),
        "global": summarize_bucket(global_bucket),
        "by_problem": {
            problem_id: summarize_bucket(bucket)
            for problem_id, bucket in sorted(by_problem.items())
        },
        "by_category": {
            category: summarize_bucket(bucket)
            for category, bucket in sorted(by_category.items())
        },
        "by_problem_category": {
            f"{problem_id}::{category}": summarize_bucket(bucket)
            for (problem_id, category), bucket in sorted(by_problem_category.items())
        },
    }

    report = {"summary": summary, "rows": detailed}
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    failures = [
        item
        for item in detailed
        if item["extraction_error"]
        or item["missing_claims"]
        or item["extra_claims"]
        or item["missing_formal_steps"]
        or item["extra_formal_steps"]
    ]

    if failures:
        print("\nCASOS COM DIVERGÊNCIA:")
        for item in failures[:80]:
            print(f"- {item['id']} [{item['problem_id']} {item['category']}]")
            if item["extraction_error"]:
                print("  extraction_error:", item["extraction_error"])
            if item["missing_claims"]:
                print("  missing_claims:", item["missing_claims"])
            if item["extra_claims"]:
                print("  extra_claims:", item["extra_claims"])
            if item["missing_formal_steps"]:
                print("  missing_formal_steps:", item["missing_formal_steps"])
            if item["extra_formal_steps"]:
                print("  extra_formal_steps:", item["extra_formal_steps"])

        if len(failures) > 80:
            print(f"... mais {len(failures) - 80} divergências omitidas no console")


if __name__ == "__main__":
    main()
