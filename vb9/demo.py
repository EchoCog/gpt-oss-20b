"""Quick demonstration of the VB9 prototype with proof manifest."""
from __future__ import annotations

import time
from .ide import VB9IDE
from . import styx, glyph


def main() -> None:
    ide = VB9IDE()
    expr = ide.designer("(widget (button ok) (textbox name))")
    ide.compiler(expr)
    ide.runtime()
    styx.send("(button ok click)")
    styx.send("(textbox name focus)")
    time.sleep(0.25)
    # Display events
    for ev in styx.events():
        print(f"EVENT {ev.kind}: {ev.detail}")
    print("Last path:", styx.tread("/last/msg.path"))
    print("Manifest:\n", styx.tread("/form/manifest.json"))
    # Show a tiny convolution sample
    bitmap = styx.tread("/dev/draw")
    conv = glyph.convolve(bitmap) if bitmap else []
    if conv:
        print("Convolution sample (first 3 rows):", conv[:3])
    ide.stop()


if __name__ == "__main__":  # pragma: no cover
    main()
