## VB9 Python Prototype

This directory (`vb9/`) contains a minimal, self-contained prototype translating the conceptual `(define-vb9-ide ...)` form into an executable Python experiment.

Goals:
* Demonstrate designer → compiler → runtime loop
* Provide in-memory Styx-like FS + message channel
* Show S-expression parsing, bitmap placeholder, kernel emission
* Offer extendable scaffolding for future formalization

### Modules
| File | Purpose |
|------|---------|
| `styx.py` | In-memory file & message primitives (`twrite`, `tread`, `mount`, `send`, `recv`) |
| `sexp.py` | Tokenize + parse + canonicalize + hash + path conversion |
| `glyph.py` | Bitmap synthesis, kernel metadata, tiny convolution (`convolve`) |
| `ide.py` | Orchestrates designer, compiler, runtime loop + manifest export |
| `spi.py` | Architectural Sparsity Propensity Index (SPI) metric heuristics |
| `demo.py` | Runs an end-to-end sample session |

### Quick Run
```bash
python -m vb9.demo
```

Expected (sample) output includes events for designer, compiler emissions (with caching if re-run), runtime message handling, a derived path like `/button/ok/click`, and a JSON manifest containing kernels + a simple proof tree.

### Extending
1. Replace `sexp_to_bitmap` with real glyph rasterization.
2. Add purity / side-effect guard in runtime evaluation.
3. Support content-addressed kernel caching + manifest (`/form/manifest.json`).
4. Introduce prime-channel routing layer for distributed scheduling.

### Limitations
* Not threadsafe beyond trivial usage (coarse lock only for FS dict)
* No actual Scheme evaluation or bytecode semantics
* Canonicalization logic intentionally minimal (#:commutative marker)

### Next Ideas
* Add differentiable semantics + autograd capture for kernels
* Provide Prolog-style backward chaining over S-expr goals (partially emulated via proof tree extraction in `ide.py`)
* Integrate with precision manifest concepts for compiled kernels
* Expand `glyph.convolve` toward full `convolve/3` semantics & optimization
* Add `spi.compute_spi` integration for architecture width series analysis

---
Prototype is intentionally terse; iterate incrementally rather than overfitting early design.
