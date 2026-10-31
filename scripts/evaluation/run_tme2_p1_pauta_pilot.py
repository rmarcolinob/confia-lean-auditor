"""Small, fixed DIGITAL pilot; local deterministic checks/optional local Lean.

Run with `python -m scripts.evaluation.run_tme2_p1_pauta_pilot --output PATH
--with-lean`. No dataset enumeration or network client is used.
"""
import argparse
import json
from pathlib import Path

from confia_lean_auditor.rubric.pauta import load_pauta
from confia_lean_auditor.rubric.pauta.bridge import TME2_P1_OBLIGATIONS
from confia_lean_auditor.rubric.pauta.tme2_p1 import audit_tme2_p1_digital

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--with-lean", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    config = load_pauta(ROOT / "examples/pautas/tme2_problem1.v1.json")
    cases = json.loads((ROOT / "tests/fixtures/tme2_p1_digital/cases.json").read_text())
    rows, coverage, formal = [], set(), []
    for case in cases:
        bridge, result = audit_tme2_p1_digital(config, {case["item"]: case["text"]}, case["id"],
            use_lean=args.with_lean, run_id="tme2-p1-" + case["id"])
        item = result.items["abcd".index(case["item"])]
        portion = item.children[2] if case["item"] == "c" else item
        passed = item.points_awarded == case["points"]
        if "band" in case:
            passed = passed and portion.selected_band == case["band"]
        if "band_points" in case:
            passed = passed and portion.points_awarded == case["band_points"]
        payload = dict(case=case, bridge=bridge.model_dump(mode="json"), assessment=result.model_dump(mode="json"), passed=passed)
        (args.output / (case["id"] + ".json")).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        coverage.update(e.obligation_id for e in bridge.evidence.obligations if e.status == "supported")
        checks = [dict(case_id=case["id"], fact_id=f.fact_id, status=f.verification.status,
            artifact_ref=f.verification.artifact_ref, verification_source=f.verification_source)
            for f in bridge.auditor.facts if f.student_check]
        formal.extend(checks)
        rows.append(dict(case_id=case["id"], item=case["item"], points=str(item.points_awarded),
            expected_points=case["points"], selected_band=portion.selected_band,
            band_points=str(portion.points_awarded) if case["item"] == "c" else None,
            passed=passed, supported_obligations=list(item.satisfied_obligations),
            refuted_obligations=list(item.unsatisfied_obligations),
            indeterminate_obligations=list(item.indeterminate_obligations),
            credit_evidence_refs=list(item.credit_evidence_refs)))
    summary = dict(mode="local_lean_and_deterministic" if args.with_lean else "deterministic_only",
        cases=len(rows), passed=sum(r["passed"] for r in rows),
        coverage=dict(supported=sorted(coverage), missing=sorted(set(TME2_P1_OBLIGATIONS.values()) - coverage)),
        formal_checks=formal, results=rows)
    (args.output / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(f"{summary['passed']}/{len(rows)} cases; {len(coverage)}/21 obligations; {len(formal)} local Lean checks")
    return 0 if summary["passed"] == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
