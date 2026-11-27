"""Bounded closed arithmetic with literal factorials, retaining written operations."""
import ast
import math
import re

from . import parse_math
from .rational import rational_value


FACTORIAL=re.compile(r'(?<![\d.])(\d+)\s*!')


def factorial_form(text):
    if len(text)>2048 or not re.fullmatch(r'[\d\s!+*/^().=\-]+',text):return None
    numbers=[int(m[1]) for m in FACTORIAL.finditer(text)]
    if any(n>12 for n in numbers):return None
    expanded=FACTORIAL.sub(lambda m:str(math.factorial(int(m[1]))),text)
    parts=expanded.split('=')
    forms=[parse_math(p) for p in parts]
    if not 1<=len(parts)<=4 or any(p.status!='parsed' or p.canonical_form.kind!='expression' or p.canonical_form.variables for p in forms):return None
    original_parts=text.split('=')
    trees=[]
    for p in original_parts:
        try:
            tree=ast.parse(FACTORIAL.sub(lambda m:'factorial('+m[1]+')',p.strip()).replace('^','**'),mode='eval').body
            if len(list(ast.walk(tree)))>256:return None
            trees.append(tree)
        except (ValueError,SyntaxError,RecursionError):return None
    return {'expanded_parts':parts,'forms':[p.canonical_form.to_dict() for p in forms],
            'factorials':numbers,'original_parts':original_parts}


def lean_combinatorial_expression(text):
    form=factorial_form(text)
    if not form or len(form['original_parts'])!=1:return None
    root=ast.parse(FACTORIAL.sub(lambda m:'factorial('+m[1]+')',text.strip()).replace('^','**'),mode='eval').body
    def render(n):
        if isinstance(n,ast.Constant) and type(n.value) is int:return f'({n.value} : ℤ)'
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='factorial' and len(n.args)==1 and isinstance(n.args[0],ast.Constant):
            return f'((Nat.factorial {n.args[0].value} : ℕ) : ℤ)'
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)):
            return f'(-{render(n.operand)})' if isinstance(n.op,ast.USub) else render(n.operand)
        if isinstance(n,ast.BinOp):
            if isinstance(n.op,ast.Pow) and isinstance(n.right,ast.Constant) and type(n.right.value) is int and 0<=n.right.value<=12:
                return f'({render(n.left)} ^ {n.right.value})'
            operators={ast.Add:'+',ast.Sub:'-',ast.Mult:'*'}
            if type(n.op) in operators:return f'({render(n.left)} {operators[type(n.op)]} {render(n.right)})'
        raise ValueError('Unsupported formal combinatorial expression')
    try:return render(root)
    except (ValueError,TypeError,RecursionError):return None


def two_count_factors(text):
    """A written product of distribution and orientation counts, in either order."""
    form=factorial_form(text)
    if not form or len(form['original_parts'])!=1:return False
    tree=ast.parse(FACTORIAL.sub(lambda m:str(math.factorial(int(m[1]))),text.strip()).replace('^','**'),mode='eval').body
    if not isinstance(tree,ast.BinOp) or not isinstance(tree.op,ast.Mult):return False
    values=[rational_value(ast.unparse(n)) for n in (tree.left,tree.right)]
    return None not in values and sorted(values)==[16,24]
