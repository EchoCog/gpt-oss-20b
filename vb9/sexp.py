"""Very small S-expression utilities.

Parsing approach: balanced parentheses, atoms are symbols or numbers or strings.
Not production ready—just enough for experimentation.
"""
from __future__ import annotations

import re, hashlib
from typing import Any, Iterable

Symbol = str

TOKEN_RE = re.compile(r"\s*(;.*|"(?:[^"\\]|\\.)*"|[()]|[^()\s]+)")

def tokenize(src: str) -> Iterable[str]:
    for m in TOKEN_RE.finditer(src):
        tok = m.group(1)
        if tok.startswith(";"):
            continue
        yield tok

def parse(src: str) -> Any:
    toks = list(tokenize(src))
    pos = 0

    def atom(t: str):
        if t.startswith("\"") and t.endswith("\""):
            return bytes(t[1:-1], "utf-8").decode("unicode_escape")
        try:
            if "." in t:
                return float(t)
            return int(t)
        except ValueError:
            return t  # symbol

    def read():
        nonlocal pos
        if pos >= len(toks):
            raise ValueError("Unexpected EOF")
        t = toks[pos]; pos += 1
        if t == "(":
            lst = []
            while pos < len(toks) and toks[pos] != ")":
                lst.append(read())
            if pos >= len(toks):
                raise ValueError("Unclosed (")
            pos += 1  # consume )
            return tuple(lst)
        elif t == ")":
            raise ValueError(") without (")
        else:
            return atom(t)

    exprs = []
    while pos < len(toks):
        exprs.append(read())
    return exprs[0] if len(exprs) == 1 else tuple(exprs)

def to_canonical(expr: Any) -> Any:
    if isinstance(expr, tuple) and expr:
        head, *rest = expr
        if head == '#:commutative':
            return (head, tuple(sorted((to_canonical(r) for r in rest), key=repr)))
        return (head, *(to_canonical(r) for r in rest))
    return expr

def hash_sexp(expr: Any) -> str:
    canon = repr(to_canonical(expr)).encode()
    return hashlib.blake2b(canon, digest_size=16).hexdigest()

def sexp_to_path(expr: Any) -> str:
    if not isinstance(expr, tuple):
        return f"/{expr}"
    return "/" + "/".join(str(e) for e in expr)
