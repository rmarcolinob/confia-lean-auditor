import ConfiaLeanAuditor.Problems.ITA2025F2Q1.Statement

namespace ConfiaStudentClaimCheck.ITA2025F2Q1

open ConfIA.LeanAuditor.ITA2025F2Q1

/-- Proposição vinculada ao trecho de origem: [342:403] Ou seja, a = −1 e b = 3, e o polinômio é x⁵⁷ − x¹⁴ + 3x⁷ + 1. -/
theorem student_claim_check_3 :
    candidateA = (-1 : ℤ) ∧ candidateB = (3 : ℤ) := by
  norm_num [candidateA, candidateB]

end ConfiaStudentClaimCheck.ITA2025F2Q1
