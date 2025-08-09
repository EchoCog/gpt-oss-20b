"""Glyph + kernel placeholder utilities."""
from __future__ import annotations

from typing import Any
from . import sexp

def sexp_to_bitmap(expr: Any) -> list[list[int]]:
    s = repr(expr)
    width = min(64, max(4, int(len(s) ** 0.5)))
    rows = []
    cur = []
    for ch in s.encode():
        cur.append(1 if ch % 2 else 0)
        if len(cur) == width:
            rows.append(cur); cur = []
    if cur:
        while len(cur) < width:
            cur.append(0)
        rows.append(cur)
    return rows

def extract_glyphs(expr: Any) -> list[Any]:
    out = []
    def walk(e):
        if isinstance(e, tuple):
            for x in e: walk(x)
        elif isinstance(e, str):
            out.append(e)
    walk(expr)
    return list(dict.fromkeys(out))

def backpropagate_glyph(symbol: str) -> dict:
    return {"symbol": symbol, "kernel": f"kernel::{symbol}", "hash": sexp.hash_sexp(symbol)}

def kernel_name(kern: dict) -> str:
    return kern["symbol"]

def kernel_to_bytecode(kern: dict) -> bytes:
    return f"BYTECODE({kern['symbol']}:{kern['hash']})".encode()
