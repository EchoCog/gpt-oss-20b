"""In-memory Styx / 9P flavored façade.

This is NOT a full 9P implementation; we only model:
 - twrite(path, data)
 - tread(path) -> data
 - mount(src, mountpoint)
 - recv() / send(msg) for a simplistic message channel

All operations are synchronous and single-process for demonstration.
"""
from __future__ import annotations

from dataclasses import dataclass
from queue import Queue, Empty
from threading import Lock
from typing import Dict, Any, Optional

_fs: Dict[str, Any] = {}
_mounts: Dict[str, str] = {}
_lock = Lock()
_msg_queue: "Queue[str]" = Queue()

def _norm(path: str) -> str:
    """Normalize a filesystem-like path."""
    if not path.startswith("/"):
        path = "/" + path
    while "//" in path:
        path = path.replace("//", "/")
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return path

def twrite(path: str, data: Any) -> None:
    """Transactional write (best-effort atomic for this toy model)."""
    path = _norm(path)
    with _lock:
        _fs[path] = data

def tread(path: str) -> Any:
    path = _norm(path)
    with _lock:
        return _fs.get(path)

def exists(path: str) -> bool:
    return tread(path) is not None

def mount(src: str, mountpoint: str) -> None:
    src = _norm(src)
    mountpoint = _norm(mountpoint)
    with _lock:
        _mounts[mountpoint] = src

def send(msg: str) -> None:
    _msg_queue.put(msg)

def recv(timeout: Optional[float] = None) -> Optional[str]:
    try:
        return _msg_queue.get(timeout=timeout)
    except Empty:
        return None

@dataclass
class Event:
    kind: str
    detail: str

_events: list[Event] = []

def log(kind: str, detail: str) -> None:
    _events.append(Event(kind, detail))

def events() -> list[Event]:
    return list(_events)
