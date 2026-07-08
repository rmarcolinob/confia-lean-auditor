import Mathlib

namespace ConfIA.LeanAuditor.ITA2025Q8

open Real

noncomputable section

def numerator (x : ℝ) : ℝ :=
  2 * sin (2 * x) + 2 * sin x - 2 * cos x - 1

def factoredNumerator (x : ℝ) : ℝ :=
  (2 * cos x + 1) * (2 * sin x - 1)

def CandidateA : ℝ :=
  5 * Real.pi / 6

def CandidateB : ℝ :=
  4 * Real.pi / 3

def NumeratorFactorizationClaim : Prop :=
  ∀ x : ℝ, numerator x = factoredNumerator x

def EndpointSumClaim : Prop :=
  CandidateA + CandidateB = 13 * Real.pi / 6

def CandidateLengthClaim : Prop :=
  CandidateB - CandidateA = Real.pi / 2

end

end ConfIA.LeanAuditor.ITA2025Q8
