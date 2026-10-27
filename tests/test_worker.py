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

    def clear_auto_indent(self) -> None:
        self.characters.append("<clear-indent>")


class SimulatedEditor:
    def __init__(self) -> None:
        self.lines = [""]

    def type_character(self, character: str) -> None:
        if character == "\n":
            previous = self.lines[-1]
            indent = previous[:len(previous) - len(previous.lstrip(" \t"))]
            self.lines.append(indent + ("    " if previous.rstrip().endswith(":") else ""))
        else:
            self.lines[-1] += character

    def clear_auto_indent(self) -> None:
        self.lines[-1] = ""


class TypingWorkerTests(unittest.TestCase):
    def test_auto_indent_mode_preserves_source_and_clears_after_each_enter(self) -> None:
        backend = CaptureBackend()
        text = "root\n\t child\n\n  end\n"
        worker = TypingWorker(text, TypingSettings(600, 0, 0, seed=1, compensate_auto_indent=True),
                              queue.Queue(), lambda: backend, threading.Event(), threading.Event())
        worker._wait_delay = lambda delay: True
        worker.run()
        expected = []
        for character in text:
            expected.append(character)
            if character == "\n":
                expected.append("<clear-indent>")
        self.assertEqual(backend.characters, expected)

    def test_auto_indent_with_simulated_editor(self) -> None:
        source = "root:\n\tchild:\n\t  nested\n\n  dedent\nend\n"
        editor = SimulatedEditor()
        worker = TypingWorker(source, TypingSettings(600, 0, 0, compensate_auto_indent=True),
                              queue.Queue(), lambda: editor, threading.Event(), threading.Event())
        worker._wait_delay = lambda delay: True
        worker.run()
        self.assertEqual("\n".join(editor.lines), source)

    def test_stopped_worker_does_not_send_keys(self) -> None:
        backend = CaptureBackend()
        stop = threading.Event()
        stop.set()
        worker = TypingWorker("a\n", TypingSettings(600, 0, 0, compensate_auto_indent=True),
                              queue.Queue(), lambda: backend, stop, threading.Event())
        worker.run()
        self.assertEqual(backend.characters, [])

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
