"""High-level VB9 IDE orchestrator.

Enhancements in this iteration:
    * Logic-inspired proof tree extraction from S-expression structure
    * Kernel caching (skip emission if unchanged hash present)
    * Manifest export `/form/manifest.json` with kernels + proof_tree
"""
from __future__ import annotations

import json
import threading
from typing import Any, Optional, Dict, List

from . import styx, sexp, glyph

class VB9IDE:
    def __init__(self) -> None:
        self._runtime_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._kernel_cache: Dict[str, str] = {}

    def designer(self, form_src: str):  # type: ignore[override]
        expr = sexp.parse(form_src)
        bitmap = glyph.sexp_to_bitmap(expr)
        styx.twrite("/dev/draw", bitmap)
        styx.twrite("/form/source.scm", form_src)
        dims = (len(bitmap), len(bitmap[0]) if bitmap else 0)
        styx.log("designer", f"bitmap {dims[0]}x{dims[1]}")
        return expr

    def _proof_tree(self, expr: Any) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []

        def walk(node: Any) -> None:
            if isinstance(node, tuple) and node:
                head = node[0]
                deps = [
                    c[0] if isinstance(c, tuple) and c else c
                    for c in node[1:]
                ]
                edges.append({"node": head, "deps": deps})
                for c in node[1:]:
                    walk(c)

        walk(expr)
        # Deduplicate by (node, deps) order
        uniq: list[Dict[str, Any]] = []
        seen = set()
        for e in edges:
            key = (e["node"], tuple(e["deps"]))
            if key not in seen:
                seen.add(key)
                uniq.append(e)
        return uniq

    def compiler(self, expr: Any):  # type: ignore[override]
        symbols = glyph.extract_glyphs(expr)
        kernels: List[Dict[str, Any]] = []
        for sym in symbols:
            meta = glyph.backpropagate_glyph(sym)
            name = glyph.kernel_name(meta)
            prior = self._kernel_cache.get(name)
            kernel_path = f"/form/{name}.kernel"
            if prior == meta["hash"] and styx.tread(kernel_path) is not None:
                styx.log("compiler-skip", name)
            else:
                styx.twrite(kernel_path, glyph.kernel_to_bytecode(meta))
                styx.log("compiler", f"emit {name}")
                self._kernel_cache[name] = meta["hash"]
            kernels.append(meta)

        manifest = {
            "kernels": kernels,
            "proof_tree": self._proof_tree(expr),
        }
        styx.twrite("/form/manifest.json", json.dumps(manifest, indent=2))
        return kernels

    def _runtime_loop(self):  # pragma: no cover - timing dependent
        styx.log("runtime", "start")
        while not self._stop.is_set():
            msg = styx.recv(timeout=0.1)
            if msg is None:
                continue
            try:
                expr = sexp.parse(msg)
            except Exception as e:
                styx.log("runtime-error", str(e))
                continue
            path = sexp.sexp_to_path(expr)
            styx.twrite("/last/msg.path", path)
            styx.log("runtime-msg", path)

    def runtime(self, mount_src: str = "/form", mount_point: str = "/mnt/app"):
        styx.mount(mount_src, mount_point)
        if self._runtime_thread and self._runtime_thread.is_alive():
            return
        self._stop.clear()
        self._runtime_thread = threading.Thread(
            target=self._runtime_loop,
            daemon=True,
        )
        self._runtime_thread.start()

    def stop(self):
        self._stop.set()
        if self._runtime_thread:
            self._runtime_thread.join(timeout=1)
