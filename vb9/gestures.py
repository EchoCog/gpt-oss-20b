"""Gestural language routines abstraction.

Maps the conceptual framing:
  LLM ≈ Model(self, *arge, **nguage)
into minimal code primitives capturing:
  * Routine (invariant gestural intent)
  * Gesture (one stochastic performance / sample)
  * GaugeField (normalizes equivalent gestures under symmetry)
  * Temperature as resolution (controls exploration granularity)

Intentionally lightweight; no deep ML dependency—semantic scaffold bridging
editor forms / hyperglyph manifest to generative acts.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
import math
import hashlib
from typing import Sequence, Dict, Any


# ---------------- Core Data Types -----------------

@dataclass
class Routine:
    """Gestural routine (semantic intent) identified by canonical form."""
    form: str
    context: Dict[str, Any]
    hash: str

    @staticmethod
    def from_form(form: str, **context: Any) -> "Routine":
        canon = form.strip()
        h = hashlib.blake2b(canon.encode(), digest_size=16).hexdigest()
        return Routine(canon, context, h)


@dataclass
class Gesture:
    """One realization (performance) of a Routine."""
    tokens: list[str]
    routine_hash: str
    gauge_signature: str
    temperature: float


class GaugeField:
    """Defines equivalence classes of gestures via normalization."""
    def __init__(self, synonym_classes: Sequence[Sequence[str]] | None = None):
        self.syn_map: Dict[str, str] = {}
        if synonym_classes:
            for cls in synonym_classes:
                if not cls:
                    continue
                root = min(cls, key=len)
                for w in cls:
                    self.syn_map[w.lower()] = root.lower()

    def normalize_token(self, t: str) -> str:
        key = t.lower()
        return self.syn_map.get(key, key)

    def signature(self, tokens: Sequence[str]) -> str:
        norm = [self.normalize_token(t) for t in tokens]
        joined = "\u241f".join(norm)
        return hashlib.blake2b(joined.encode(), digest_size=16).hexdigest()


class Sampler:
    """Temperature-as-resolution sampling facade."""
    def __init__(self, gauge: GaugeField):
        self.gauge = gauge

    def sample(
        self,
        routine: Routine,
        intent_tokens: Sequence[str],
        temperature: float = 1.0,
    ) -> Gesture:
        temperature = max(0.0, temperature)
        rng = random.random
        out: list[str] = []
        for tok in intent_tokens:
            variants = self._variants(tok)
            if temperature == 0 or len(variants) == 1:
                choice = variants[0]
            else:
                scores = [1.0 / (len(v) + 1) for v in variants]
                if temperature != 1.0:
                    pow_exp = 1.0 / max(1e-6, temperature)
                    scores = [s ** pow_exp for s in scores]
                total = sum(scores)
                r = rng() * total
                acc = 0.0
                choice = variants[-1]
                for v, s in zip(variants, scores):
                    acc += s
                    if r <= acc:
                        choice = v
                        break
            out.append(choice)
        sig = self.gauge.signature(out)
        return Gesture(out, routine.hash, sig, temperature)

    @staticmethod
    def _variants(token: str) -> list[str]:
        table = {
            "hello": ["hello", "hi", "greetings", "hey"],
            "there": ["there", "friend", "traveler"],
            "world": ["world", "earth", "cosmos"],
        }
        return table.get(token.lower(), [token])


# ---------------- Utility -----------------

def temperature_schedule(low: float, high: float, steps: int) -> list[float]:
    if steps <= 1:
        return [low]
    return [low + (high - low) * (i / (steps - 1)) for i in range(steps)]


def adaptive_temperature(metric: float) -> float:
    """Map a confidence / entropy metric in [0,1] to a temperature.

    Lower metric -> explore more (higher temp); higher metric -> exploit.
    """
    metric = min(1.0, max(0.0, metric))
    return 0.2 + 1.2 * (1.0 - math.sqrt(metric))


__all__ = [
    "Routine",
    "Gesture",
    "GaugeField",
    "Sampler",
    "temperature_schedule",
    "adaptive_temperature",
]
