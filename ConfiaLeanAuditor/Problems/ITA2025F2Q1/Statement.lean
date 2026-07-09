import Mathlib

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

end

end ConfIA.LeanAuditor.ITA2025F2Q1
