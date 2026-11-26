"""Lossless notation view; callers retain the original source and offsets."""
import re

_MATH_DASH = re.compile(r'(?<=[0-9)])\s*–\s*(?=[0-9(])|(?<=[=+(*/])\s*–\s*(?=[0-9])|^–(?=[0-9])')


def mathematical_dash_at(text, offset):
    return text[offset:offset + 1] == '–' and any(m.start() <= offset < m.end() for m in _MATH_DASH.finditer(text))


def mathematical_signs(text):
    text = text.replace('−', '-')
    # En dash is mathematical only beside explicit numeric/operator syntax.
    # Do not reinterpret prose such as "prova – tentativa" or "x – y".
    return _MATH_DASH.sub('-', text)
