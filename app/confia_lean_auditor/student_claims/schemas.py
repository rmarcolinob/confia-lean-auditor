from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


StudentClaimType = Literal[
    "f2q8_student_final_answer",
    "arithmetic_equality",
    "f2q8_student_det_formula",
    "f2q8_student_alternating_sum_value",
    "f2q8_student_pair_count",
    "f2q8_student_pair_reduction",
    "f2q1_student_final_answer",
    "f2q1_student_power_reduction",
    "f2q1_student_reduced_form",
    "f2q1_student_coefficient_system",
    "f2q5_student_log_power_decomposition",
    "f2q5_student_mantissa",
    "f2q5_student_digit_log_bounds",
    "f2q5_student_between_bounds",
    "f2q5_student_final_digit",
    "f2q3_student_beta_difference",
    "f2q3_student_candidate_value",
    "f2q3_student_final_sin_sum",
    "f2q3_student_final_answer",
]


StudentClaimStatus = Literal[
    "verified",
    "failed",
    "unsupported",
    "error",
]


@dataclass
class StudentClaim:
    id: str
    problem_id: str
    claim_type: StudentClaimType
    raw_text: str
    normalized_text: str
    context: str
    data: dict[str, Any] = field(default_factory=dict)
    method: str = "norm_num"
    confidence: float = 0.85


@dataclass
class StudentClaimCheck:
    id: str
    problem_id: str
    claim_type: StudentClaimType
    raw_text: str
    normalized_text: str
    lean_statement: str
    method: str
    status: StudentClaimStatus
    compiled: bool
    lean_file: str | None
    stdout: str
    stderr: str
    data: dict[str, Any] = field(default_factory=dict)
