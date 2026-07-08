import Mathlib

namespace ConfIA.LeanAuditor.ITA2025Q3

noncomputable section

def firstExponent (i : ℤ) : ℤ :=
  6 - 2 * i

def secondExponent (j : ℤ) : ℤ :=
  5 - 2 * j

def productExponent (i j : ℤ) : ℤ :=
  firstExponent i + secondExponent j

def FirstFactorExponentClaim : Prop :=
  ∀ i : ℤ, Even (firstExponent i)

def SecondFactorExponentClaim : Prop :=
  ∀ j : ℤ, Odd (secondExponent j)

def ProductExponentOddClaim : Prop :=
  ∀ i j : ℤ, Odd (productExponent i j)

def NoConstantExponentClaim : Prop :=
  ∀ i j : ℤ, productExponent i j ≠ 0

def FinalAnswerZeroClaim : Prop :=
  NoConstantExponentClaim

end

end ConfIA.LeanAuditor.ITA2025Q3
