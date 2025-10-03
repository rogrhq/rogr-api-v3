from __future__ import annotations
from typing import List, Tuple

# NOTE: This module performs *syntax-only* conformance for search queries.
# It does not modify tokens chosen by the planner; it only removes double-quote
# characters that force exact-phrase matching in public search APIs.

_DQUOTE_CHARS = {
    '\u201C', '\u201D', '\u201E', '\u201F',  # curly/smart quotes
    '\u2033', '\u2036',                      # double prime variants
    '\u275D', '\u275E',                      # heavy double quotes
    '\u301D', '\u301E', '\u301F',          # corner quotes
    '\uFF02',                                 # fullwidth double quote
    '"',                                      # ASCII double quote
}

def _normalize_double_quotes(s: str) -> str:
    table = {ord(ch): '"' for ch in _DQUOTE_CHARS if ch != '"'}
    return s.translate(table)


def _strip_all_double_quotes(s: str) -> str:
    return s.replace('"', '')


def quote_conform_variants(original: str) -> List[Tuple[str, str]]:
    """
    Return a single (q_original, q_conformed) pair where q_conformed is the
    same text as the planner produced but with all double-quote characters
    removed. Whitespace is normalized to a single space. If input is empty,
    return [].
    """
    if not isinstance(original, str):
        return []
    orig = original.strip()
    if not orig:
        return []
    norm = _normalize_double_quotes(orig)
    conformed = _strip_all_double_quotes(norm)
    conformed = " ".join(conformed.split())
    return [(orig, conformed)]
