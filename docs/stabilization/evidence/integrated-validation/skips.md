# Skips e xfail preservados

- 1 × **skipped**, `tests.test_claim_fidelity`: Original smoke artifact is local; the portable source fixture is tested separately
- 1 × **skipped**, `tests.test_common_math_claims`: Local historical artifact
- 1 × **xfailed**, `tests.test_f2q6_strong_certificate`: P2 preexistente: maximizers_identification ausente nesta formulação; subtotal 8/8, sem nota global
- 1 × **skipped**, `tests.test_generic_student_math`: Local replay artifacts; portable cases above cover the syntax
- 1 × **skipped**, `tests.test_math_canonical`: Local historical artifact
- 1 × **skipped**, `tests.test_positive_credit_evidence`: Historical smoke artifact is local
- 1 × **skipped**, `tests.test_rubric_bridge`: Local V2 artifact; equivalent portable regression is tested above
- 1 × **skipped**, `tests.test_scope_boundary`: Frozen DEV artifact unavailable; never load another dataset
- 4 × **skipped**, `tests.test_scope_boundary_replay`: Frozen DEV outputs unavailable; never substitute another split
- 1 × **skipped**, `tests.test_score_policy`: Local synthetic corpus fixture unavailable
- 21 × **skipped**, `tests.test_sufficiency_dev_regressions`: Actual independent gate shadow has not run yet
- 12 × **skipped**, `tests.test_tme_model_ablation`: Frozen local DEV pack unavailable; never replace with another dataset
- 2 × **skipped**, `tests.test_tme_model_compat`: Frozen local DEV pack unavailable
- 5 × **skipped**, `tests.test_tme_review_diagnostics`: Local pilot audit unavailable; portable P1 and synthetic regressions still run
