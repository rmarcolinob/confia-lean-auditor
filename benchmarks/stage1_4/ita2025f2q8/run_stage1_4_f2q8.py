from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Set

from confia_lean_auditor.claims.extract_claims import extract_claims


ROOT = Path(__file__).resolve().parents[3]
BENCH_DIR = ROOT / "benchmarks" / "stage1_4" / "ita2025f2q8"
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


def check_assets(problem_id: str) -> Dict[str, bool]:
    problem_dir = ROOT / "problems" / problem_id
    lean_statement = ROOT / "ConfiaLeanAuditor" / "Problems" / problem_id / "Statement.lean"

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gold",
        default=str(BENCH_DIR / "gold_100.csv"),
        help="CSV gold file to evaluate.",
    )
    parser.add_argument(
        "--out",
        default=str(REPORTS_DIR / "stage1_4_f2q8_report_100.json"),
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

    claim_tp = claim_fp = claim_fn = 0
    step_tp = step_fp = step_fn = 0
    claim_exact_sum = 0.0
    step_exact_sum = 0.0

    input_valid_count = 0
    load_success_count = 0
    extraction_success_count = 0

    by_category = {}

    for row in rows:
        row_id = row["id"]
        problem_id = row["problem_id"]
        solution = row["solution"]
        category = row["category"]

        input_valid = bool(problem_id and solution)
        if input_valid:
            input_valid_count += 1

        assets = check_assets(problem_id)
        load_success = all(assets.values())
        if load_success:
            load_success_count += 1

        expected_claims = parse_set(row["expected_claims"])
        expected_steps = parse_set(row["expected_formal_steps"])

        extraction, error = safe_extract(problem_id, solution)
        if extraction is not None:
            extraction_success_count += 1
            got_claims = {claim.type for claim in extraction.claims}
            got_steps = {step.type for step in extraction.formal_steps}
        else:
            got_claims = set()
            got_steps = set()

        claim_metrics = prf(expected_claims, got_claims)
        step_metrics = prf(expected_steps, got_steps)

        claim_tp += int(claim_metrics["tp"])
        claim_fp += int(claim_metrics["fp"])
        claim_fn += int(claim_metrics["fn"])
        step_tp += int(step_metrics["tp"])
        step_fp += int(step_metrics["fp"])
        step_fn += int(step_metrics["fn"])

        claim_exact_sum += claim_metrics["exact"]
        step_exact_sum += step_metrics["exact"]

        cat = by_category.setdefault(
            category,
            {
                "n": 0,
                "claim_tp": 0,
                "claim_fp": 0,
                "claim_fn": 0,
                "step_tp": 0,
                "step_fp": 0,
                "step_fn": 0,
                "claim_exact": 0.0,
                "step_exact": 0.0,
            },
        )
        cat["n"] += 1
        cat["claim_tp"] += int(claim_metrics["tp"])
        cat["claim_fp"] += int(claim_metrics["fp"])
        cat["claim_fn"] += int(claim_metrics["fn"])
        cat["step_tp"] += int(step_metrics["tp"])
        cat["step_fp"] += int(step_metrics["fp"])
        cat["step_fn"] += int(step_metrics["fn"])
        cat["claim_exact"] += claim_metrics["exact"]
        cat["step_exact"] += step_metrics["exact"]

        detailed.append(
            {
                "id": row_id,
                "category": category,
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

    n = len(rows)

    def aggregate(tp: int, fp: int, fn: int) -> Dict[str, float]:
        precision = tp / (tp + fp) if (tp + fp) else 1.0
        recall = tp / (tp + fn) if (tp + fn) else 1.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        return {"precision": precision, "recall": recall, "f1": f1}

    claim_agg = aggregate(claim_tp, claim_fp, claim_fn)
    step_agg = aggregate(step_tp, step_fp, step_fn)

    by_category_summary = {}
    for category, cat in sorted(by_category.items()):
        claim_cat = aggregate(cat["claim_tp"], cat["claim_fp"], cat["claim_fn"])
        step_cat = aggregate(cat["step_tp"], cat["step_fp"], cat["step_fn"])
        by_category_summary[category] = {
            "n": cat["n"],
            "claim_precision": claim_cat["precision"],
            "claim_recall": claim_cat["recall"],
            "claim_f1": claim_cat["f1"],
            "claim_exact_match": cat["claim_exact"] / cat["n"] if cat["n"] else 0.0,
            "formal_step_precision": step_cat["precision"],
            "formal_step_recall": step_cat["recall"],
            "formal_step_f1": step_cat["f1"],
            "formal_step_exact_match": cat["step_exact"] / cat["n"] if cat["n"] else 0.0,
        }

    summary = {
        "problem_id": "ITA2025F2Q8",
        "gold_path": str(gold_path),
        "n": n,
        "stage_1_input_valid_rate": input_valid_count / n if n else 0.0,
        "stage_2_load_success_rate": load_success_count / n if n else 0.0,
        "stage_3_extraction_success_rate": extraction_success_count / n if n else 0.0,
        "stage_3_claim_precision": claim_agg["precision"],
        "stage_3_claim_recall": claim_agg["recall"],
        "stage_3_claim_f1": claim_agg["f1"],
        "stage_3_claim_exact_match": claim_exact_sum / n if n else 0.0,
        "stage_4_formal_step_precision": step_agg["precision"],
        "stage_4_formal_step_recall": step_agg["recall"],
        "stage_4_formal_step_f1": step_agg["f1"],
        "stage_4_formal_step_exact_match": step_exact_sum / n if n else 0.0,
        "claim_counts": {"tp": claim_tp, "fp": claim_fp, "fn": claim_fn},
        "formal_step_counts": {"tp": step_tp, "fp": step_fp, "fn": step_fn},
        "by_category": by_category_summary,
    }

    report = {"summary": summary, "rows": detailed}

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

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
        for item in failures:
            print(f"- {item['id']} [{item['category']}]")
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


if __name__ == "__main__":
    main()
