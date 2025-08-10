"""VB9 prototype package.

Lightweight experimental scaffolding to explore the
(designer → compiler → runtime) loop described in the conceptual docs.
Intentionally minimal & pure-Python; no external deps.
"""

__all__ = [
    "styx",
    "sexp",
    "glyph",
    "ide",
    "logic",
    "spi",
    "gestures",
    "hyperglyph",
]

from .seed import (
    parse_seed,
    bootstrap_chain,
    Stage0Seed,
    Stage1Pattern,
    Stage2Symbols,
    Stage3Eval,
)
__all__ += [
    "parse_seed",
    "bootstrap_chain",
    "Stage0Seed",
    "Stage1Pattern",
    "Stage2Symbols",
    "Stage3Eval",
]
