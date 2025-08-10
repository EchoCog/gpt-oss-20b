"""Minimal cognitive bootstrap (Stage0 → stages) inspired by manifest vision.

Stages (conceptual, lightweight placeholders):
    Stage0: Seed manifest (self, *structure, **computation)
    Stage1: Pattern matching scaffold
    Stage2: Symbol manipulation table
    Stage3: Meta-eval (tiny applicative evaluator subset)

Goal: traceable expansion chain from atomic seed to richer substrate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Callable
import hashlib

from . import sexp

SeedExpr = Any


@dataclass
class Stage0Seed:
    self_ref: Any
    structure: Any
    computation: Any
    hash: str

    def next(self) -> "Stage1Pattern":
        return stage1_from_seed(self)


def _blake(data: Any) -> str:
    return hashlib.blake2b(repr(data).encode(), digest_size=16).hexdigest()


def parse_seed(form_src: str) -> Stage0Seed:
    expr = sexp.parse(form_src)
    if not isinstance(expr, tuple):  # accept single atom fallback
        raise ValueError("Seed must be a list-like S-expression")
    mapping = {}
    for entry in expr:
        if not isinstance(entry, tuple) or len(entry) < 2:
            continue
        head = entry[0]
        body = entry[1:] if len(entry) > 2 else entry[1]
        mapping[head] = body
    self_ref = mapping.get("self")
    structure = mapping.get("*structure") or mapping.get("*layers")
    computation = mapping.get("**computation") or mapping.get("**heads")
    seed_hash = _blake([self_ref, structure, computation])
    return Stage0Seed(self_ref, structure, computation, seed_hash)


@dataclass
class Stage1Pattern:
    seed: Stage0Seed
    patterns: Dict[str, str]
    hash: str

    def next(self) -> "Stage2Symbols":
        return stage2_from_stage1(self)


def stage1_from_seed(seed: Stage0Seed) -> Stage1Pattern:
    # Derive trivial pattern set from structure specification tokens
    base_tokens: List[str] = []
    if isinstance(seed.structure, tuple):
        base_tokens = [str(t) for t in seed.structure]
    elif seed.structure is not None:
        base_tokens = [str(seed.structure)]
    patterns = {tok: f"ACTION:{tok}" for tok in base_tokens[:8]}
    h = _blake([seed.hash, sorted(patterns.items())])
    return Stage1Pattern(seed, patterns, h)


@dataclass
class Stage2Symbols:
    stage1: Stage1Pattern
    symbols: Dict[str, int]
    hash: str

    def next(self) -> "Stage3Eval":
        return stage3_from_stage2(self)


def stage2_from_stage1(stage1: Stage1Pattern) -> Stage2Symbols:
    # Assign incremental ids to pattern actions
    symbols: Dict[str, int] = {}
    for i, (pat, _) in enumerate(sorted(stage1.patterns.items())):
        symbols[pat] = i
    h = _blake([stage1.hash, symbols])
    return Stage2Symbols(stage1, symbols, h)


@dataclass
class Stage3Eval:
    stage2: Stage2Symbols
    env: Dict[str, Any]
    evaluator: Callable[[Any], Any]
    hash: str

    def eval(self, expr: Any) -> Any:
        return self.evaluator(expr)


def stage3_from_stage2(stage2: Stage2Symbols) -> Stage3Eval:
    # Very small recursively applied evaluator for (seq ...) and atoms.
    env: Dict[str, Any] = {
        "symbols": stage2.symbols,
        "count-symbols": lambda: len(stage2.symbols),
    }

    def _eval(e: Any) -> Any:
        if isinstance(e, tuple) and e:
            op = e[0]
            if op == "seq":
                last = None
                for sub in e[1:]:
                    last = _eval(sub)
                return last
            if op == "count-symbols":
                return env["count-symbols"]()
            return tuple(_eval(x) for x in e)
        return e

    h = _blake([stage2.hash, "eval", len(stage2.symbols)])
    return Stage3Eval(stage2, env, _eval, h)


def bootstrap_chain(seed_src: str) -> Dict[str, Any]:
    """Produce all stages from a seed source string."""
    s0 = parse_seed(seed_src)
    s1 = s0.next()
    s2 = s1.next()
    s3 = s2.next()
    return {
        "stage0": s0,
        "stage1": s1,
        "stage2": s2,
        "stage3": s3,
    }


__all__ = [
    "parse_seed",
    "bootstrap_chain",
    "Stage0Seed",
    "Stage1Pattern",
    "Stage2Symbols",
    "Stage3Eval",
]
