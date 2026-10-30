"""Criterion-specific mathematical representations for the ten current rubrics.

These rules validate source content; they do not create ExtractedClaims or new
rubric requirements. Required formal microclaims remain owned by rubric assets.
"""
from confia_lean_auditor.rubric.positive_evidence import Rule, MathematicalPattern, require as R, equation as E, fragment as F, math_pattern as M, math_end


def either(*patterns):
    result = "(?:" + "|".join(patterns) + ")"
    if any(isinstance(p, MathematicalPattern) for p in patterns):
        result = MathematicalPattern(result)
        # Only alternatives made entirely of declared equations can use the
        # generic equivalence fallback. Never bypass a prose/compound condition.
        if all(getattr(p, 'equations', ()) for p in patterns):
            result.equations = tuple(e for p in patterns for e in p.equations)
    return result


RULES = {
    ("ITA2025Q1", "z_squared_coordinates"): Rule((
        R("coordinates of z squared", either(E("z^2", "(a^2-4,4a)"), E("z^2", "a^2-4+4ai"))),)),
    ("ITA2025Q1", "area_formula"): Rule((
        R("area expression", r"area\s*(?:=|e)\s*" + M("a^2-2a+5") + math_end()),
        R("determinant expansion actually written", either(E("(a-1)4a-2(a^2-5)","2a^2-4a+10"),
          E("(a-1)*(4*a)-2*(a^2-5)","2*a^2-4*a+10"))))),
    ("ITA2025Q1", "area_equation"): Rule((
        R("equation for prescribed area", either(E("a^2-2a+5","200"), E("a^2-2a-195","0"), E("(a-15)(a+13)","0"))),)),
    ("ITA2025Q1", "positive_root_selection"): Rule((
        R("positive domain and rejected negative root", either(F("a>0"),r"a\s+(?:e\s+)?positivo"), r"descart\w*", r"-\s*13\b"),),
        allowed_negations=(r"descart\w*",)),
    ("ITA2025Q1", "final_answer"): Rule((R("assigned final value",either(E("a","15"),r"valor\s+de\s+a\s+e\s*15"+math_end())),), binding=(("a",15),)),

    ("ITA2025Q3", "first_factor_exponent_form"): Rule((
        R("exponent of first factor", F("(x+1/x)^6"), r"expoente", F("6-2i")),)),
    ("ITA2025Q3", "second_factor_exponent_form"): Rule((
        R("exponent of second factor", F("(x-2/x)^5"), r"expoente", F("5-2j")),)),
    ("ITA2025Q3", "exponent_balance"): Rule((
        R("zero exponent condition", E("11-2i-2j","0"), r"(?:termo\s+independente|expoente\s+(?:zero|nulo))"),)),
    ("ITA2025Q3", "parity_obstruction"): Rule((
        R("odd exponent excludes zero", F("11-2i-2j"), r"impar", r"(?:nunca\s+(?:pode\s+)?ser\s+zero|nao\s+(?:pode\s+)?ser\s+zero|impossivel|nao\s+e\s+zero)"),),
        allowed_negations=(r"nunca\s+(?:pode\s+)?ser\s+zero",r"nao\s+(?:pode\s+)?ser\s+zero",r"nao\s+e\s+zero",
                           r"nao\s+ha\s+termo\s+independente\s+nao\s+nulo")),
    ("ITA2025Q3", "final_answer_zero"): Rule((
        R("constant term concluded zero", r"termo\s+independente\s*(?:e|=|vale)\s*0" + math_end()),),
        allowed_negations=(r"nao\s+ha\s+termo\s+independente\s+nao\s+nulo",)),

    ("ITA2025Q4", "positive_witnesses"): Rule((
        R("positive witness assignments", E("x1","1/8"), E("x2","3/8")),)),
    ("ITA2025Q4", "same_f_argument"): Rule((
        R("equal arguments", either(E("2x1^2-x1+1","2x2^2-x2+1"), E("2*x1^2-x1+1","2*x2^2-x2+1"),
            "(?s:(?=" + E("2(1/8)^2-1/8+1","29/32") + ").*" + E("2(3/8)^2-3/8+1","29/32") + ")")),)),
    ("ITA2025Q4", "distinct_g_inputs"): Rule((
        R("distinct square inputs", E("x1^2","1/64"), E("x2^2","9/64"), r"(?:distintos|diferentes|!=)"),)),
    ("ITA2025Q4", "equal_g_values"): Rule((
        R("applied equality of function values", E("g(x1^2)","g(x2^2)")),),
        allowed_negations=(r"pela\s+hipotese\s+funcional",)),
    ("ITA2025Q4", "not_injective_conclusion"): Rule((
        R("noninjectivity conclusion", r"\bg\s+nao\s+e\s+injet(?:ora|iva)\b"),),
        allowed_negations=(r"\bg\s+nao\s+e\s+injet(?:ora|iva)\b",), conclusion_only=True),

    ("ITA2025Q5", "difference_relation"): Rule((
        R("difference of consecutive sums", E("an","bn+1-bn")),)),
    ("ITA2025Q5", "geometric_form"): Rule((
        R("geometric sequence representation", E("bn","cq^n")),)),
    ("ITA2025Q5", "geometric_factorization"): Rule((
        R("geometric factorization chain", either(E("an","c(q-1)q^n"), E("cq^(n+1)-cq^n","c(q-1)q^n")), M("cq^(n+1)-cq^n")),)),
    ("ITA2025Q5", "conclusion_pg"): Rule((
        R("conclusion about a, not b", r"(?:\(\s*an\s*\)|\ban\b)\s+(?:tambem\s+)?(?:e\s+(?:uma\s+)?(?:pg|progressao\s+geometrica)|tem\s+a\s+forma\s+de\s+uma\s+progressao\s+geometrica)"),),
        allowed_negations=(r"se\s+\(?\s*bn\s*\)?\s+e\s+(?:uma\s+)?(?:pg|progressao\s+geometrica),?\s*entao",), conclusion_only=True),

    ("ITA2025Q8", "numerator_factorization"): Rule((
        R("factorization attached to numerator", either(E("2sin(2x)+2sin(x)-2cos(x)-1","(2cos(x)+1)(2sin(x)-1)"),
          r"numerador\s*(?:e|=|fatora\w*\s+(?:como|em)|pode\s+ser\s+fatorado\s+como)\s*" + M("(2cos(x)+1)(2sin(x)-1)") + math_end())),)),
    ("ITA2025Q8", "denominator_condition"): Rule((
        R("denominator exclusion", r"denominador", either(
            r"positivo[\s\S]*" + either(F("cos(x)!=0"),r"exceto.*"+M("cos(x)=0")),
            r"denominador\s*(?:e|=)\s*"+M("8(cos(2x)+1)")+r"[\s\S]*excluir\s+os\s+pontos\s+em\s+que\s*"+M("cos(x)=0")+math_end())),),
        allowed_negations=(r"nao\s+esta\s+definido\s+quando\s*"+M("cos(x)=0"),r"nao\s+nulo")),
    ("ITA2025Q8", "sign_analysis"): Rule((
        R("complete stated sign intervals", r"intervalos\s+de\s+definicao(?:\s+relevantes)?\s*(?:sao|:)\s*:?\s*" +
          r"\s*,\s*".join(M(i) for i in ("[-pi,-2pi/3]","[pi/6,pi/2)","(pi/2,2pi/3]","[5pi/6,4pi/3]")) + r"\s*(?:\.|$)"),)),
    ("ITA2025Q8", "longest_interval"): Rule((
        R("chosen longest interval", r"(?:maior\s+(?:comprimento|intervalo)|intervalo.*maior|intervalo\s*(?:e|=))", M("(5pi/6,4pi/3)")),)),
    ("ITA2025Q8", "endpoint_sum"): Rule((R("sum of endpoints", E("a+b","13pi/6")),)),

    ("ITA2025F2Q1", "power_reductions"): Rule((
        R("power 57 reduction", E("x^57","-1")), R("power 14 reduction", E("x^14","x-1")), R("power 7 reduction", E("x^7","x")))),
    ("ITA2025F2Q1", "reduced_polynomial_form"): Rule((
        R("identified remainder", r"resto", F("(a+b)x-a")),), formal_types=("f2q1_student_reduced_form",)),
    ("ITA2025F2Q1", "coefficient_system"): Rule((
        R("coefficient equations", either(E("a+b","2"), E("b+a","2")), E("-a","1")),), formal_types=("f2q1_student_coefficient_system",)),
    ("ITA2025F2Q1", "final_answer"): Rule((R("local a,b conclusion", E("a","-1"), E("b","3")),),
        formal_types=("f2q1_student_final_answer",), binding=(("a",-1),("b",3))),

    ("ITA2025F2Q3", "beta_difference"): Rule((R("beta difference", E("cos(beta)-sin(beta)","1/2")),), formal_types=("f2q3_student_beta_difference",)),
    ("ITA2025F2Q3", "candidate_values"): Rule((
        R("sin beta candidate", either(E("sin(beta)","-(1+sqrt(7))/4"), E("sin(beta)","-(sqrt(7)+1)/4"))), R("cos beta candidate", E("cos(beta)","(1-sqrt(7))/4")),
        R("sin alpha candidate", E("sin(alpha)","-sqrt(7)/4")), R("cos alpha candidate", E("cos(alpha)","-3/4")))),
    ("ITA2025F2Q3", "sin_sum_identity"): Rule((
        R("sine addition identity", either(E("sin(alpha+beta)","sin(alpha)cos(beta)+cos(alpha)sin(beta)"), E("sin(alpha+beta)","sin(alpha)cos(beta)+sin(beta)cos(alpha)"))),)),
    ("ITA2025F2Q3", "final_sin_sum"): Rule((
        R("addition identity", M("sin(alpha)cos(beta)+cos(alpha)sin(beta)")),
        R("computed sum", E("sin(alpha+beta)","(5+sqrt(7))/8")))),
    ("ITA2025F2Q3", "final_answer"): Rule((R("final sine value", either(E("sin(alpha+beta)","(5+sqrt(7))/8"),
        E("resposta","(5+sqrt(7))/8"))),), formal_types=("f2q3_student_final_answer",)),

    ("ITA2025F2Q5", "log_power_decomposition"): Rule((
        R("logarithm result", either(E("log10(3^100)","47,7100"),E("log10(3^100)","47.7100"))),), formal_types=("f2q5_student_log_power_decomposition",)),
    ("ITA2025F2Q5", "mantissa_identification"): Rule((
        R("mantissa associated with power", either(r"(?:mantissa|parte\s+fracionaria)\s*(?:e|=|vale)?\s*0[,.]7100\b", E("3^100","10^47*10^0,7100"), E("3^100","10^47*10^0.7100"))),)),
    ("ITA2025F2Q5", "digit_log_bounds"): Rule((
        R("log five", either(E("log10(5)","0,6990"),E("log10(5)","0.6990"))),
        R("log six", either(E("log10(6)","0,7781"),E("log10(6)","0.7781"))))),
    ("ITA2025F2Q5", "mantissa_between_bounds"): Rule((
        R("ordered mantissa bounds", either(F("0,6990<0,7100<0,7781"), F("0.6990<0.7100<0.7781"))),), formal_types=("f2q5_student_between_bounds",)),
    # No new digit extraction: this validator runs only for an already detected claim.
    ("ITA2025F2Q5", "final_digit_five"): Rule((
        R("conclusion about leading digit", r"(?:primeiro\s+algarismo|algarismo\s+inicial)(?:\s+(?:de|do)\s*3\s*\^\s*100)?\s*(?:e|=|vale)\s*5" + math_end()),), formal_types=("f2q5_student_final_digit",)),

    ("ITA2025F2Q6", "probability_formula"): Rule((
        R("probability expression", either(E("P(N=n)","C(n-1,3)/2^n"), E("P(n)","C(n-1,3)/2^n"))),), formal_types=("f2q6_student_probability_formula",)),
    ("ITA2025F2Q6", "ratio_comparison"): Rule((
        R("ratio attached to consecutive probabilities", either(E("P(N=n+1)/P(N=n)","n/(2n-6)"), E("P(n+1)/P(n)","n/(2n-6)"), r"razao\s*(?:e|=)?\s*"+M("n/(2n-6)")+math_end())),
        R("analysis of the ratio", either(
            r"cresce\s+ate\s*n\s*=\s*6[\s\S]*(?:p\s*\(\s*n\s*=\s*7\s*\)\s*=\s*p\s*\(\s*n\s*=\s*6\s*\)|empata|empate)[\s\S]*decresce",
            r"maior\s+que\s*1\s+para\s*n\s*<\s*6[\s\S]*igual\s+a\s*1\s+em\s*n\s*=\s*6[\s\S]*menor\s+que\s*1\s+para\s*n\s*>\s*6")))),
    ("ITA2025F2Q6", "maximizers_identification"): Rule((
        R("increasing then equal then decreasing", r"cresce\s+ate\s*n\s*=\s*6", either(E("P(N=7)","P(N=6)"),r"empate|empata"),r"(?:depois\s+)?decresce"),)),
    ("ITA2025F2Q6", "final_answer"): Rule((
        R("maximizers conclusion", either(
            r"valores\s+de\s+n\s+sao\s*6\s+e\s*7"+math_end(),
            r"(?:logo|portanto|conclu\w*|resposta|maximiz\w*)[\s\S]*"+M("n=6")+r"\s+e\s*"+M("n=7")+math_end())),), formal_types=("f2q6_student_final_answer",)),

    ("ITA2025F2Q8", "matrix_transformation"): Rule((
        R("actual column difference operation", r"coluna", M("C_j-C_{j-1}"), r"(?:substitu\w*|diferenca|operac\w*)"),),
        allowed_negations=(r"nao\s+alteram\s+o\s+determinante",)),
    ("ITA2025F2Q8", "determinant_formula"): Rule((
        R("determinant formula", either(E("det(A_k)","(-1)^(k-1)k"), E("det(A_k)","(-1)^(k-1)*k"))),), formal_types=("f2q8_student_det_formula",)),
    ("ITA2025F2Q8", "alternating_sum"): Rule((
        R("specified alternating sum", r"soma", F("1-2+3-4+...+2025")),)),
    ("ITA2025F2Q8", "final_answer"): Rule((
        R("computed or concluded value", either(E("-1012+2025","1013"), r"(?:resposta|resultado|soma|valor\s+final)\s*(?:e|=|vale|:)\s*1013" + math_end())),), formal_types=("f2q8_student_final_answer",)),
}
