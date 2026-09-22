from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable

from code_typing_utility.domain.models import TypingSettings, WorkerEvent, WorkerEventKind
from code_typing_utility.domain.planner import KeystrokePlanner
from code_typing_utility.services.text_loader import normalise_line_endings


class TypingWorker(threading.Thread):
    """Sends planned key events without ever blocking the Tkinter thread."""

    def __init__(
        self,
        text: str,
        settings: TypingSettings,
        events: queue.Queue[WorkerEvent],
        backend_factory: Callable[[], object],
        stop_event: threading.Event,
        pause_event: threading.Event,
    ) -> None:
        super().__init__(daemon=True)
        self._text = normalise_line_endings(text)
        self._settings = settings
        self._events = events
        self._backend_factory = backend_factory
        self._stop_event = stop_event
        self._pause_event = pause_event

    def run(self) -> None:
        try:
            if not self._run_countdown():
                self._emit(WorkerEventKind.STOPPED)
                return
            backend = self._backend_factory()
            planner = KeystrokePlanner(self._settings)
            total = len(self._text)
            for index, character in enumerate(self._text):
                if not self._wait_until_active():
                    self._emit(WorkerEventKind.STOPPED)
                    return
                backend.type_character(character)
                self._emit(WorkerEventKind.PROGRESS, index + 1, total)
                following = self._text[index + 1] if index + 1 < total else None
                if not self._wait_delay(planner.delay_after(character, following)):
                    self._emit(WorkerEventKind.STOPPED)
                    return
            self._emit(WorkerEventKind.FINISHED)
        except Exception as error:
            self._emit(WorkerEventKind.ERROR, message=str(error))

    def _run_countdown(self) -> bool:
        for seconds_left in range(self._settings.countdown_seconds, 0, -1):
            if self._stop_event.wait(1):
                return False
            self._emit(WorkerEventKind.COUNTDOWN, message=str(seconds_left - 1))
        return not self._stop_event.is_set()

    def _wait_until_active(self) -> bool:
        while self._pause_event.is_set():
            if self._stop_event.wait(0.05):
                return False
        return not self._stop_event.is_set()

    def _wait_delay(self, delay: float) -> bool:
        deadline = time.monotonic() + delay
        while time.monotonic() < deadline:
            if not self._wait_until_active():
                return False
            self._stop_event.wait(min(0.02, max(0.0, deadline - time.monotonic())))
        return not self._stop_event.is_set()

    def _emit(self, kind: WorkerEventKind, completed: int = 0, total: int = 0, message: str = "") -> None:
        self._events.put(WorkerEvent(kind, completed, total, message))
