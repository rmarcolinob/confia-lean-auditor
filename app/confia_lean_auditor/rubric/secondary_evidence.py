"""Presentation-only quote matching; always return text from the original source."""
import unicodedata


def _presentation(text):
    chars, spans = [], []
    for index, char in enumerate(text):
        for unit in unicodedata.normalize('NFD', char):
            if unit.isspace():
                if chars and chars[-1] == ' ':
                    spans[-1] = (spans[-1][0], index + 1)
                    continue
                unit = ' '
            chars.append(unit)
            spans.append((index, index + 1))
    return ''.join(chars), spans


def source_quote(quote, source):
    """No punctuation, case, operators, numbers, negation or LaTeX rewriting.

    Canonically equivalent Unicode and whitespace runs may differ. One balanced
    outer quotation pair may be presentation. The recovered original span must
    round-trip, including complete combining characters; never use fuzzy search.
    """
    if quote in source:
        return quote
    trimmed = quote.strip()
    candidates = [trimmed]
    if len(trimmed) >= 2 and (trimmed[0], trimmed[-1]) in {
            ('"', '"'), ("'", "'"), ('“', '”'), ('‘', '’'), ('«', '»')}:
        candidates.append(trimmed[1:-1].strip())
    normalized, spans = _presentation(source)
    for candidate in candidates:
        needle = _presentation(candidate)[0]
        if not needle.strip():
            continue
        start = normalized.find(needle)
        while start >= 0:
            end = start + len(needle)
            original = source[spans[start][0]:spans[end - 1][1]]
            if _presentation(original)[0] == needle:
                return original
            start = normalized.find(needle, start + 1)
    return None


def resolve_evidence(evidence, source, redact):
    if not isinstance(evidence, list):
        return None, 'not_array'
    if not 1 <= len(evidence) <= 3:
        return None, 'empty_array' if not evidence else 'too_many_quotes'
    resolved = []
    for quote in evidence:
        if not isinstance(quote, str) or not quote.strip():
            return None, 'empty_or_non_string_quote'
        if len(quote) > 800:
            return None, 'quote_over_800_chars'
        if redact(quote) != quote:
            return None, 'sensitive_content'
        actual = source_quote(quote, source)
        if actual is None:
            return None, 'quote_not_found'
        if len(actual) > 800:
            return None, 'source_span_over_800_chars'
        if redact(actual) != actual:
            return None, 'sensitive_content'
        resolved.append(actual)
    return resolved, None
