"""Glyph + kernel placeholder utilities.

Adds a slightly richer bitmap generator and a simple convolution primitive
to inch closer to a future `convolve/3` semantic while remaining lightweight.
"""
from __future__ import annotations

from typing import Any, Iterable
from . import sexp


def sexp_to_bitmap(expr: Any) -> list[list[int]]:
    """Generate a deterministic pseudo-bitmap from the S-expression.

    Strategy: hash each leaf symbol into a short binary stripe and
    tile / interleave across lines to reflect structural ordering.
    This keeps output stable while being more structure-aware than a
    flat repr-based byte parity.
    """
    leaves = extract_glyphs(expr)
    if not leaves:
        leaves = ["∅"]
    # Each leaf becomes a column chunk of bits derived from its hash hex.
    columns: list[list[int]] = []
    max_len = 0
    for sym in leaves:
        h = sexp.hash_sexp(sym)
        bits = [1 if c in "89abcdef" else 0 for c in h]
        max_len = max(max_len, len(bits))
        columns.append(bits)
    # Normalize column lengths
    for col in columns:
        if len(col) < max_len:
            col.extend([0] * (max_len - len(col)))
    # Transpose columns -> rows (limit height for sanity)
    height = min(64, max_len)
    width = min(64, len(columns))
    rows: list[list[int]] = []
    for r in range(height):
        row = [columns[c][r] for c in range(width)]
        rows.append(row)
    return rows


def extract_glyphs(expr: Any) -> list[str]:
    out: list[str] = []

    def walk(e: Any) -> None:
        if isinstance(e, tuple):
            for x in e:
                walk(x)
        elif isinstance(e, str):
            out.append(e)

    walk(expr)
    # Preserve order while deduplicating
    return list(dict.fromkeys(out))


def backpropagate_glyph(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "kernel": f"kernel::{symbol}",
        "hash": sexp.hash_sexp(symbol),
    }


def kernel_name(kern: dict) -> str:
    return kern["symbol"]


def kernel_to_bytecode(kern: dict) -> bytes:
    return f"BYTECODE({kern['symbol']}:{kern['hash']})".encode()


def convolve(
    bitmap: list[list[int]],
    kernel: Iterable[Iterable[int]] | None = None,
) -> list[list[int]]:
    """Very small 2D convolution (no padding) for experimentation.

    Args:
        bitmap: 2D int matrix (0/1 values).
        kernel: 2D int kernel; defaults to a 3x3 all-ones box.
    Returns:
        2D int matrix of convolution sums.
    """
    if not bitmap:
        return []
    k = [list(row) for row in (kernel or [[1, 1, 1], [1, 1, 1], [1, 1, 1]])]
    kh, kw = len(k), len(k[0])
    h, w = len(bitmap), len(bitmap[0])
    out_h = max(0, h - kh + 1)
    out_w = max(0, w - kw + 1)
    out: list[list[int]] = [[0] * out_w for _ in range(out_h)]
    for i in range(out_h):
        for j in range(out_w):
            acc = 0
            for ki in range(kh):
                row = bitmap[i + ki]
                kro = k[ki]
                for kj in range(kw):
                    acc += row[j + kj] * kro[kj]
            out[i][j] = acc
    return out
