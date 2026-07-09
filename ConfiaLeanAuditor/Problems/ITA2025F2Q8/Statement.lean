import Mathlib

set_option linter.unusedSimpArgs false
set_option linter.style.emptyLine false
set_option linter.style.nativeDecide false

namespace ConfIA.LeanAuditor.ITA2025F2Q8

noncomputable section

def detFormula (k : ℕ) : ℤ :=
  (-1 : ℤ) ^ (k - 1) * (k : ℤ)

def transformedShape (k : ℕ) : Matrix (Fin k) (Fin k) ℤ :=
  fun i j =>
    if (j : ℕ) = 0 then
      ((i : ℕ) + 1 : ℤ)
    else if (i : ℕ) < (j : ℕ) then
      1
    else
      0

def upperOnes (n : ℕ) : Matrix (Fin n) (Fin n) ℤ :=
  fun i j =>
    if (i : ℕ) ≤ (j : ℕ) then 1 else 0

theorem upperOnes_blockTriangular (n : ℕ) :
    (upperOnes n).BlockTriangular id := by
  intro i j hji
  unfold upperOnes
  have hnot : ¬ ((i : ℕ) ≤ (j : ℕ)) := by
    intro hij
    exact (not_le_of_gt (by exact_mod_cast hji)) hij
  simp [hnot]

theorem det_upperOnes (n : ℕ) :
    Matrix.det (upperOnes n) = 1 := by
  rw [Matrix.det_of_upperTriangular (upperOnes_blockTriangular n)]
  apply Finset.prod_eq_one
  intro i hi
  simp [upperOnes]

/-
Este menor é exatamente o menor que aparece em Matrix.det_succ_row
quando expandimos transformedShape (n+1) pela última linha e pela coluna 0.

Remover última linha: Fin.castSucc
Remover primeira coluna: Fin.succ
-/
def transformedMinor (n : ℕ) : Matrix (Fin n) (Fin n) ℤ :=
  (transformedShape (n + 1)).submatrix
    (Fin.last n).succAbove
    (0 : Fin (n + 1)).succAbove

theorem transformedMinor_eq_upperOnes (n : ℕ) :
    transformedMinor n = upperOnes n := by
  ext i j
  unfold transformedMinor transformedShape upperOnes
  by_cases hle : (i : ℕ) ≤ (j : ℕ)
  · have hleFin : i ≤ j := by
      exact_mod_cast hle
    have hlt : ((Fin.last n).succAbove i : ℕ) <
        (((0 : Fin (n + 1)).succAbove j : ℕ)) := by
      simp
      omega
    have hcol : (((0 : Fin (n + 1)).succAbove j : ℕ)) ≠ 0 := by
      simp
    simp [hle, hleFin, hlt, hcol]
  · have hjiNat : (j : ℕ) < (i : ℕ) := by
      exact Nat.lt_of_not_ge hle
    have hjiFin : j < i := by
      exact_mod_cast hjiNat
    have hnlt : ¬ (((Fin.last n).succAbove i : ℕ) <
        (((0 : Fin (n + 1)).succAbove j : ℕ))) := by
      simp
      omega
    have hcol : (((0 : Fin (n + 1)).succAbove j : ℕ)) ≠ 0 := by
      simp
    simp [hle, hjiNat, hjiFin, hnlt, hcol]

theorem det_transformedMinor (n : ℕ) :
    Matrix.det (transformedMinor n) = 1 := by
  rw [transformedMinor_eq_upperOnes n]
  exact det_upperOnes n

theorem transformedShape_last_row_zero
    (n : ℕ) (j : Fin (n + 1)) (hj : j ≠ 0) :
    transformedShape (n + 1) (Fin.last n) j = 0 := by
  unfold transformedShape
  have hcol : (j : ℕ) ≠ 0 := by
    intro h
    apply hj
    ext
    simpa using h
  have hle : (j : ℕ) ≤ n := by
    exact Nat.le_of_lt_succ j.isLt
  have hlast : ((Fin.last n : Fin (n + 1)) : ℕ) = n := by
    simp
  have hnotlt : ¬ (((Fin.last n : Fin (n + 1)) : ℕ) < (j : ℕ)) := by
    rw [hlast]
    exact not_lt_of_ge hle
  simp [hcol, hlast, hle, hnotlt]


theorem det_transformedShape_succ (n : ℕ) :
    Matrix.det (transformedShape (n + 1)) =
      (-1 : ℤ) ^ n * ((n + 1 : ℕ) : ℤ) := by
  rw [Matrix.det_succ_row (transformedShape (n + 1)) (Fin.last n)]
  rw [Finset.sum_eq_single (0 : Fin (n + 1))]
  · have hminor :
        Matrix.det
          ((transformedShape (n + 1)).submatrix
            (Fin.last n).succAbove
            ((0 : Fin (n + 1)).succAbove)) = 1 := by
      change Matrix.det (transformedMinor n) = 1
      exact det_transformedMinor n
    rw [hminor]
    simp [transformedShape]
  · intro j hjmem hjne
    have hentry :
        transformedShape (n + 1) (Fin.last n) j = 0 :=
      transformedShape_last_row_zero n j hjne
    simp [hentry]
  · intro hnot
    simp at hnot

theorem det_transformedShape_formula (k : ℕ) (hk : 1 ≤ k) :
    Matrix.det (transformedShape k) = detFormula k := by
  obtain ⟨n, rfl⟩ := Nat.exists_eq_succ_of_ne_zero (Nat.ne_of_gt hk)
  simpa [detFormula] using det_transformedShape_succ n

theorem det_transformedShape_2025 :
    Matrix.det (transformedShape 2025) = detFormula 2025 := by
  exact det_transformedShape_formula 2025 (by norm_num)



/-! 
Ponte para a matriz original A_k.

maxMatrix k é a matriz A_k com entrada max(i+1,j+1).
colDiffMatrix k realiza diferenças sucessivas de colunas.
-/

def maxMatrix (k : ℕ) : Matrix (Fin k) (Fin k) ℤ :=
  fun i j => max ((i : ℕ) + 1) ((j : ℕ) + 1)

def colDiffMatrix (k : ℕ) : Matrix (Fin k) (Fin k) ℤ :=
  fun i j =>
    if (i : ℕ) = (j : ℕ) then 1
    else if (i : ℕ) + 1 = (j : ℕ) then -1
    else 0

theorem colDiffMatrix_blockTriangular (k : ℕ) :
    (colDiffMatrix k).BlockTriangular id := by
  intro i j hji
  unfold colDiffMatrix
  have hjiNat : (j : ℕ) < (i : ℕ) := by
    exact_mod_cast hji
  have hneDiag : ¬ ((i : ℕ) = (j : ℕ)) := by
    omega
  have hneSuper : ¬ ((i : ℕ) + 1 = (j : ℕ)) := by
    omega
  simp [hneDiag, hneSuper]

theorem det_colDiffMatrix_eq_one (k : ℕ) :
    Matrix.det (colDiffMatrix k) = 1 := by
  rw [Matrix.det_of_upperTriangular (colDiffMatrix_blockTriangular k)]
  apply Finset.prod_eq_one
  intro i hi
  simp [colDiffMatrix]

theorem pred_castSucc_val
    (n : ℕ) (j : Fin (n + 1)) (hj : j ≠ 0) :
    ((Fin.castSucc (Fin.pred j hj) : Fin (n + 1)) : ℕ) + 1 = (j : ℕ) := by
  have hnez : (j : ℕ) ≠ 0 := by
    intro h
    apply hj
    ext
    exact h
  have hpos : 0 < (j : ℕ) := Nat.pos_of_ne_zero hnez
  simp [Fin.pred]
  omega

theorem pred_castSucc_ne_self
    (n : ℕ) (j : Fin (n + 1)) (hj : j ≠ 0) :
    Fin.castSucc (Fin.pred j hj) ≠ j := by
  intro h
  have hval :
      ((Fin.castSucc (Fin.pred j hj) : Fin (n + 1)) : ℕ) = (j : ℕ) := by
    exact congrArg Fin.val h
  have hpred :
      ((Fin.castSucc (Fin.pred j hj) : Fin (n + 1)) : ℕ) + 1 = (j : ℕ) :=
    pred_castSucc_val n j hj
  omega

theorem max_diff_bridge (a b : ℕ) :
    ((max (a + 1) (b + 1) : ℕ) : ℤ) - ((max (a + 1) b : ℕ) : ℤ) =
      if a < b then 1 else 0 := by
  by_cases h : a < b
  · have h1 : max (a + 1) (b + 1) = b + 1 := by
      apply max_eq_right
      omega
    have h2 : max (a + 1) b = b := by
      apply max_eq_right
      omega
    simp [h, h1, h2]
  · have h1 : max (a + 1) (b + 1) = a + 1 := by
      apply max_eq_left
      omega
    have h2 : max (a + 1) b = a + 1 := by
      apply max_eq_left
      omega
    simp [h, h1, h2]

theorem bridge_col_zero (n : ℕ) (i : Fin (n + 1)) :
    (maxMatrix (n + 1) * colDiffMatrix (n + 1)) i 0 =
      transformedShape (n + 1) i 0 := by
  simp [Matrix.mul_apply, maxMatrix, colDiffMatrix, transformedShape]

theorem bridge_col_nonzero_sum
    (n : ℕ) (i j : Fin (n + 1)) (hj : j ≠ 0) :
    (maxMatrix (n + 1) * colDiffMatrix (n + 1)) i j =
      ((max ((i : ℕ) + 1) ((j : ℕ) + 1) : ℕ) : ℤ) -
      ((max ((i : ℕ) + 1) (j : ℕ) : ℕ) : ℤ) := by
  let p : Fin (n + 1) := Fin.castSucc (Fin.pred j hj)
  let A : ℤ := ((max ((i : ℕ) + 1) ((j : ℕ) + 1) : ℕ) : ℤ)
  let B : ℤ := -((max ((i : ℕ) + 1) (j : ℕ) : ℕ) : ℤ)

  have hpval : (p : ℕ) + 1 = (j : ℕ) := by
    dsimp [p]
    exact pred_castSucc_val n j hj

  have hpne : p ≠ j := by
    dsimp [p]
    exact pred_castSucc_ne_self n j hj

  have hterm :
      ∀ x : Fin (n + 1),
        maxMatrix (n + 1) i x * colDiffMatrix (n + 1) x j =
          (if x = j then A else 0) + (if x = p then B else 0) := by
    intro x
    by_cases hxj : x = j
    · subst x
      have hnotjp : ¬ j = p := by
        intro h
        exact hpne h.symm
      simp [maxMatrix, colDiffMatrix, A, B, hnotjp]
    · by_cases hxp : x = p
      · subst x
        have hpneNat : ¬ ((p : ℕ) = (j : ℕ)) := by
          intro h
          apply hpne
          ext
          exact h

        have hpvalInt : (((p : ℕ) : ℤ) + 1) = ((j : ℕ) : ℤ) := by
          exact_mod_cast hpval

        have hcalc :
            (-1 : ℤ) + -max (((i : ℕ) : ℤ)) (((p : ℕ) : ℤ)) =
              -max (((i : ℕ) : ℤ) + 1) (((j : ℕ) : ℤ)) := by
          rw [← hpvalInt]
          by_cases hip : (i : ℕ) ≤ (p : ℕ)
          · have hipInt : ((i : ℕ) : ℤ) ≤ ((p : ℕ) : ℤ) := by
              exact_mod_cast hip
            have hipSuccInt :
                ((i : ℕ) : ℤ) + 1 ≤ ((p : ℕ) : ℤ) + 1 := by
              omega
            rw [max_eq_right hipInt, max_eq_right hipSuccInt]
            ring
          · have hpi : (p : ℕ) ≤ (i : ℕ) := by
              exact Nat.le_of_not_ge hip
            have hpiInt : ((p : ℕ) : ℤ) ≤ ((i : ℕ) : ℤ) := by
              exact_mod_cast hpi
            have hpiSuccInt :
                ((p : ℕ) : ℤ) + 1 ≤ ((i : ℕ) : ℤ) + 1 := by
              omega
            rw [max_eq_left hpiInt, max_eq_left hpiSuccInt]
            ring

        simpa [maxMatrix, colDiffMatrix, A, B, hpval, hpne, hpneNat] using hcalc
      · have hxneNat : ¬ ((x : ℕ) = (j : ℕ)) := by
          intro h
          apply hxj
          ext
          exact h
        have hxnePredNat : ¬ ((x : ℕ) + 1 = (j : ℕ)) := by
          intro h
          apply hxp
          ext
          omega
        simp [maxMatrix, colDiffMatrix, A, B, hxj, hxp, hxneNat, hxnePredNat]

  rw [Matrix.mul_apply]
  calc
    (∑ x, maxMatrix (n + 1) i x * colDiffMatrix (n + 1) x j)
        = ∑ x, ((if x = j then A else 0) + (if x = p then B else 0)) := by
          apply Finset.sum_congr rfl
          intro x hx
          exact hterm x
    _ = (∑ x, if x = j then A else 0) + (∑ x, if x = p then B else 0) := by
          rw [Finset.sum_add_distrib]
    _ = A + B := by
          simp [hpne]
    _ = ((max ((i : ℕ) + 1) ((j : ℕ) + 1) : ℕ) : ℤ) -
        ((max ((i : ℕ) + 1) (j : ℕ) : ℕ) : ℤ) := by
          simp [A, B, sub_eq_add_neg]

theorem bridge_col_nonzero
    (n : ℕ) (i j : Fin (n + 1)) (hj : j ≠ 0) :
    (maxMatrix (n + 1) * colDiffMatrix (n + 1)) i j =
      transformedShape (n + 1) i j := by
  have hjnat : (j : ℕ) ≠ 0 := by
    intro h
    apply hj
    ext
    exact h
  rw [bridge_col_nonzero_sum n i j hj]
  rw [max_diff_bridge]
  simp [transformedShape, hjnat]

theorem bridge_generic (n : ℕ) :
    maxMatrix (n + 1) * colDiffMatrix (n + 1) =
      transformedShape (n + 1) := by
  ext i j
  by_cases hj : j = 0
  · subst j
    exact bridge_col_zero n i
  · exact bridge_col_nonzero n i j hj

/-
Teorema forte: determinante da matriz original A_k.
-/
theorem det_maxMatrix_formula (k : ℕ) (hk : 1 ≤ k) :
    Matrix.det (maxMatrix k) = detFormula k := by
  obtain ⟨n, rfl⟩ := Nat.exists_eq_succ_of_ne_zero (Nat.ne_of_gt hk)

  have hprod :
      Matrix.det (maxMatrix (n + 1)) * Matrix.det (colDiffMatrix (n + 1)) =
        Matrix.det (transformedShape (n + 1)) := by
    rw [← Matrix.det_mul, bridge_generic n]

  have hcol :
      Matrix.det (colDiffMatrix (n + 1)) = 1 :=
    det_colDiffMatrix_eq_one (n + 1)

  have htrans :
      Matrix.det (transformedShape (n + 1)) = detFormula (n + 1) :=
    det_transformedShape_formula (n + 1) (by omega)

  calc
    Matrix.det (maxMatrix (n + 1))
        = Matrix.det (maxMatrix (n + 1)) * 1 := by
            simp
    _ = Matrix.det (maxMatrix (n + 1)) *
          Matrix.det (colDiffMatrix (n + 1)) := by
            rw [hcol]
    _ = Matrix.det (transformedShape (n + 1)) := hprod
    _ = detFormula (n + 1) := htrans

def determinantFormulaClaim : Prop :=
  ∀ k : ℕ, 1 ≤ k → Matrix.det (maxMatrix k) = detFormula k

theorem determinant_formula_claim : determinantFormulaClaim := by
  intro k hk
  exact det_maxMatrix_formula k hk

def alternatingDetSum (n : ℕ) : ℤ :=
  (Finset.Icc 1 n).sum fun k => detFormula k

def finalAnswerClaim : Prop :=
  alternatingDetSum 2025 = 1013

theorem final_answer_claim : finalAnswerClaim := by
  unfold finalAnswerClaim alternatingDetSum detFormula
  native_decide

def strongF2Q8Claim : Prop :=
  determinantFormulaClaim ∧ finalAnswerClaim

theorem strong_f2q8_claim : strongF2Q8Claim := by
  exact ⟨determinant_formula_claim, final_answer_claim⟩

end

end ConfIA.LeanAuditor.ITA2025F2Q8
