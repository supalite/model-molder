"""Split Luau source into code, string and comment spans.

Everything in modernize goes through here. A bare regex rewrite will happily edit
`wait()` inside a string literal or a doc comment, and the result is a training sample
whose code contradicts its own documentation. Nothing downstream catches that.
"""
from __future__ import annotations

import re

_LONG_OPEN = re.compile(r"\[(=*)\[")


def _long_bracket_end(src: str, start: int) -> int | None:
    m = _LONG_OPEN.match(src, start)
    if not m:
        return None
    close = "]" + "=" * len(m.group(1)) + "]"
    end = src.find(close, m.end())
    return len(src) if end == -1 else end + len(close)


def _quoted_end(src: str, start: int) -> int:
    quote = src[start]
    i = start + 1
    while i < len(src):
        c = src[i]
        if c == "\\":
            i += 2
            continue
        if c == quote or c == "\n":  # unterminated string, stop at the newline
            return i + 1
        i += 1
    return len(src)


def spans(src: str) -> list[tuple[int, int, bool]]:
    """Contiguous `(start, end, is_code)` spans covering the whole source.

    Not a parser. It only needs to find where strings and comments begin and end, which
    for Luau means `--` line comments, `--[[ ]]` and `--[=[ ]=]` blocks, quoted strings
    with backslash escapes, and `[[ ]]` / `[=[ ]=]` long strings.
    """
    out: list[tuple[int, int, bool]] = []
    code_start = 0
    i = 0
    n = len(src)

    def flush_code(upto: int) -> None:
        if upto > code_start:
            out.append((code_start, upto, True))

    while i < n:
        c = src[i]
        if c == "-" and src.startswith("--", i):
            flush_code(i)
            # --[[ ]] is a comment, not a comment plus a long string
            block = _long_bracket_end(src, i + 2)
            if block is not None:
                end = block
            else:
                nl = src.find("\n", i)
                end = n if nl == -1 else nl
            out.append((i, end, False))
            i = code_start = end
        elif c in "\"'":
            flush_code(i)
            end = _quoted_end(src, i)
            out.append((i, end, False))
            i = code_start = end
        elif c == "[":
            end = _long_bracket_end(src, i)
            if end is None:   # ordinary index, t[k]
                i += 1
                continue
            flush_code(i)
            out.append((i, end, False))
            i = code_start = end
        else:
            i += 1
    flush_code(n)
    return out


def code_text(src: str) -> str:
    """Only the code spans, joined, for rules that have to ignore prose."""
    return "".join(src[a:b] for a, b, is_code in spans(src) if is_code)


def sub_in_code(src: str, pattern: re.Pattern[str], repl: str) -> tuple[str, int]:
    """Substitute inside code spans only. Returns the new source and the match count."""
    pieces: list[str] = []
    total = 0
    for a, b, is_code in spans(src):
        chunk = src[a:b]
        if is_code:
            chunk, hits = pattern.subn(repl, chunk)
            total += hits
        pieces.append(chunk)
    return "".join(pieces), total


def search_in_code(src: str, pattern: re.Pattern[str]) -> int:
    return sum(
        len(pattern.findall(src[a:b])) for a, b, is_code in spans(src) if is_code
    )
