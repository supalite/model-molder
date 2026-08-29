"""Find Luau function bodies so a module can be stripped down to its interface.

The architectural mining task is "here are the types, signatures and doc comments,
implement it", which means deleting the bodies and leaving everything else intact.
Runs over code spans only, so an `end` sitting in a string or a comment never counts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from luau_spans import spans

TOKEN = re.compile(r"\b(function|if|for|while|repeat|do|end|until|then)\b")


@dataclass(frozen=True)
class FunctionBlock:
    header_start: int   # the `function` keyword
    body_start: int     # just past the closing paren / return type
    end_start: int      # the matching `end`
    end_stop: int       # just past it
    name: str


def _code_tokens(src: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for a, b, is_code in spans(src):
        if not is_code:
            continue
        for m in TOKEN.finditer(src, a, b):
            out.append((m.start(), m.group(1)))
    return out


_SIG_END = re.compile(r"\)(\s*:\s*[^\n]+?)?(?=\s*(\n|$))")
_NAME = re.compile(r"function\s+([\w.:]+)?\s*\(")


def functions(src: str) -> list[FunctionBlock]:
    """Every function block, nested ones included, outermost first."""
    toks = _code_tokens(src)
    out: list[FunctionBlock] = []

    for i, (pos, tok) in enumerate(toks):
        if tok != "function":
            continue
        # `end` closes function/if/for/while/do alike, so we have to count depth rather
        # than pattern-match. The catch is `for ... do`: that `do` belongs to the `for`
        # and must not open a second block.
        depth = 0
        pending_do = False
        j = i
        while j < len(toks):
            p, t = toks[j]
            if t in ("function", "if"):
                depth += 1
            elif t in ("for", "while"):
                depth += 1
                pending_do = True
            elif t == "do":
                if pending_do:
                    pending_do = False
                else:
                    depth += 1
            elif t == "repeat":
                depth += 1
            elif t == "until":
                depth -= 1
            elif t == "end":
                depth -= 1
                if depth == 0:
                    m = _NAME.search(src, pos, min(len(src), pos + 200))
                    sig = _SIG_END.search(src, pos, p)
                    if sig:
                        out.append(FunctionBlock(
                            header_start=pos, body_start=sig.end(),
                            end_start=p, end_stop=p + 3,
                            name=(m.group(1) if m and m.group(1) else "<anon>"),
                        ))
                    break
            j += 1
    return out


def top_level(src: str) -> list[FunctionBlock]:
    blocks = functions(src)
    out: list[FunctionBlock] = []
    for b in blocks:
        if not any(o.header_start < b.header_start and b.end_stop <= o.end_stop for o in blocks):
            out.append(b)
    return out
