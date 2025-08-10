"""Hyperglyph manifest generator.

Derives a hypergraph-style structural manifest from a GPT-OSS config.json.
Outputs both a JSON structure and an optional Scheme-like s-expression string.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

# ---------------- Data Structures -----------------

@dataclass
class HGNode:
    name: str
    shape: List[Any]

@dataclass
class HGOperator:
    name: str
    attrs: Dict[str, Any]

@dataclass
class HGLayer:
    index: int
    kind: str
    ops: List[str]
    hash: str

@dataclass
class HGManifest:
    nodes: List[HGNode]
    operators: List[HGOperator]
    layers: List[HGLayer]
    hashing: Dict[str, Any]
    meta: Dict[str, Any]

# ---------------- Generation Logic -----------------

def _blake2b128(s: str) -> str:
    return hashlib.blake2b(s.encode(), digest_size=16).hexdigest()

def _operator_seeds(
    hidden_size: int,
    window: int,
    head_dim: int,
    router_k: int,
    experts: int,
    act: str,
    aux: float,
) -> Dict[str, str]:
    return {
        "sliding-attn": f"sliding-attn:v1:{window}:{head_dim}:{head_dim}",
        "full-attn": f"full-attn:v1:{head_dim}:{head_dim}",
        "moe-router": f"moe-router:v1:{router_k}:{experts}:{aux}",
        "feedforward": f"ff:v1:{hidden_size}:{act}",
    }

def build_manifest(cfg: Dict[str, Any]) -> HGManifest:
    hidden = cfg["hidden_size"]
    layers = cfg["num_hidden_layers"]
    num_heads = cfg["num_attention_heads"]
    kv_heads = cfg.get("num_key_value_heads", num_heads)
    head_dim = cfg["head_dim"]
    window = cfg.get("sliding_window", 128)
    router_k = (
        cfg.get("experts_per_token")
        or cfg.get("num_experts_per_tok")
        or 4
    )
    experts = cfg.get("num_local_experts", 32)
    aux = cfg.get("router_aux_loss_coef", 0.9)
    act = cfg.get("hidden_act", "silu")
    layer_types = cfg.get("layer_types", ["full_attention"] * layers)

    seeds = _operator_seeds(
        hidden, window, head_dim, router_k, experts, act, aux
    )

    nodes = [
        HGNode("token_stream", ["B", "T", hidden]),
        HGNode("kv_space", ["B", kv_heads, "T", head_dim]),
        HGNode("head_space", ["B", num_heads, "T", head_dim]),
        HGNode("expert_route", ["B", "T", router_k]),
        HGNode("position_space", ["T"]),
        HGNode("rope_phase", ["T", 2]),
        HGNode("routing_logits", ["B", "T", experts]),
    ]

    operators = [
        HGOperator("sliding-attn", {"window": window, "causal": True}),
        HGOperator("full-attn", {"causal": True}),
        HGOperator(
            "moe-router",
            {"k": router_k, "experts": experts, "loss-scale": aux},
        ),
        HGOperator("feedforward", {"act": act, "intermediate-size": hidden}),
    ]

    layer_objs: List[HGLayer] = []
    for i, kind in enumerate(layer_types):
        attn_op = (
            "sliding-attn" if kind == "sliding_attention" else "full-attn"
        )
        ops = [attn_op, "moe-router", "feedforward"]
        layer_seed = f"{attn_op}:{i}:{seeds[attn_op]}"
        h = _blake2b128(layer_seed)
        layer_objs.append(HGLayer(i, kind, ops, h))

    hashing = {
        "algorithm": "blake2b-128",
        "operator_hash_seeds": seeds,
    }
    meta = {
        "hidden_size": hidden,
        "num_layers": layers,
        "config_hash": _blake2b128(json.dumps(cfg, sort_keys=True)),
    }

    return HGManifest(nodes, operators, layer_objs, hashing, meta)

# ---------------- Serialization -----------------

def to_json(manifest: HGManifest) -> str:
    obj = {
        "nodes": [asdict(n) for n in manifest.nodes],
        "operators": [asdict(o) for o in manifest.operators],
        "layers": [asdict(layer) for layer in manifest.layers],
        "hashing": manifest.hashing,
        "meta": manifest.meta,
    }
    return json.dumps(obj, indent=2)

def to_scheme(manifest: HGManifest) -> str:
    lines: List[str] = []
    lines.append("(hyperglyph")
    lines.append("  (nodes")
    for node in manifest.nodes:
        shape_str = " ".join(str(p) for p in node.shape)
        lines.append(
            f"    (node {node.name} (shape {shape_str}))"
        )
    lines.append("  )")
    lines.append("  (operators")
    for o in manifest.operators:
        attrs = ' '.join(f"({k} {v})" for k, v in o.attrs.items())
        lines.append(f"    (op {o.name} {attrs})")
    lines.append("  )")
    lines.append("  (layers")
    for layer in manifest.layers:
        ops_str = " ".join(layer.ops)
        lines.append(
            "    (layer {idx} {kind} (ops {ops}) (hash {h}))".format(
                idx=layer.index, kind=layer.kind, ops=ops_str, h=layer.hash
            )
        )
    lines.append("  )")
    lines.append(
        "  (meta (hidden-size {0}) (num-layers {1}) (config-hash {2}))".format(
            manifest.meta["hidden_size"],
            manifest.meta["num_layers"],
            manifest.meta["config_hash"],
        )
    )
    lines.append(")")
    return '\n'.join(lines) + '\n'

# ---------------- Convenience -----------------

def generate_from_config_path(path: str) -> HGManifest:
    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    return build_manifest(cfg)

if __name__ == "__main__":  # pragma: no cover
    import sys
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    m = generate_from_config_path(cfg_path)
    print(to_json(m))
