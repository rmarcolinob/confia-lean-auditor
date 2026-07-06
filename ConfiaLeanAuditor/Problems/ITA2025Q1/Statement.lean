import Mathlib

namespace ConfIA.LeanAuditor.ITA2025Q1

noncomputable section

def signedDoubleArea (a : ℝ) : ℝ :=
  (a - 1) * (4 * a) - 2 * ((a ^ 2 - 4) - 1)

def triangleArea (a : ℝ) : ℝ :=
  |signedDoubleArea a| / 2

def ZSquaredCoordinatesClaim : Prop :=
  ∀ a : ℝ,
    (a ^ 2 - 2 ^ 2 = a ^ 2 - 4) ∧
    (2 * a * 2 = 4 * a)

def TriangleAreaFormulaClaim : Prop :=
  ∀ a : ℝ,
    0 < a →
    triangleArea a = a ^ 2 - 2 * a + 5

def AnswerUniqueClaim : Prop :=
  ∀ a : ℝ,
    0 < a →
    triangleArea a = 200 →
    a = 15

def AnswerCheckClaim : Prop :=
  triangleArea 15 = 200

end

end ConfIA.LeanAuditor.ITA2025Q1
