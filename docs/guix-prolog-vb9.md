## Guix ↔ Prolog ↔ VB9 Unification Pattern

This document summarizes the unified backward-chaining / reproducible-build / glyph derivation pattern.

### Core Mapping
| Concept | Guix | Prolog | VB9 Prototype |
|---------|------|--------|---------------|
| Goal | Manifest target package/profile | Query | Target form/glyph set |
| Subgoals | Derivation inputs | Clause body predicates | Decomposed glyph kernels |
| Base facts | Bootstrap binaries in store | Ground facts | Primitive kernels |
| Execution | Builder scripts (pure env) | Rule expansion + resolution | Rendering + kernel emission |
| Cache | /gnu/store (content addressed) | Memo table | In-memory styx FS + hash paths |
| Proof artifact | Store path hash | Successful derivation trace | Proof tree → *.kernel |

### Backward Chaining Flow
1. Declare goal state (package, glyph, activation kernel set).
2. Resolver expands dependencies (derivations / subgoals / composite kernels).
3. Shared subgoals collapse into DAG (memoization).
4. Execute leaf builders (deterministic → reproducible hash).
5. Materialize & cache artifacts; subsequent proofs shortcut.

### Why It Matters
* Uniform mental model for package management, logic inference, model compilation, glyph rendering.
* Enables provenance queries ("why does this artifact exist?").
* Supports distribution by shipping proof trees instead of full artifacts.

### Prototype Hooks
* `vb9/logic.py` minimal knowledge base + backward prover.
* Future: integrate IDE compiler with logic-driven dependency expansion.

### Next Extensions
1. Attach cryptographic hashes to proven subgoals.
2. Export proof tree as JSON manifest for replay.
3. Failure explanation path (minimal unsatisfied subgoal set).

---
Incremental implementation will gradually replace ad-hoc traversal with logic-driven resolution.
