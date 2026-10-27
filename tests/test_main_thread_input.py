import threading
import time
import unittest

from code_typing_utility.platforms.main_thread_input import MainThreadInput


class MainThreadInputTests(unittest.TestCase):
    def test_backend_created_and_called_on_draining_thread(self):
        calls = []
        main_id = threading.get_ident()
        class Backend:
            def __init__(self):
                calls.append(("create", threading.get_ident()))
            def type_character(self, char):
                calls.append((char, threading.get_ident()))
        dispatcher = MainThreadInput(Backend, threading.Event())
        worker = threading.Thread(target=dispatcher.type_character, args=("x",))
        worker.start()
        deadline = time.monotonic() + 2
        while worker.is_alive() and time.monotonic() < deadline:
            dispatcher.drain()
            worker.join(0.01)
        self.assertFalse(worker.is_alive())
        self.assertEqual(calls, [("create", main_id), ("x", main_id)])

    def test_exception_is_returned_to_worker(self):
        errors = []
        class Backend:
            def type_character(self, char):
                raise ValueError("failure")
        dispatcher = MainThreadInput(Backend, threading.Event())
        def run():
            try:
                dispatcher.type_character("x")
            except ValueError as error:
                errors.append(str(error))
        worker = threading.Thread(target=run)
        worker.start()
        deadline = time.monotonic() + 2
        while worker.is_alive() and time.monotonic() < deadline:
            dispatcher.drain()
            worker.join(0.01)
        self.assertEqual(errors, ["failure"])
        self.assertFalse(worker.is_alive())

    def test_stop_discards_pending_input(self):
        stop = threading.Event()
        calls = []
        dispatcher = MainThreadInput(lambda: calls.append("created"), stop)
        worker = threading.Thread(target=dispatcher.type_character, args=("x",))
        worker.start()
        stop.set()
        dispatcher.drain()
        worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertEqual(calls, [])
