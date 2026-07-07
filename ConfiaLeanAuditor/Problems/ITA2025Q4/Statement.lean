import Mathlib

namespace ConfIA.LeanAuditor.ITA2025Q4

noncomputable section

def witnessX1 : ℝ := (1 : ℝ) / 8

def witnessX2 : ℝ := (3 : ℝ) / 8

def phi (x : ℝ) : ℝ :=
  2 * x ^ 2 - x + 1

def FunctionalHypothesis (f g : ℝ → ℝ) : Prop :=
  ∀ x : ℝ, 0 < x → g (x ^ 2) = f (phi x)

def PositiveWitnessesClaim : Prop :=
  0 < witnessX1 ∧ 0 < witnessX2

def SameArgumentWitnessClaim : Prop :=
  phi witnessX1 = phi witnessX2

def DistinctGInputsClaim : Prop :=
  witnessX1 ^ 2 ≠ witnessX2 ^ 2

def EqualGValuesClaim : Prop :=
  ∀ f g : ℝ → ℝ,
    FunctionalHypothesis f g →
    g (witnessX1 ^ 2) = g (witnessX2 ^ 2)

def GNotInjectiveClaim : Prop :=
  ∀ f g : ℝ → ℝ,
    FunctionalHypothesis f g →
    ¬ Function.Injective g

end

end ConfIA.LeanAuditor.ITA2025Q4
