import Mathlib

set_option linter.style.nativeDecide false

namespace ConfIA.LeanAuditor.ITA2025F2Q1

noncomputable section

/-
Representamos o resto linear c + d*x pelo par (c,d).
A tabela abaixo codifica o ciclo de restos de x^n módulo x^2 - x + 1:

n mod 6 = 0:  1
n mod 6 = 1:  x
n mod 6 = 2:  x - 1
n mod 6 = 3: -1
n mod 6 = 4: -x
n mod 6 = 5:  1 - x
-/
def powRem (n : ℕ) : ℤ × ℤ :=
  match n % 6 with
  | 0 => (1, 0)
  | 1 => (0, 1)
  | 2 => (-1, 1)
  | 3 => (-1, 0)
  | 4 => (0, -1)
  | _ => (1, -1)

def candidateA : ℤ := -1
def candidateB : ℤ := 3

def remainderConst (a b : ℤ) : ℤ :=
  (powRem 57).1 + a * (powRem 14).1 + b * (powRem 7).1 + 1

def remainderXCoeff (a b : ℤ) : ℤ :=
  (powRem 57).2 + a * (powRem 14).2 + b * (powRem 7).2

def PowerReductionsClaim : Prop :=
  powRem 57 = (-1, 0) ∧
  powRem 14 = (-1, 1) ∧
  powRem 7 = (0, 1)

def ReducedPolynomialFormClaim : Prop :=
  ∀ a b : ℤ,
    remainderConst a b = -a ∧ remainderXCoeff a b = a + b

def CoefficientSystemSolutionClaim : Prop :=
  candidateA + candidateB = 2 ∧ -candidateA = 1

def TargetRemainderClaim : Prop :=
  remainderXCoeff candidateA candidateB = 2 ∧
  remainderConst candidateA candidateB = 1

def FinalAnswerClaim : Prop :=
  candidateA = -1 ∧ candidateB = 3


/-
Núcleo algébrico forte.

Modelamos restos lineares módulo x^2 - x + 1 como pares (c,d),
representando c + d*x.

A multiplicação abaixo usa a relação x^2 = x - 1:

(c + d*x)(e + f*x)
= ce + (cf + de)x + df*x^2
≡ (ce - df) + (cf + de + df)x.
-/
abbrev LinRem := ℤ × ℤ

def linOne : LinRem := (1, 0)

def linX : LinRem := (0, 1)

def linAdd (u v : LinRem) : LinRem :=
  (u.1 + v.1, u.2 + v.2)

def linScale (a : ℤ) (u : LinRem) : LinRem :=
  (a * u.1, a * u.2)

def linMul (u v : LinRem) : LinRem :=
  (u.1 * v.1 - u.2 * v.2, u.1 * v.2 + u.2 * v.1 + u.2 * v.2)

def linPow : ℕ → LinRem
  | 0 => linOne
  | n + 1 => linMul (linPow n) linX

def strongRemainder (a b : ℤ) : LinRem :=
  linAdd
    (linAdd
      (linAdd (linPow 57) (linScale a (linPow 14)))
      (linScale b (linPow 7)))
    linOne

def StrongF2Q1Claim : Prop :=
  strongRemainder candidateA candidateB = (1, 2)
    ∧ (∀ a b : ℤ, strongRemainder a b = (1, 2) → a = -1 ∧ b = 3)
    ∧ FinalAnswerClaim

theorem linPow_57_claim : linPow 57 = (-1, 0) := by
  native_decide

theorem linPow_14_claim : linPow 14 = (-1, 1) := by
  native_decide

theorem linPow_7_claim : linPow 7 = (0, 1) := by
  native_decide

theorem strong_remainder_formula (a b : ℤ) :
    strongRemainder a b = (-a, a + b) := by
  ext <;>
    simp [
      strongRemainder,
      linAdd,
      linScale,
      linOne,
      linPow_57_claim,
      linPow_14_claim,
      linPow_7_claim
    ] <;>
    ring_nf

theorem strong_candidate_satisfies_target :
    strongRemainder candidateA candidateB = (1, 2) := by
  rw [strong_remainder_formula]
  norm_num [candidateA, candidateB]

theorem strong_unique_solution (a b : ℤ) :
    strongRemainder a b = (1, 2) → a = -1 ∧ b = 3 := by
  intro h
  rw [strong_remainder_formula] at h
  injection h with h_const h_coeff
  constructor
  · linarith
  · linarith

theorem strong_final_answer_claim : FinalAnswerClaim := by
  unfold FinalAnswerClaim candidateA candidateB
  norm_num

theorem strong_f2q1_claim : StrongF2Q1Claim := by
  unfold StrongF2Q1Claim
  constructor
  · exact strong_candidate_satisfies_target
  constructor
  · intro a b h
    exact strong_unique_solution a b h
  · exact strong_final_answer_claim

end

end ConfIA.LeanAuditor.ITA2025F2Q1
