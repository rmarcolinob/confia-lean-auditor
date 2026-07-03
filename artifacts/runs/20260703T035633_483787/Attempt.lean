
import ConfiaLeanAuditor.Problems.ITA2025Q1.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q1

open ConfIA.LeanAuditor.ITA2025Q1

noncomputable section

private theorem triangleArea_formula_helper (a : ℝ) :
    triangleArea a = a ^ 2 - 2 * a + 5 := by
  unfold triangleArea signedDoubleArea
  have hdet :
      (a - 1) * (4 * a) - 2 * ((a ^ 2 - 4) - 1)
        = 2 * (a ^ 2 - 2 * a + 5) := by
    ring
  rw [hdet]
  have hnonneg : 0 ≤ 2 * (a ^ 2 - 2 * a + 5) := by
    have hrewrite : a ^ 2 - 2 * a + 5 = (a - 1) ^ 2 + 4 := by
      ring
    have hsq : 0 ≤ (a - 1) ^ 2 := sq_nonneg (a - 1)
    nlinarith
  rw [abs_of_nonneg hnonneg]
  ring


theorem z_squared_coordinates : ZSquaredCoordinatesClaim := by
  unfold ZSquaredCoordinatesClaim
  intro a
  constructor <;> ring


theorem answer_unique : AnswerUniqueClaim := by
  unfold AnswerUniqueClaim
  intro a ha harea
  rw [triangleArea_formula_helper] at harea
  have hquad : (a - 15) * (a + 13) = 0 := by
    nlinarith
  have hcases := mul_eq_zero.mp hquad
  cases hcases with
  | inl h =>
      nlinarith
  | inr h =>
      have hneg : a = -13 := by
        nlinarith
      nlinarith


theorem answer_check : AnswerCheckClaim := by
  unfold AnswerCheckClaim
  rw [triangleArea_formula_helper]
  norm_num


end

end ConfIA.LeanAuditor.Generated.ITA2025Q1
