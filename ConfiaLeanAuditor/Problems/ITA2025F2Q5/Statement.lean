import Mathlib

namespace ConfIA.LeanAuditor.ITA2025F2Q5

noncomputable section

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

end

end ConfIA.LeanAuditor.ITA2025F2Q5
