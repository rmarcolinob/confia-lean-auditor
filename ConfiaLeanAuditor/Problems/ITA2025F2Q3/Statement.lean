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

end

end ConfIA.LeanAuditor.ITA2025F2Q3
