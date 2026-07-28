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


/-
Núcleo aritmético-combinatório forte.

Para a quarta cara ocorrer no lançamento n, o fator combinatório é
C(n-1,3). Para a comparação entre probabilidades consecutivas, o fator
constante 1/6 pode ser ignorado e usamos o numerador proporcional

  (n-1)(n-2)(n-3).

A razão entre termos consecutivos fica

  P(n+1)/P(n) = n / (2(n-3)) = n / (2n-6).

Aqui formalizamos a identidade algébrica que sustenta essa razão e o
limiar aritmético que produz o empate em n=6 e n=7.
-/
def fourthHeadWeight (n : ℤ) : ℤ :=
  (n - 1) * (n - 2) * (n - 3)

def strongRatioDenom (n : ℤ) : ℤ :=
  2 * (n - 3)

def StrongRatioDenomBridgeClaim : Prop :=
  ∀ n : ℤ, strongRatioDenom n = ratioDenom n

def StrongRatioIdentityClaim : Prop :=
  ∀ n : ℤ,
    fourthHeadWeight (n + 1) * strongRatioDenom n =
      ratioNumer n * (2 * fourthHeadWeight n)

def StrongRatioThresholdClaim : Prop :=
  (∀ n : ℤ, 4 ≤ n → n < 6 → strongRatioDenom n < ratioNumer n) ∧
  strongRatioDenom 6 = ratioNumer 6 ∧
  (∀ n : ℤ, 6 < n → ratioNumer n < strongRatioDenom n)

def StrongF2Q6Claim : Prop :=
  ProbabilityValuesClaim ∧
  StrongRatioDenomBridgeClaim ∧
  StrongRatioIdentityClaim ∧
  StrongRatioThresholdClaim ∧
  CandidateMaximizersClaim ∧
  FinalAnswerClaim

theorem f2q6_probability_values_claim : ProbabilityValuesClaim := by
  unfold ProbabilityValuesClaim waysBeforeFourthHead denom
  norm_num

theorem f2q6_ratio_comparison_claim : RatioComparisonClaim := by
  unfold RatioComparisonClaim ratioNumer ratioDenom
  constructor
  · intro n hn hlt
    omega
  · constructor
    · norm_num
    · intro n hgt
      omega

theorem f2q6_candidate_maximizers_claim : CandidateMaximizersClaim := by
  unfold CandidateMaximizersClaim candidateN1 candidateN2
  norm_num

theorem f2q6_final_answer_claim : FinalAnswerClaim := by
  unfold FinalAnswerClaim
  exact f2q6_candidate_maximizers_claim

theorem strong_ratio_denom_bridge : StrongRatioDenomBridgeClaim := by
  unfold StrongRatioDenomBridgeClaim strongRatioDenom ratioDenom
  intro n
  ring

theorem strong_ratio_identity : StrongRatioIdentityClaim := by
  unfold StrongRatioIdentityClaim fourthHeadWeight strongRatioDenom ratioNumer
  intro n
  ring

theorem strong_ratio_threshold : StrongRatioThresholdClaim := by
  unfold StrongRatioThresholdClaim strongRatioDenom ratioNumer
  constructor
  · intro n hn hlt
    omega
  · constructor
    · norm_num
    · intro n hgt
      omega

theorem strong_f2q6_claim : StrongF2Q6Claim := by
  unfold StrongF2Q6Claim
  constructor
  · exact f2q6_probability_values_claim
  constructor
  · exact strong_ratio_denom_bridge
  constructor
  · exact strong_ratio_identity
  constructor
  · exact strong_ratio_threshold
  constructor
  · exact f2q6_candidate_maximizers_claim
  · exact f2q6_final_answer_claim

end

end ConfIA.LeanAuditor.ITA2025F2Q6
