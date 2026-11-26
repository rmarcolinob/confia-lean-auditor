"""Bounded opt-in positive multisets and factored integer products.

A list and a product are different types. Powers remain factor multiplicities;
no large integer expansion, eval(), general CAS, or global parser limit change.
"""
import ast
from collections import Counter
from .parser import Budget, _tokens
from .rational import rational_value


def bounded_syntax(text):
    if len(text) > 2048:
        return None
    try:
        node = ast.parse(''.join(_tokens(text, Budget())), mode='eval').body
        return node if len(list(ast.walk(node))) <= 256 else None
    except (ValueError, SyntaxError, RecursionError):
        return None


def positive_multiset(text):
    """Tuple/list, additive list, or {value: multiplicity}; never a power-list."""
    if len(text) > 2048 or '#' in text:
        return None
    try:
        root = ast.parse(text.strip(), mode='eval').body
    except (ValueError, SyntaxError, RecursionError):
        return None
    if len(list(ast.walk(root))) > 512:
        return None
    def integer(node):
        return node.value if isinstance(node, ast.Constant) and type(node.value) is int and 1 <= node.value <= 100000 else None
    def terms(node):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return terms(node.left)+terms(node.right)
        return [node]
    counts = Counter()
    if isinstance(root, ast.Dict):
        if not 1 <= len(root.keys) <= 16:
            return None
        for k, v in zip(root.keys, root.values):
            key, value = integer(k), integer(v)
            if key is None or value is None or key in counts:
                return None
            counts[key] = value
    else:
        nodes = root.elts if isinstance(root, (ast.Tuple, ast.List)) else terms(root)
        if not 1 <= len(nodes) <= 128:
            return None
        for node in nodes:
            value = integer(node)
            if value is None:
                return None
            counts[value] += 1
    if sum(k*v for k,v in counts.items()) > 1000000:
        return None
    return {str(k):v for k,v in sorted(counts.items())}


def partition_table(text):
    """An explicit finite enumeration of lists, not a claimed maximum alone."""
    if len(text)>2048 or '#' in text:
        return None
    try:
        root=ast.parse(text.strip(),mode='eval').body
        if not isinstance(root, (ast.List,ast.Tuple)) or not 1<=len(root.elts)<=128:
            return None
        values=[positive_multiset(ast.unparse(n)) for n in root.elts]
        return values if all(values) else None
    except (ValueError,SyntaxError,RecursionError):
        return None


def prime_factors(number):
    if type(number) is not int or not 1<=number<=100000:
        return None
    result=Counter(); d=2
    while d*d<=number:
        while number%d==0:
            result[str(d)]+=1; number//=d
        d+=1
    if number>1: result[str(number)]+=1
    return result


def product_form(text):
    """Canonical prime/exponent map, e.g. 4*3^674 == 12*3^673."""
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            result=prime_factors(node.value)
            if result is not None:return result
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            return visit(node.left)+visit(node.right)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            exponent=rational_value(ast.unparse(node.right))
            if exponent is not None and exponent.denominator==1 and 0<=exponent<=10000:
                return Counter({k:v*int(exponent) for k,v in visit(node.left).items() if v*exponent})
        raise ValueError('Unsupported factored product')
    try:
        result=visit(bounded_syntax(text))
        if sum(result.values())>100000: return None
        return dict(sorted(result.items(),key=lambda pair:int(pair[0])))
    except (ValueError,TypeError,RecursionError):
        return None


def multiset_product(counts):
    result=Counter()
    for k,v in counts.items():
        result.update({p:e*v for p,e in prime_factors(int(k)).items()})
    return dict(sorted(result.items(),key=lambda pair:int(pair[0])))


def written_factors(text):
    """Written factors, before prime factorization; 4 is not two written twos."""
    def visit(node):
        if isinstance(node,ast.Constant) and type(node.value) is int and 1<=node.value<=100000:
            return Counter({str(node.value):1})
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Mult):return visit(node.left)+visit(node.right)
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Pow):
            exponent=rational_value(ast.unparse(node.right))
            if exponent is not None and exponent.denominator==1 and 1<=exponent<=10000:
                return Counter({k:v*int(exponent) for k,v in visit(node.left).items()})
        raise ValueError('Unsupported written factor list')
    try:return dict(visit(bounded_syntax(text)))
    except (ValueError,TypeError,RecursionError):return None
