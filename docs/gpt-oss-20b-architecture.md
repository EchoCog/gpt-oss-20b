## GPT-OSS 20B Architecture and Topology (Repo Snapshot)

This document summarizes the model topology and precision layout discovered in the repo configs, and links to a formal Z++ specification.

### Key topology parameters
- **Layers**: 24
- **Layer schedule**: Alternating `sliding_attention` and `full_attention` per layer (even-indexed: sliding; odd-indexed: full). `sliding_window = 128`.
- **Hidden size**: 2880 (`hidden_size`)
- **Intermediate size**: 2880 (`intermediate_size`, experts are gated MoE SwiGLU)
- **Attention**:
  - **Heads (Q)**: 64 (`num_attention_heads`)
  - **KV heads**: 8 (`num_key_value_heads`)
  - **Head dim**: 64 (`head_dim`)
  - **Attention bias**: true (`attention_bias`)
  - **Dropout**: 0.0 (`attention_dropout`)
- **MoE**:
  - **Local experts**: 32 (`num_local_experts`)
  - **Top-k per token**: 4 (`experts_per_token`, `num_experts_per_tok`)
  - **Router aux loss coef**: 0.9 (`router_aux_loss_coef`)
  - **Gated activation**: SiLU/SwiGLU (`hidden_act = silu`, `swiglu_limit = 7.0`)
- **Positions / RoPE**:
  - **Max positions**: 131072 (`max_position_embeddings`)
  - **RoPE theta**: 150000 (`rope_theta`)
  - **YARN scaling**: factor 32 (`rope_scaling.factor = 32.0`, `rope_scaling.rope_type = yarn`)
  - **Initial context**: 4096 (`initial_context_length`)
- **Embedding**:
  - **Vocab size**: 201088 (`vocab_size`)
  - **Tie embeddings**: false (`tie_word_embeddings`)
- **Norm**: RMSNorm eps 1e-5 (`rms_norm_eps`)
- **Cache**: `use_cache = true`

### Precision and quantization
- **Quantization method**: `mxfp4` (`quantization_config.quant_method`)
- **Modules excluded from conversion** (kept in BF16): `model.layers.*.self_attn`, `model.layers.*.mlp.router`, `model.embed_tokens`, `lm_head` (`quantization_config.modules_to_not_convert`).
- This matches the hybrid scheme summarized in `docs/precision-manifest.md`: attention/embeddings/router in BF16; expert MLP weights stored as FP4 blocks with UE8 scales.

### Tokenizer and special tokens
- **Special tokens** (IDs): `<|startoftext|>=199998`, `<|endoftext|>=199999`, `<|return|>=200002`, `<|constrain|>=200003`, `<|channel|>=200005`, `<|start|>=200006`, `<|end|>=200007`, `<|message|>=200008`, `<|endofprompt|>=200018`.
- **Pad/BOS/EOS**: `pad_token_id=199999`, `bos_token=<|startoftext|>`, `eos_token=<|return|>`.

### Attention schedule
- Layers alternate between local `sliding_attention` (window 128) and global `full_attention`. This preserves global mixing frequency while keeping many layers linear in sequence length.

### Formal specification
See the companion Z++ spec saved at:
- `docs/gpt-oss-20b.zpp`

### Deployment notes (size/speed/hardware)
- **VRAM target**: ~16–24 GB with MXFP4 for MoE blocks; attention/embeddings/router in BF16.
- **Inference stacks**: Transformers, vLLM (preferred for throughput and KV cache management), Ollama for consumer hardware.
- **Kernel advice**: Use fused dequant kernels for FP4+UE8 tiles in experts; keep QKV/O/Bias in BF16. Enable KV cache; benefit from sliding layers for long contexts.

### Recommended use-cases
- **Agentic tooling**: Function calling, constrained outputs, and tool/browse orchestration with low latency on a single high-end consumer GPU.
- **Long-context RAG and summarization**: Up to 128k tokens with periodic global attention for cross-chunk mixing.
- **Code and structured outputs**: Schema-constrained JSON/YAML, DSL parsing; strong fit for local dev assistants.
- **Domain-tuned assistants**: Lightweight adapters for support, knowledge bases, classification, and form-filling.
- **Batch generation/rewriting**: Copy generation, data cleanup, and templated transformations leveraging MoE throughput.

Provenance: Derived from `config.json`, `tokenizer_config.json`, `model.safetensors.index.json`, and existing docs in this repo.