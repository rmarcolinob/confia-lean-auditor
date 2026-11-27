"""Strict mathematical fragments, never document prose or executable Python.

AST is used only as a parser. There is no eval, sympify or arbitrary function
dispatch. Algebra is the existing exact affine collector; nonlinear syntax is
retained without polynomial expansion or cancellation of variable factors.
"""
import ast
from fractions import Fraction
import re
import time
import unicodedata

from confia_lean_auditor.core.audit_math_projection import _affine, _add, _braced
from .models import CanonicalMath, MathNode, ParseResult

MAX_LENGTH = 2048
MAX_NODES = 256
MAX_DEPTH = 32
MAX_TERMS = 128
MAX_BITS = 512
MAX_EXPONENT = 128
MAX_SECONDS = 0.05
GREEK = dict(zip('αβγδεζηθικλμνξοπρστυφχψω',
    'alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega'.split()))
GREEK_NAMES = set(GREEK.values())
ALIASES = {'sen':'sin', 'seno':'sin', 'tg':'tan'}
FUNCTIONS = {'sin', 'cos', 'tan', 'log10'}
TOKEN = re.compile(r'\d+(?:\.\d+)?|[A-Za-z_][A-Za-z_0-9]*|<=|>=|!=|\*\*|//|[+*/^()=<>.,\[\]-]')


class Failure(ValueError):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason


class Budget:
    def __init__(self):
        self.deadline = time.monotonic() + MAX_SECONDS
        self.nodes = 0

    def tick(self, depth=0):
        self.nodes += 1
        if self.nodes > MAX_NODES or depth > MAX_DEPTH:
            raise Failure('unsupported', 'AST complexity limit')
        if time.monotonic() > self.deadline:
            raise Failure('unsupported', 'Canonicalization time budget')

    def rational(self, value):
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_BITS:
            raise Failure('unsupported', 'Exact coefficient size limit')
        return value


def _latex(text, budget, depth=0):
    budget.tick(depth)
    out, i = [], 0
    while i < len(text):
        if text[i] != '\\':
            out.append(text[i]); i += 1; continue
        match = re.match(r'\\([A-Za-z]+)', text[i:])
        if not match:
            raise Failure('unsupported', 'Unsupported LaTeX escape')
        command = match[1]; end = i + len(match[0])
        if command == 'frac':
            a = _braced(text, end)
            b = _braced(text, a[1]) if a else None
            if not a or not b:
                raise Failure('invalid', 'Fraction requires two braced operands')
            out.append('((' + _latex(a[0], budget, depth+1) + ')/(' + _latex(b[0], budget, depth+1) + '))')
            i = b[1]; continue
        commands = {**{v:v for v in GREEK_NAMES}, 'sin':'sin', 'sen':'sin', 'cos':'cos',
                    'tan':'tan', 'tg':'tan', 'cdot':'*', 'times':'*', 'le':'<=', 'leq':'<=',
                    'ge':'>=', 'geq':'>=', 'left':'', 'right':''}
        if command == 'log':
            base = re.match(r'_\s*(?:\{10\}|10)', text[end:])
            if not base:
                raise Failure('unsupported', 'Logarithm requires explicit base 10')
            out.append(' log10 '); i = end + len(base[0]); continue
        if command not in commands:
            raise Failure('unsupported', 'Unknown LaTeX command: ' + command)
        out.append(' ' + commands[command] + ' '); i = end
    return ''.join(out)


def _tokens(text, budget):
    if not isinstance(text, str) or not text.strip():
        raise Failure('invalid', 'Empty mathematical fragment')
    if len(text) > MAX_LENGTH:
        raise Failure('unsupported', 'Input length limit')
    from .normalization import mathematical_signs
    text = mathematical_signs(text.strip())
    if text.startswith('$') and text.endswith('$') and text.count('$') == 2:
        text = text[1:-1]
    elif text.startswith(r'\(') and text.endswith(r'\)'):
        text = text[2:-2]
    if ';' in text or text.count('=') > 1 and not any(op in text for op in ('<=','>=')):
        raise Failure('ambiguous', 'Multiple mathematical statements')
    text = _latex(text, budget)
    text = re.sub(r'[⁰¹²³⁴⁵⁶⁷⁸⁹]+', lambda m: '**' + unicodedata.normalize('NFKC', m[0]), text)
    text = ''.join(GREEK.get(c, {'−':'-', '·':'*', '×':'*', '≤':'<=', '≥':'>='}.get(c,c)) for c in text)
    # Braces are grouping, after strict LaTeX command handling.
    text = text.replace('{','(').replace('}',')')
    if re.search(r'\d[eE][+-]?\d', text):
        raise Failure('unsupported', 'Scientific notation requires an explicit supported spelling')
    tokens, pos = [], 0
    nesting = 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1; continue
        match = TOKEN.match(text,pos)
        if not match:
            raise Failure('unsupported', 'Unsupported mathematical character')
        token = ALIASES.get(match[0], match[0])
        if token == 'log_10': token = 'log10'
        if token in {'(', '['}: nesting += 1
        if token in {')', ']'}: nesting -= 1
        if nesting > MAX_DEPTH:
            raise Failure('unsupported', 'Grouping depth limit')
        if nesting < 0:
            raise Failure('invalid', 'Unbalanced mathematical grouping')
        if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', token) and token not in FUNCTIONS and not _variable(token):
            raise Failure('unsupported', 'Unknown identifier or prose token: ' + token)
        if re.fullmatch(r'\d+(?:\.\d+)?', token):
            if len(token) > 64:
                raise Failure('unsupported', 'Numeric literal size limit')
            fraction = budget.rational(Fraction(token))
            token = str(fraction.numerator) if fraction.denominator == 1 else f'({fraction.numerator}/{fraction.denominator})'
        tokens.append(token); pos = match.end()
        if len(tokens) > MAX_NODES:
            raise Failure('unsupported', 'Token limit')
    if nesting:
        raise Failure('invalid', 'Unbalanced mathematical grouping')
    # Bare trig arguments are single identifiers only. No guessing sin 2x.
    result, i = [], 0
    while i < len(tokens):
        token = tokens[i]
        if token in FUNCTIONS and i+1 < len(tokens) and re.fullmatch(r'[A-Za-z][A-Za-z_0-9]*', tokens[i+1]):
            if tokens[i+1] in FUNCTIONS:
                raise Failure('ambiguous', 'Parentheses required for nested functions')
            if i+2 < len(tokens) and tokens[i+2] in {'^','**','*','/','('}:
                raise Failure('ambiguous', 'Parentheses required around the function argument')
            result.extend([token,'(',tokens[i+1],')']); i += 2; continue
        result.append('**' if token == '^' else token); i += 1
    expanded = []
    for index, token in enumerate(result):
        if expanded:
            prev = result[index-1]
            # Only number-symbol/number-group and adjacent parenthesized groups.
            if (re.fullmatch(r'\d+|\(\d+/\d+\)',prev) and (re.fullmatch(r'[A-Za-z][A-Za-z_0-9]*',token) or token=='(')) or prev==')' and (token=='(' or _variable(token) or token in FUNCTIONS):
                if index>=2 and result[index-2]=='/':
                    raise Failure('ambiguous','Implicit multiplication after a divisor requires parentheses')
                expanded.append('*')
        expanded.append(token)
    return expanded


def _variable(name):
    return name in GREEK_NAMES or bool(re.fullmatch(r'[A-Za-z](?:_?\d+)?', name))


def _node(node, budget, depth=0):
    budget.tick(depth)
    if isinstance(node, ast.Constant) and type(node.value) is int:
        value = budget.rational(Fraction(node.value))
        return MathNode('rational', str(value)), ast.Constant(value.numerator)
    if isinstance(node, ast.Name):
        if not _variable(node.id):
            raise Failure('unsupported', 'Unknown identifier or prose token: ' + node.id)
        return MathNode('constant' if node.id=='pi' else 'variable', node.id), node
    if isinstance(node, ast.Call):
        if not isinstance(node.func,ast.Name) or node.func.id not in FUNCTIONS or len(node.args)!=1 or node.keywords:
            raise Failure('unsupported', 'Function outside the explicit whitelist')
        if node.func.id=='tan':
            raise Failure('unsupported', 'Tangent requires a domain excluding its poles')
        arg, parsed = _node(node.args[0],budget,depth+1)
        if node.func.id=='log10' and (arg.kind!='rational' or Fraction(arg.value)<=0):
            raise Failure('unsupported', 'Log10 supports positive rational arguments only')
        return MathNode('function',node.func.id,(arg,)), ast.Call(func=node.func,args=[parsed],keywords=[])
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
        arg, parsed = _node(node.operand,budget,depth+1)
        if isinstance(node.op,ast.UAdd): return arg,parsed
        if arg.kind=='rational': return _fraction_node(-Fraction(arg.value),budget)
        return MathNode('negative',args=(arg,)),ast.UnaryOp(op=ast.USub(),operand=parsed)
    if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow)):
        left,l = _node(node.left,budget,depth+1); right,r = _node(node.right,budget,depth+1)
        a = Fraction(left.value) if left.kind=='rational' else None
        b = Fraction(right.value) if right.kind=='rational' else None
        if isinstance(node.op,ast.Div) and (b is None or b==0):
            raise Failure('invalid' if b==0 else 'unsupported','Division requires a nonzero rational denominator')
        if isinstance(node.op,ast.Pow):
            if b is None or b.denominator!=1:
                raise Failure('unsupported','Exponent must be an explicit integer')
            exponent=int(b)
            if abs(exponent)>MAX_EXPONENT:
                raise Failure('unsupported','Exponent limit')
            if exponent<0 and (a is None or a==0):
                raise Failure('unsupported','Negative powers require a nonzero rational base')
            if a is not None:
                if max(a.numerator.bit_length(),a.denominator.bit_length())*abs(exponent)>MAX_BITS:
                    raise Failure('unsupported','Power coefficient size limit')
                return _fraction_node(a**exponent,budget)
            if exponent==0:return _fraction_node(Fraction(1),budget)
            if exponent==1:return left,l
        if a is not None and b is not None:
            operations={ast.Add:lambda:a+b,ast.Sub:lambda:a-b,ast.Mult:lambda:a*b,ast.Div:lambda:a/b}
            if type(node.op) in operations:return _fraction_node(operations[type(node.op)](),budget)
        kind={ast.Add:'sum',ast.Sub:'difference',ast.Mult:'product',ast.Div:'quotient',ast.Pow:'power'}[type(node.op)]
        return MathNode(kind,args=(left,right)),ast.BinOp(left=l,op=node.op,right=r)
    raise Failure('unsupported','Unsupported AST node')


def _fraction_node(value,budget):
    budget.rational(value)
    node = ast.Constant(value.numerator) if value.denominator==1 else ast.BinOp(left=ast.Constant(value.numerator),op=ast.Div(),right=ast.Constant(value.denominator))
    return MathNode('rational',str(value)),node


def _expression(tokens,budget):
    if not tokens:raise Failure('invalid','Missing operand')
    # Spaces preserve token boundaries: never join prose or identifiers.
    source=' '.join(tokens)
    try: tree=ast.parse(source,mode='eval').body
    except SyntaxError as exc:raise Failure('invalid','Malformed mathematical expression') from exc
    return _node(tree,budget)


def _collect(node,budget):
    try: result=_affine(node,budget)
    except Failure:raise
    except ValueError:return None
    budget.tick()
    if len(result)>MAX_TERMS:raise Failure('unsupported','Affine term limit')
    for coefficient in result.values():budget.rational(coefficient)
    return result


def parse_math(text, *, expected_kind=None):
    """Parse one bounded fragment over real, total expressions. No prose search."""
    budget=Budget()
    try:
        tokens=_tokens(text,budget)
        # Intervals are handled explicitly; comma decimals are never guessed.
        if tokens and tokens[0] in {'[','('} and tokens[-1] in {']',')'} and ',' in tokens:
            if tokens[0]=='(' and tokens[-1]==')' and expected_kind!='interval':
                raise Failure('ambiguous','Open interval or ordered pair; specify interval context')
            if tokens.count(',')!=1:raise Failure('ambiguous','Multiple interval separators')
            index=tokens.index(',')
            left,_=_expression(tokens[1:index],budget);right,_=_expression(tokens[index+1:-1],budget)
            form=CanonicalMath('interval',MathNode('interval',tokens[0]+tokens[-1],(left,right)))
            return ParseResult('parsed','Interval syntax; no set simplification',form)
        relations=[i for i,t in enumerate(tokens) if t in {'=','<','>','<=','>=','!='}]
        if len(relations)>1:raise Failure('ambiguous','Multiple relations require explicit separate claims')
        if ',' in tokens:raise Failure('ambiguous','Comma may be a separator or decimal notation')
        variables=tuple(sorted({t for t in tokens if _variable(t) and t!='pi'}))
        if not relations:
            tree,node=_expression(tokens,budget); affine=_collect(node,budget)
            form=CanonicalMath('expression',tree,None if affine is None else tuple((k,str(v)) for k,v in sorted(affine.items())),variables=variables)
        else:
            index=relations[0];relation=tokens[index]
            if relation=='!=':raise Failure('unsupported','Disequality not in this initial domain')
            left,l=_expression(tokens[:index],budget);right,r=_expression(tokens[index+1:],budget)
            if relation in {'>','>='}:left,right,l,r,relation=right,left,r,l,('<' if relation=='>' else '<=')
            a,b=_collect(l,budget),_collect(r,budget)
            affine=None
            if a is not None and b is not None:
                terms=sorted(_add(a,b,-1).items())
                divisor=terms[0][1] if terms else Fraction(1)
                if relation!='=':divisor=abs(divisor)
                affine=tuple((atom,str(budget.rational(coefficient/divisor))) for atom,coefficient in terms)
            form=CanonicalMath('equality' if relation=='=' else 'inequality',MathNode('relation',relation,(left,right)),affine,relation,variables)
        budget.tick()
        return ParseResult('parsed','Bounded real syntax and exact affine projection',form)
    except Failure as exc:return ParseResult(exc.status,exc.reason)
    except (SyntaxError,ValueError,TypeError,ZeroDivisionError,RecursionError,OverflowError):
        return ParseResult('invalid','Malformed or excessive mathematical expression')
