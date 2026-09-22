import queue
import threading
import unittest

from code_typing_utility.domain.models import TypingSettings, WorkerEventKind
from code_typing_utility.services.typing_worker import TypingWorker


class CaptureBackend:
    def __init__(self) -> None:
        self.characters: list[str] = []

    def type_character(self, character: str) -> None:
        self.characters.append(character)


class TypingWorkerTests(unittest.TestCase):
    def test_worker_normalises_line_endings_and_emits_finished(self) -> None:
        backend = CaptureBackend()
        events: queue.Queue = queue.Queue()
        worker = TypingWorker(
            "a\t= 1\r\n",
            TypingSettings(600, 0, 0, seed=1),
            events,
            lambda: backend,
            threading.Event(),
            threading.Event(),
        )

        worker.run()

        self.assertEqual(backend.characters, ["a", "\t", "=", " ", "1", "\n"])
        collected = [events.get_nowait() for _ in range(events.qsize())]
        self.assertEqual(collected[-1].kind, WorkerEventKind.FINISHED)
