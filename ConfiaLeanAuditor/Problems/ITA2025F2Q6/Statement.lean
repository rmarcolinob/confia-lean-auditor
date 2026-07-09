import Mathlib

namespace ConfIA.LeanAuditor.ITA2025F2Q6

noncomputable section

def waysBeforeFourthHead (n : ℤ) : ℤ :=
  ((n - 1) * (n - 2) * (n - 3)) / 6

def denom (n : ℕ) : ℕ :=
  2 ^ n

def ratioNumer (n : ℤ) : ℤ :=
  n

def ratioDenom (n : ℤ) : ℤ :=
  2 * n - 6

def candidateN1 : ℕ := 6
def candidateN2 : ℕ := 7

def ProbabilityValuesClaim : Prop :=
  waysBeforeFourthHead 6 = 10 ∧
  denom 6 = 64 ∧
  waysBeforeFourthHead 7 = 20 ∧
  denom 7 = 128 ∧
  10 * 128 = 20 * 64

def RatioComparisonClaim : Prop :=
  (∀ n : ℤ, 4 ≤ n → n < 6 → ratioDenom n < ratioNumer n) ∧
  ratioNumer 6 = ratioDenom 6 ∧
  (∀ n : ℤ, 6 < n → ratioNumer n < ratioDenom n)

def CandidateMaximizersClaim : Prop :=
  candidateN1 = 6 ∧ candidateN2 = 7

def FinalAnswerClaim : Prop :=
  CandidateMaximizersClaim

end

end ConfIA.LeanAuditor.ITA2025F2Q6
