import ConfiaLeanAuditor.Problems.ITA2025F2Q1.Statement

namespace ConfiaStudentClaimCheck.ITA2025F2Q1

open ConfIA.LeanAuditor.ITA2025F2Q1

/-- Proposição vinculada ao trecho de origem: [0:138] Como x³ − 1 = (x − 1)(x² − x + 1), tenho x³ ≡ 1 e x⁶ ≡ 1 módulo o divisor, então reduzo os expoentes de 6 em 6: x⁵⁷ ≡ 1, x¹⁴ ≡ x², x⁷ ≡ x. -/
theorem student_claim_check_1 :
    powRem 7 = (0, 1) := by
  norm_num [powRem]

end ConfiaStudentClaimCheck.ITA2025F2Q1
