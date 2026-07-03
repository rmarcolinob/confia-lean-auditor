import Mathlib

namespace ConfIA.LeanAuditor.ITA2025Q1

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

theorem answer_unique
    (a : ℝ)
    (ha : 0 < a)
    (harea : triangleArea a = 200) :
    a = 15 := by
  rw [triangleArea_formula] at harea
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

theorem answer_check :
    triangleArea 15 = 200 := by
  rw [triangleArea_formula]
  norm_num

end

end ConfIA.LeanAuditor.ITA2025Q1
