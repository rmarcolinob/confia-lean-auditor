import Mathlib

namespace ConfIA.LeanAuditor.ITA2025F2Q3

noncomputable section

open Real

/-
ITA 2025, 2ª fase, Q3.

Versão formal inicial:
- formaliza a parte algébrica da solução;
- verifica os valores candidatos para sen α, cos α, sen β, cos β;
- verifica o valor final de sen(α+β).

A parte trigonométrica dos intervalos [π/2, 3π/2], usada para escolher os sinais,
fica explicitamente como argumento matemático externo nesta primeira versão.
-/

def sqrt7 : ℝ := Real.sqrt 7

def sinBetaCandidate : ℝ := - (sqrt7 + 1) / 4
def cosBetaCandidate : ℝ := (1 - sqrt7) / 4
def sinAlphaCandidate : ℝ := - sqrt7 / 4
def cosAlphaCandidate : ℝ := -3 / 4

def FirstEquationClaim : Prop :=
  sinAlphaCandidate - sinBetaCandidate = 1 / 4

def SecondEquationClaim : Prop :=
  sinAlphaCandidate - 2 * sinBetaCandidate + cosBetaCandidate = 3 / 4

def BetaDifferenceClaim : Prop :=
  cosBetaCandidate - sinBetaCandidate = 1 / 2

def CandidateUnitCircleClaim : Prop :=
  sinAlphaCandidate ^ 2 + cosAlphaCandidate ^ 2 = 1 ∧
  sinBetaCandidate ^ 2 + cosBetaCandidate ^ 2 = 1

def FinalSinSumClaim : Prop :=
  sinAlphaCandidate * cosBetaCandidate +
    cosAlphaCandidate * sinBetaCandidate =
      (5 + sqrt7) / 8

def FinalAnswerClaim : Prop :=
  FinalSinSumClaim

theorem sqrt7_sq : sqrt7 ^ 2 = 7 := by
  unfold sqrt7
  rw [Real.sq_sqrt]
  norm_num

theorem first_equation_claim : FirstEquationClaim := by
  unfold FirstEquationClaim sinAlphaCandidate sinBetaCandidate sqrt7
  ring

theorem beta_difference_claim : BetaDifferenceClaim := by
  unfold BetaDifferenceClaim sinBetaCandidate cosBetaCandidate sqrt7
  ring

theorem second_equation_claim : SecondEquationClaim := by
  unfold SecondEquationClaim sinAlphaCandidate sinBetaCandidate cosBetaCandidate sqrt7
  ring

theorem candidate_unit_circle_claim : CandidateUnitCircleClaim := by
  unfold CandidateUnitCircleClaim sinAlphaCandidate cosAlphaCandidate
    sinBetaCandidate cosBetaCandidate
  constructor
  · ring_nf
    rw [sqrt7_sq]
    ring
  · ring_nf
    rw [sqrt7_sq]
    ring

theorem final_sin_sum_claim : FinalSinSumClaim := by
  unfold FinalSinSumClaim sinAlphaCandidate cosBetaCandidate
    cosAlphaCandidate sinBetaCandidate
  ring_nf
  rw [sqrt7_sq]
  ring

theorem final_answer_claim : FinalAnswerClaim := by
  unfold FinalAnswerClaim
  exact final_sin_sum_claim


/-
  Núcleo forte adicional.

  A formalização abaixo não modela diretamente alpha e beta como ângulos
  nem prova, a partir de alpha,beta ∈ [π/2,3π/2], que os cossenos são
  não positivos.

  Em vez disso, formaliza a etapa algébrica forte:
  - os candidatos principais satisfazem as equações e o círculo unitário;
  - o ramo alternativo para beta também satisfaz a equação beta, mas tem
    cos beta positivo;
  - o ramo alternativo para cos alpha tem cos alpha positivo;
  - as restrições de sinal cos alpha ≤ 0 e cos beta ≤ 0 selecionam
    os candidatos usados na resposta.
-/

def sinBetaAlternative : ℝ := (sqrt7 - 1) / 4
def cosBetaAlternative : ℝ := (sqrt7 + 1) / 4
def cosAlphaAlternative : ℝ := 3 / 4

def CandidateIntervalSignClaim : Prop :=
  cosAlphaCandidate ≤ 0 ∧ cosBetaCandidate ≤ 0

def BetaAlternativeEquationsClaim : Prop :=
  cosBetaAlternative - sinBetaAlternative = 1 / 2 ∧
    sinBetaAlternative ^ 2 + cosBetaAlternative ^ 2 = 1

def BetaSignSelectionClaim : Prop :=
  cosBetaCandidate ≤ 0 ∧ 0 < cosBetaAlternative

def AlphaSignSelectionClaim : Prop :=
  cosAlphaCandidate ≤ 0 ∧ 0 < cosAlphaAlternative

def StrongF2Q3Claim : Prop :=
  FirstEquationClaim ∧
    SecondEquationClaim ∧
    BetaDifferenceClaim ∧
    CandidateUnitCircleClaim ∧
    CandidateIntervalSignClaim ∧
    BetaAlternativeEquationsClaim ∧
    BetaSignSelectionClaim ∧
    AlphaSignSelectionClaim ∧
    FinalSinSumClaim ∧
    FinalAnswerClaim

theorem sqrt7_nonneg : 0 ≤ sqrt7 := by
  unfold sqrt7
  exact Real.sqrt_nonneg 7

theorem one_lt_sqrt7 : (1 : ℝ) < sqrt7 := by
  by_contra h
  have hle : sqrt7 ≤ 1 := le_of_not_gt h
  have hnonneg : 0 ≤ sqrt7 := sqrt7_nonneg
  nlinarith [sqrt7_sq]

theorem candidate_interval_sign_claim : CandidateIntervalSignClaim := by
  unfold CandidateIntervalSignClaim cosAlphaCandidate cosBetaCandidate
  constructor
  · norm_num
  · have h : (1 : ℝ) < sqrt7 := one_lt_sqrt7
    nlinarith

theorem beta_alternative_equations_claim : BetaAlternativeEquationsClaim := by
  unfold BetaAlternativeEquationsClaim sinBetaAlternative cosBetaAlternative
  constructor
  · ring
  · ring_nf
    rw [sqrt7_sq]
    ring

theorem beta_sign_selection_claim : BetaSignSelectionClaim := by
  unfold BetaSignSelectionClaim cosBetaCandidate cosBetaAlternative
  constructor
  · have h : (1 : ℝ) < sqrt7 := one_lt_sqrt7
    nlinarith
  · have h : (1 : ℝ) < sqrt7 := one_lt_sqrt7
    nlinarith

theorem alpha_sign_selection_claim : AlphaSignSelectionClaim := by
  unfold AlphaSignSelectionClaim cosAlphaCandidate cosAlphaAlternative
  norm_num

theorem strong_f2q3_claim : StrongF2Q3Claim := by
  unfold StrongF2Q3Claim
  exact
    ⟨ first_equation_claim,
      second_equation_claim,
      beta_difference_claim,
      candidate_unit_circle_claim,
      candidate_interval_sign_claim,
      beta_alternative_equations_claim,
      beta_sign_selection_claim,
      alpha_sign_selection_claim,
      final_sin_sum_claim,
      final_answer_claim ⟩

end

end ConfIA.LeanAuditor.ITA2025F2Q3
