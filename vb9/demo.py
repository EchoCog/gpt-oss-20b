"""Quick demonstration of the VB9 prototype."""
from __future__ import annotations

from .ide import VB9IDE
from . import styx

def main():
    ide = VB9IDE()
    expr = ide.designer("(widget (button ok) (textbox name))")
    ide.compiler(expr)
    ide.runtime()
    styx.send("(button ok click)")
    styx.send("(textbox name focus)")
    import time; time.sleep(0.3)
    for ev in styx.events():
        print(f"EVENT {ev.kind}: {ev.detail}")
    print("Last path:", styx.tread("/last/msg.path"))
    ide.stop()

if __name__ == "__main__":
    main()
