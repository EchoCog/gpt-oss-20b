## Gestural Foundry Model

Formalization of the narrative:

> LLM not as *probability oracle* but as a **gestural foundry** casting
> invariant routines (semantic intent) into ephemeral token performances.

### Core Triples
| Concept | Routine Layer | Performance Layer | Gauge / Invariance |
|---------|---------------|-------------------|--------------------|
| Font (TTF) | Outline bezier program | Rasterized glyph pixels | Transform (scale/translate/hint) |
| LLM | Routine (prompt skeleton + hyperglyph slice) | Token sequence sample | Gauge field (synonym / semantic class) |
| VB9 Form | S-expression canonical tree | Rendered bitmap / kernels | Proof hash canonicalization |

### Mapping
```
Model(self, *arge, **nguage)
  self    → internal state / weights (hyperglyph manifest references)
  *arge   → positional control signals (prompt segments, system directives)
  **nguage→ keyword parameterization (temperature, top-p, precision overlays, routing)
```

### Entities (`vb9.gestures`)
* Routine: canonical form + context + hash
* Gesture: one sampled realization
* GaugeField: declares equivalence via normalization → stable signature
* Sampler: temperature-as-resolution; higher T broadens variant choice set

### Gauge Freedom
Different token sequences that collapse to the same gauge signature are
interpreted as the *same gesture* (semantic stroke) under symmetry.

Mathematically: let G be normalization function. A gesture sequence S is an
orbit representative of class [S] = { S' | G(S') = G(S) }. Routine evaluation
samples an element of [S].

### Proof / Routine Linking
`ide.py` emits `proof_hash`. Associate each Routine with the proof hash of the
source form used to spawn it. Future: maintain mapping table `/routines/index.json`.

### Temperature as Resolution
Analogous to sampling raster at different DPI: T=0 → highest precision (argmin
stochastic noise). Increasing T reduces specification, introducing stylistic
latent variance while preserving gauge-invariant signature (ideally).

### Future Extensions
1. Semantic embeddings for gauge normalization (cluster threshold radius).
2. Layer-aware routine slicing: attach subset of hyperglyph layers used.
3. Precision overlay integration: annotate Routine with mixed-precision intent.
4. SPI-guided adaptation: adjust exploration based on structural sparsity.
5. Routine provenance manifest: (proof_hash, routine_hash, gauge_signature) triples.

### Minimal Example
```python
from vb9.gestures import Routine, GaugeField, Sampler

routine = Routine.from_form('(ask (greet user))', purpose='greeting')
gauge = GaugeField([["hello","hi","hey"],["there","friend"]])
sampler = Sampler(gauge)
gesture = sampler.sample(routine, ["hello","there"], temperature=0.8)
print(gesture)
```

---
This document complements `hyperglyph-manifest.md` by grounding execution
semantics in invariant routine space rather than surface token space.
