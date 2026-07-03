
import Mathlib

namespace ConfIA.LeanAuditor.Generated.ITA2025Q1

noncomputable section

def signedDoubleArea (a : ℝ) : ℝ :=
  (a - 1) * (4 * a) - 2 * ((a ^ 2 - 4) - 1)

def triangleArea (a : ℝ) : ℝ :=
  |signedDoubleArea a| / 2

theorem signedDoubleArea_formula (a : ℝ) :
    signedDoubleArea a = 2 * (a ^ 2 - 2 * a + 5) := by
  unfold signedDoubleArea
  ring

theorem triangleArea_formula (a : ℝ) :
    triangleArea a = a ^ 2 - 2 * a + 5 := by
  unfold triangleArea
  rw [signedDoubleArea_formula]
  have hnonneg : 0 ≤ 2 * (a ^ 2 - 2 * a + 5) := by
    have hrewrite : a ^ 2 - 2 * a + 5 = (a - 1) ^ 2 + 4 := by
      ring
    have hsq : 0 ≤ (a - 1) ^ 2 := sq_nonneg (a - 1)
    nlinarith
  rw [abs_of_nonneg hnonneg]
  ring


end

end ConfIA.LeanAuditor.Generated.ITA2025Q1
