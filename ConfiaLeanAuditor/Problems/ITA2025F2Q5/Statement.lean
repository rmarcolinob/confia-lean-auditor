import Mathlib

namespace ConfIA.LeanAuditor.ITA2025F2Q5

noncomputable section

/-
  ITA 2025 - 2ª fase - Q5.

  Núcleo formal:
  1. aritmética inteira escalada das aproximações logarítmicas fornecidas;
  2. comparação da mantissa 7100 com os limites 6990 e 7781;
  3. certificado exato independente:
       5 * 10^47 ≤ 3^100 < 6 * 10^47.

  Observação:
  isto não formaliza a função analítica log10 na Mathlib.
  Formaliza a aritmética escalada usada na solução e verifica exatamente
  o intervalo decimal que garante o primeiro algarismo 5.
-/

def scale : ℤ := 10000

def log2Scaled : ℤ := 3010
def log3Scaled : ℤ := 4771

def totalLogScaled : ℤ := 100 * log3Scaled
def integerPartScaled : ℤ := 47 * scale
def mantissaScaled : ℤ := 7100

def log5Scaled : ℤ := scale - log2Scaled
def log6Scaled : ℤ := log2Scaled + log3Scaled

def LogPowerDecompositionClaim : Prop :=
  totalLogScaled = integerPartScaled + mantissaScaled

def DigitLogBoundsClaim : Prop :=
  log5Scaled = 6990 ∧ log6Scaled = 7781

def MantissaBetweenBoundsClaim : Prop :=
  log5Scaled < mantissaScaled ∧ mantissaScaled < log6Scaled

def FinalDigitFiveClaim : Prop :=
  DigitLogBoundsClaim ∧ MantissaBetweenBoundsClaim

/- Valor exato de 3^100. -/
def exactPower : ℕ := 3 ^ 100

/- Escala decimal correspondente ao intervalo [5·10^47, 6·10^47). -/
def exactScalePower : ℕ := 10 ^ 47

/-
  Certificado exato do primeiro algarismo:
  3^100 está entre 5·10^47 e 6·10^47.
-/
def ExactLeadingDigitIntervalClaim : Prop :=
  (5 : ℕ) * exactScalePower ≤ exactPower ∧
    exactPower < (6 : ℕ) * exactScalePower

/-
  Agrupa a parte logarítmica escalada usada na solução oficial.
-/
def ScaledLogArithmeticClaim : Prop :=
  LogPowerDecompositionClaim ∧
    DigitLogBoundsClaim ∧
    MantissaBetweenBoundsClaim ∧
    FinalDigitFiveClaim

/-
  Certificado forte da F2Q5:
  combina a aritmética escalada da solução por logs com a verificação exata
  do intervalo decimal de 3^100.
-/
def StrongF2Q5Claim : Prop :=
  ScaledLogArithmeticClaim ∧ ExactLeadingDigitIntervalClaim


theorem log_power_decomposition_claim : LogPowerDecompositionClaim := by
  unfold LogPowerDecompositionClaim totalLogScaled integerPartScaled mantissaScaled log3Scaled scale
  norm_num


theorem digit_log_bounds_claim : DigitLogBoundsClaim := by
  unfold DigitLogBoundsClaim log5Scaled log6Scaled log2Scaled log3Scaled scale
  norm_num


theorem mantissa_between_bounds_claim : MantissaBetweenBoundsClaim := by
  unfold MantissaBetweenBoundsClaim log5Scaled log6Scaled mantissaScaled log2Scaled log3Scaled scale
  norm_num


theorem final_digit_five_claim : FinalDigitFiveClaim := by
  unfold FinalDigitFiveClaim
  exact ⟨digit_log_bounds_claim, mantissa_between_bounds_claim⟩


theorem scaled_log_arithmetic_claim : ScaledLogArithmeticClaim := by
  unfold ScaledLogArithmeticClaim
  exact
    ⟨ log_power_decomposition_claim,
      digit_log_bounds_claim,
      mantissa_between_bounds_claim,
      final_digit_five_claim ⟩


theorem exact_leading_digit_interval_claim : ExactLeadingDigitIntervalClaim := by
  unfold ExactLeadingDigitIntervalClaim exactPower exactScalePower
  norm_num


theorem strong_f2q5_claim : StrongF2Q5Claim := by
  unfold StrongF2Q5Claim
  exact ⟨scaled_log_arithmetic_claim, exact_leading_digit_interval_claim⟩

end

end ConfIA.LeanAuditor.ITA2025F2Q5
