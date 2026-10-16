"""Syntactic LaTeX projection for textual audit extractors.

The stored transcription and audit source remain byte-for-byte unchanged.
Unknown commands remain visible instead of being guessed or evaluated.
"""

import re


_SIMPLE_COMMANDS = {
    "alpha": "alpha", "beta": "beta", "gamma": "gamma",
    "sin": "sin", "cos": "cos", "sen": "sen",
    "cdot": "*", "times": "*", "quad": " ", "qquad": " ",
    "left": "", "right": "", "displaystyle": "",
}


def _braced(text: str, start: int):
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        return None
    depth = 1
    for index in range(start + 1, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:index], index + 1
    return None


def _operand(value: str) -> str:
    value = value.strip()
    return value if re.fullmatch(r"[+-]?[A-Za-z0-9_.]+(?:\([A-Za-z0-9_.]+\))?", value) else f"({value})"


def project_audit_math(text: str) -> str:
    """Translate common Mathpix syntax without changing values or signs."""
    text = re.sub(r"\\(?:begin|end)\s*\{(?:array|aligned|align|gathered|matrix)\}(?:\s*\{[^{}]*\})?", "", text)
    text = text.replace(r"\(", " ").replace(r"\)", " ").replace(r"\[", "\n").replace(r"\]", "\n")
    text = text.replace(r"\\", "\n")
    output = []
    index = 0
    while index < len(text):
        if text[index] != "\\":
            output.append(text[index])
            index += 1
            continue
        match = re.match(r"\\([A-Za-z]+)", text[index:])
        if not match:
            output.append(text[index])
            index += 1
            continue
        command = match.group(1)
        end = index + len(match.group(0))
        if command in {"operatorname", "mathrm", "text", "frac", "sqrt"}:
            first = _braced(text, end)
            if first:
                value, end = first
                value = project_audit_math(value)
                if command == "frac":
                    second = _braced(text, end)
                    if second:
                        denominator, end = second
                        output.append(f"{_operand(value)}/{_operand(project_audit_math(denominator))}")
                        index = end
                        continue
                elif command == "sqrt":
                    output.append(f"sqrt({value.strip()})")
                    index = end
                    continue
                else:
                    output.append(value)
                    index = end
                    continue
        if command in _SIMPLE_COMMANDS:
            output.append(_SIMPLE_COMMANDS[command])
        else:
            output.append(match.group(0))
        index += len(match.group(0))
    return "".join(output)
