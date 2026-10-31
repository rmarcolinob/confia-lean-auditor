"""Lossless operation view of the existing bounded expression grammar.

Canonicalization intentionally folds arithmetic. Checkers that distinguish a
written construction from its value can inspect this syntax, without a new CAS.
"""
import ast

from .parser import Budget, _tokens, parse_math


def expression_syntax(text):
    parsed = parse_math(text)
    if parsed.status != "parsed" or parsed.canonical_form.kind != "expression":
        return None
    try:
        return ast.parse("".join(_tokens(text, Budget())), mode="eval").body
    except (ValueError, SyntaxError, RecursionError):
        return None


def syntax_text(node):
    return ast.unparse(node)
