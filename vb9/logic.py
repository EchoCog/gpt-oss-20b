"""Backward chaining (Prolog-like) skeleton used to mirror the Guix analogy.

This module provides a tiny goal resolution engine with memoization that can
be reused to interpret VB9 glyph/kernel dependencies declaratively.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple, Any

RuleFn = Callable[[Tuple[Any, ...]], Iterable[Tuple[Any, ...]]]

@dataclass(frozen=True)
class Fact:
    head: Tuple[Any, ...]

class KB:
    def __init__(self):
        self.facts: Dict[Tuple[Any, ...], bool] = {}
        self.rules: Dict[str, List[RuleFn]] = {}
        self.memo: Dict[Tuple[Any, ...], bool] = {}

    def add_fact(self, *atom: Any) -> None:
        self.facts[tuple(atom)] = True

    def add_rule(self, name: str, fn: RuleFn) -> None:
        self.rules.setdefault(name, []).append(fn)

    def prove(self, goal: Tuple[Any, ...]) -> bool:
        if goal in self.memo:
            return self.memo[goal]
        if goal in self.facts:
            self.memo[goal] = True
            return True
        name = goal[0]
        for rule in self.rules.get(name, []):
            for expansion in rule(goal):
                if all(self.prove(sub) for sub in expansion):
                    self.memo[goal] = True
                    return True
        self.memo[goal] = False
        return False

def example_kb() -> KB:
    kb = KB()
    kb.add_fact("bootstrap", "gcc")

    def build_rule(goal: Tuple[Any, ...]):
        (_, pkg) = goal
        if pkg == "emacs":
            yield (("build", "gtk"), ("build", "elisp"))
        elif pkg == "gtk":
            yield (("build", "glib"), ("build", "cairo"))
        elif pkg == "glib":
            yield (("build", "libc"),)
        elif pkg == "libc":
            yield (("bootstrap", "gcc"),)

    kb.add_rule("build", build_rule)
    return kb
