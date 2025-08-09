"""High-level VB9 IDE orchestrator."""
from __future__ import annotations

import threading
from typing import Any, Optional

from . import styx, sexp, glyph

class VB9IDE:
    def __init__(self):
        self._runtime_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def designer(self, form_src: str):
        expr = sexp.parse(form_src)
        bitmap = glyph.sexp_to_bitmap(expr)
        styx.twrite("/dev/draw", bitmap)
        styx.twrite("/form/source.scm", form_src)
        styx.log("designer", f"bitmap {len(bitmap)}x{len(bitmap[0]) if bitmap else 0}")
        return expr

    def compiler(self, expr: Any):
        symbols = glyph.extract_glyphs(expr)
        kernels = [glyph.backpropagate_glyph(s) for s in symbols]
        for k in kernels:
            name = glyph.kernel_name(k)
            styx.twrite(f"/form/{name}.kernel", glyph.kernel_to_bytecode(k))
            styx.log("compiler", f"emit {name}")
        return kernels

    def _runtime_loop(self):
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
        self._runtime_thread = threading.Thread(target=self._runtime_loop, daemon=True)
        self._runtime_thread.start()

    def stop(self):
        self._stop.set()
        if self._runtime_thread:
            self._runtime_thread.join(timeout=1)
