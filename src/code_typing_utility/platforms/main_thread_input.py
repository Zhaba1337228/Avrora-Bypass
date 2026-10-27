from __future__ import annotations

import queue
import threading
from collections.abc import Callable


class MainThreadInput:
    """Run backend operations on the thread that drains the queue."""

    def __init__(self, factory: Callable[[], object], stop_event: threading.Event) -> None:
        self._factory = factory
        self._stop_event = stop_event
        self._requests: queue.Queue = queue.Queue()
        self._backend = None

    def _call(self, name: str, *args: object) -> None:
        done = threading.Event()
        result: list[Exception] = []
        self._requests.put((name, args, done, result))
        while not done.wait(0.05):
            if self._stop_event.is_set():
                return
        if result:
            raise result[0]

    def type_character(self, character: str) -> None:
        self._call("type_character", character)

    def clear_auto_indent(self) -> None:
        self._call("clear_auto_indent")

    def drain(self) -> None:
        while True:
            try:
                name, args, done, result = self._requests.get_nowait()
            except queue.Empty:
                return
            try:
                if not self._stop_event.is_set():
                    if self._backend is None:
                        self._backend = self._factory()
                    getattr(self._backend, name)(*args)
            except Exception as error:
                result.append(error)
            finally:
                done.set()
