import sys
import types
import unittest
from unittest.mock import Mock, patch

from code_typing_utility.platforms.pynput_adapter import MacHotkeys, PynputInputBackend


class MacHotkeysTests(unittest.TestCase):
    def test_raw_keycodes_and_cleanup(self):
        quartz = types.SimpleNamespace(
            kCGEventTapDisabledByTimeout=-1, kCGEventTapDisabledByUserInput=-2,
            kCGEventKeyDown=10, kCGKeyboardEventKeycode=9, kCGSessionEventTap=1,
            kCGHeadInsertEventTap=0, kCGEventTapOptionListenOnly=1,
            CGEventTapCreate=Mock(return_value="tap"), CGEventTapEnable=Mock(),
            CGEventGetIntegerValueField=lambda event, field: event)
        core = types.SimpleNamespace(CFMachPortCreateRunLoopSource=Mock(return_value="source"),
            CFRunLoopAddSource=Mock(), CFRunLoopRemoveSource=Mock(),
            CFRunLoopGetMain=Mock(return_value="main"), kCFRunLoopCommonModes="common")
        calls = []
        with patch.dict(sys.modules, {"Quartz": quartz, "CoreFoundation": core}):
            hotkeys = MacHotkeys(lambda: calls.append("start"), lambda: calls.append("stop"))
            hotkeys.start()
            self.assertEqual(hotkeys._callback(None, 10, 100, None), 100)
            hotkeys._callback(None, 10, 101, None)
            hotkeys._callback(None, 10, 30, None)
            hotkeys.stop()
        self.assertEqual(calls, ["start", "stop"])
        core.CFRunLoopAddSource.assert_called_once_with("main", "source", "common")
        core.CFRunLoopRemoveSource.assert_called_once_with("main", "source", "common")

    def test_unavailable_event_tap_reports_error(self):
        quartz = types.SimpleNamespace(kCGSessionEventTap=1, kCGHeadInsertEventTap=0,
            kCGEventTapOptionListenOnly=1, kCGEventKeyDown=10, CGEventTapCreate=lambda *args: None)
        with patch.dict(sys.modules, {"Quartz": quartz, "CoreFoundation": types.SimpleNamespace()}):
            with self.assertRaisesRegex(RuntimeError, "Input Monitoring"):
                MacHotkeys(lambda: None, lambda: None).start()

    def test_mac_indent_selects_with_command_shift_left(self):
        from contextlib import nullcontext
        controller = Mock()
        controller.pressed.return_value = nullcontext()
        backend = PynputInputBackend.__new__(PynputInputBackend)
        backend._controller = controller
        with patch("code_typing_utility.platforms.pynput_adapter.platform.system", return_value="Darwin"):
            backend.clear_auto_indent()
        from code_typing_utility.platforms.pynput_adapter import keyboard
        controller.pressed.assert_called_once_with(keyboard.Key.shift, keyboard.Key.cmd)
        controller.press.assert_any_call(keyboard.Key.left)
