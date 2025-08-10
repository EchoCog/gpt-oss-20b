# Cognitive Hyperglyph Manifest (Prototype)

This document sketches a Scheme-flavored manifest mapping the GPT-OSS model
(topology from `config.json`) into a hypergraph / hypermultiset view where:

* A single hidden state block: 2880 (feature width) × 24 (layers)
* Clusters: `3 + 11 × 24` conceptual hypermultiset operators acting across
  dimensions (e.g. router, attention pattern families, MoE expert selection).
* Alternating layer-types form two interleaved operator families:
  - `sliding_attention` (local receptive field length = 128 window)
  - `full_attention` (global receptive capacity)

We treat each layer L (0..23) as producing/consuming a hyperedge connecting:
`(token_stream  head_space  kv_space  expert_route  position_space)`

## High-Level Parameters
```
(hidden-size 2880)
(num-layers 24)
(num-heads 64)
(num-kv-heads 8)
(head-dim 64)
(sliding-window 128)
(context-length 131072)
(vocab-size 201088)
(router (experts-per-token 4) (local-experts 32) (aux-loss-coef 0.9))
(rope (theta 150000) (scaling yarn (factor 32.0) (beta-fast 32.0) (beta-slow 1.0)))
(quant (method mxfp4) (exclude "model.layers.*.self_attn" "model.layers.*.mlp.router" "model.embed_tokens" "lm_head"))
```

## Hypergraph Entities
```
(node token_stream :shape (B T 2880)) ; batch, time, width
(node kv_space      :shape (B num_kv_heads T head_dim))
(node head_space    :shape (B num_heads T head_dim))
(node expert_route  :shape (B T experts_per_token))
(node position_space :shape (T))
(node rope_phase     :shape (T 2))
(node routing_logits :shape (B T num_local_experts))
```

## Operator Macros
```
(define-operator sliding-attn (layer)
  (inputs token_stream kv_space rope_phase)
  (window 128) (causal #t)
  (produces head_space))

(define-operator full-attn (layer)
  (inputs token_stream kv_space rope_phase)
  (causal #t)
  (produces head_space))

(define-operator moe-router (layer)
  (inputs token_stream)
  (k experts_per_token)
  (experts num_local_experts)
  (loss-scale router_aux_loss_coef)
  (produces expert_route routing_logits))

(define-operator feedforward (layer)
  (inputs token_stream expert_route)
  (act silu) (intermediate-size 2880)
  (produces token_stream))
```

## Layer Expansion
Each layer binds `layer = i` and selects one of two attention operators following `layer_types` sequence. Pseudocode expansion:
```
(define (layer-op i kind)
  (case kind
    ((sliding_attention) (sliding-attn i))
    ((full_attention)    (full-attn i))))

(define (layer-graph i kind)
  (let* ((attn (layer-op i kind))
         (route (moe-router i))
         (ff   (feedforward i)))
    (hyperedges attn route ff)))

(define (model-graph)
  (apply append (map (lambda (i kind) (layer-graph i kind)) (iota 24) layer_types)))
```

## Genesis / Hashing
Attach deterministic structural hashes per operator for caching:
```
(operator-hash sliding-attn (blake2b "sliding-attn:v1:128:64:64"))
(operator-hash full-attn    (blake2b "full-attn:v1:64:64"))
(operator-hash moe-router   (blake2b "moe-router:v1:4:32:0.9"))
(operator-hash feedforward  (blake2b "ff:v1:2880:silu"))
```
A layer instance hash:
```
(layer-hash i kind
  (blake2b (string-append kind ":" (number->string i) ":" (operator-hash kind))))
```

## Cognitive Hyperglyph Manifest (JSON Sketch)
```json
{
  "nodes": [
    {"name": "token_stream", "shape": ["B", "T", 2880]},
    {"name": "kv_space", "shape": ["B", 8, "T", 64]},
    {"name": "head_space", "shape": ["B", 64, "T", 64]},
    {"name": "expert_route", "shape": ["B", "T", 4]},
    {"name": "position_space", "shape": ["T"]},
    {"name": "rope_phase", "shape": ["T", 2]},
    {"name": "routing_logits", "shape": ["B", "T", 32]}
  ],
  "operators": [
    {"name": "sliding-attn", "attrs": {"window":128,"causal":true}},
    {"name": "full-attn",    "attrs": {"causal":true}},
    {"name": "moe-router",    "attrs": {"k":4,"experts":32,"loss-scale":0.9}},
    {"name": "feedforward",   "attrs": {"act":"silu","intermediate-size":2880}}
  ],
  "layers": [
    {"index": 0,  "kind": "sliding_attention", "ops": ["sliding-attn","moe-router","feedforward"]},
    {"index": 1,  "kind": "full_attention",    "ops": ["full-attn","moe-router","feedforward"]}
    /* truncated for brevity: repeat pattern up to index 23 */
  ],
  "hashing": {
    "algorithm": "blake2b-128",
    "operator_hash_seeds": {
      "sliding-attn": "sliding-attn:v1:128:64:64",
      "full-attn": "full-attn:v1:64:64",
      "moe-router": "moe-router:v1:4:32:0.9",
      "feedforward": "ff:v1:2880:silu"
    }
  }
}
```

## Integration Path
1. Auto-generate this manifest from `config.json` in a future `vb9.hyperglyph` module.
2. Emit per-layer structural hash + store under `/graph/layers/<i>.json` in Styx FS.
3. Use proof-tree hashing (already in `ide.py`) to link editor forms to model layer subsets.
4. Extend SPI metric to evaluate width evolution or hypothetical expansion proposals.
5. Introduce quantization overlays: attach precision manifest slices on each operator.

## Next Steps
- Implement `vb9/hyperglyph.py` to produce JSON + Scheme emission.
- Add caching keyed by `(config-hash, code-hash)`.
- Export a minimal DOT / Mermaid representation for visualization.
- Map router load balancing stats into future dynamic hyperedge weights.
