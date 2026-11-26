import ConfiaLeanAuditor.Problems.ITA2025F2Q1.Statement

namespace ConfiaStudentClaimCheck.ITA2025F2Q1

open ConfIA.LeanAuditor.ITA2025F2Q1

/-- Proposição vinculada ao trecho de origem: [237:341] O resto tem grau menor que 2, então comparo com 2x + 1: a + 2 = 1 dá a = −1, e a + b = 2 dá então b = 3. -/
theorem student_claim_check_2 :
    candidateA + candidateB = (2 : ℤ) ∧ candidateA = (-1 : ℤ) := by
  norm_num [candidateA, candidateB]

end ConfiaStudentClaimCheck.ITA2025F2Q1
