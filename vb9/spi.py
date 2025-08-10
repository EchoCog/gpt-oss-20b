"""Sparsity Propensity Index (SPI) calculator prototype.

Metrics implemented (rough heuristics):
  - LRI  (Layer Ratio Irrationality)
  - CFD  (Continued Fraction Dispersion)
  - SI   (Spectral Incoherence)
  - PFD  (Prime Factor Dispersion)

Composite SPI0 = simple mean of metrics. All metrics roughly in [0,1].
"""
from __future__ import annotations

import math
from statistics import median, variance
from typing import List, Dict


def _continued_fraction(x: float, depth: int = 8) -> List[int]:
    out: List[int] = []
    for _ in range(depth):
        a = int(math.floor(x))
        out.append(a)
        frac = x - a
        if frac < 1e-12:
            break
        x = 1.0 / frac
    return out


def _min_denominator(r: float, Q: int = 10_000, eps: float = 1e-6) -> int:
    for q in range(1, Q + 1):
        p = round(r * q)
        if abs(r - p / q) < eps:
            return q
    return Q


def _prime_factors(n: int) -> List[int]:
    f: List[int] = []
    x = n
    d = 2
    while d * d <= x:
        while x % d == 0:
            f.append(d)
            x //= d
        d += 1 if d == 2 else 2
    if x > 1:
        f.append(x)
    return f


def compute_spi(widths: List[int]) -> Dict[str, float]:
    assert len(widths) > 1, "Need >=2 widths"
    ratios = [widths[i + 1] / widths[i] for i in range(len(widths) - 1)]

    # LRI: normalized median of denominators of rational approximants.
    Q = 5000
    denoms = [_min_denominator(r, Q) for r in ratios]
    lri = median(math.log(d + 1) / math.log(Q + 1) for d in denoms)

    # CFD: inverse variance of continued fraction terms (excluding int part).
    cfd_vals = []
    for r in ratios:
        cf = _continued_fraction(r, depth=6)[1:]
        if not cf:
            continue
        v = variance(cf) if len(cf) > 1 else 0.0
        cfd_vals.append(1.0 / (1.0 + v))
    cfd = sum(cfd_vals) / len(cfd_vals) if cfd_vals else 0.0

    # SI: histogram dispersion of fractional parts of log ratios.
    fracs = [(math.log(r) % 1.0) for r in ratios]
    bins = 16
    hist = [0] * bins
    for f in fracs:
        hist[int(f * bins) % bins] += 1
    total = len(fracs)
    max_freq = max(hist) / total
    si = 1.0 - max_freq

    # PFD: diversity of prime factors across widths.
    factors = [_prime_factors(w) for w in widths]
    unique_primes = set(p for lst in factors for p in lst)
    avg_len = sum(len(lst) for lst in factors) / len(factors)
    if unique_primes:
        pfd = len(unique_primes) / (len(unique_primes) + avg_len)
    else:
        pfd = 0.0

    metrics = {"LRI": lri, "CFD": cfd, "SI": si, "PFD": pfd}
    metrics["SPI0"] = sum(metrics.values()) / len(metrics)
    return metrics


if __name__ == "__main__":  # pragma: no cover
    example = [512, 829, 1343, 2171, 3514]
    print(compute_spi(example))
