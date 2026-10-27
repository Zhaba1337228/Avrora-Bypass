from __future__ import annotations

import os
import platform
import time
from collections.abc import Callable
from dataclasses import dataclass

try:
    from pynput import keyboard
except ImportError as error:  # shown by the application when used
    keyboard = None
    PYNPUT_ERROR = error
else:
    PYNPUT_ERROR = None


@dataclass(frozen=True)
class PlatformCheck:
    supported: bool
    message: str


def check_platform() -> PlatformCheck:
    if keyboard is None:
        return PlatformCheck(False, f"Не установлен pynput: {PYNPUT_ERROR}")
    if platform.system() == "Linux" and os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        return PlatformCheck(False, "Wayland требует отдельного backend через desktop portals. Запустите приложение в X11-сеансе.")
    if platform.system() == "Darwin":
        try:
            from ApplicationServices import AXIsProcessTrusted
            if not AXIsProcessTrusted():
                return PlatformCheck(False, "macOS: разрешите приложению или Terminal доступ в Privacy & Security → Accessibility.")
        except ImportError:
            return PlatformCheck(False, "macOS: не удалось проверить разрешение Accessibility (ApplicationServices недоступен).")
        return PlatformCheck(True, "macOS: Accessibility разрешён; для F8/F9 может понадобиться Input Monitoring.")
    return PlatformCheck(True, "Системный ввод доступен.")


class PynputInputBackend:
    def __init__(self) -> None:
        check = check_platform()
        if not check.supported:
            raise RuntimeError(check.message)
        self._controller = keyboard.Controller()

    def type_character(self, character: str) -> None:
        special = {"\n": keyboard.Key.enter, "\t": keyboard.Key.tab}
        key = special.get(character, character)
        self._controller.press(key)
        self._controller.release(key)


    def clear_auto_indent(self) -> None:
        if platform.system() == "Darwin":
            with self._controller.pressed(keyboard.Key.shift, keyboard.Key.cmd):
                self._controller.press(keyboard.Key.left)
                self._controller.release(keyboard.Key.left)
        else:
            with self._controller.pressed(keyboard.Key.shift):
                self._controller.press(keyboard.Key.home)
                self._controller.release(keyboard.Key.home)
        # A space replaces the selection even when it is empty; removing it avoids
        # Backspace joining lines when there was no automatic indentation.
        self._controller.press(" ")
        self._controller.release(" ")
        self._controller.press(keyboard.Key.backspace)
        self._controller.release(keyboard.Key.backspace)


class GlobalHotkeys:
    """F8 toggles typing and F9 stops it; held keys are debounced."""

    def __init__(self, on_toggle: Callable[[], None], on_stop: Callable[[], None]) -> None:
        self._on_toggle = on_toggle
        self._on_stop = on_stop
        self._listener: keyboard.Listener | None = None
        self._last_press: dict[object, float] = {}

    def start(self) -> None:
        check = check_platform()
        if not check.supported:
            return

        def on_press(key: keyboard.Key | keyboard.KeyCode) -> None:
            now = time.monotonic()
            if now - self._last_press.get(key, 0.0) < 0.25:
                return
            self._last_press[key] = now
            if key == keyboard.Key.f8:
                self._on_toggle()
            elif key == keyboard.Key.f9:
                self._on_stop()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()


class MacHotkeys:
    """Observe F8/F9 on the main run loop without pynput key translation."""

    def __init__(self, on_toggle: Callable[[], None], on_stop: Callable[[], None]) -> None:
        self._callbacks = {100: on_toggle, 101: on_stop}
        self._tap = None
        self._source = None
        self._last_press: dict[int, float] = {}

    def start(self) -> None:
        import Quartz
        import CoreFoundation

        def callback(proxy: object, event_type: int, event: object, refcon: object) -> object:
            if event_type in (Quartz.kCGEventTapDisabledByTimeout, Quartz.kCGEventTapDisabledByUserInput):
                Quartz.CGEventTapEnable(self._tap, True)
            elif event_type == Quartz.kCGEventKeyDown:
                keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
                now = time.monotonic()
                if keycode in self._callbacks and now - self._last_press.get(keycode, 0.0) >= 0.25:
                    self._last_press[keycode] = now
                    self._callbacks[keycode]()
            return event

        self._callback = callback
        self._tap = Quartz.CGEventTapCreate(Quartz.kCGSessionEventTap, Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly, 1 << Quartz.kCGEventKeyDown, callback, None)
        if self._tap is None:
            raise RuntimeError("Не удалось включить F8/F9. Разрешите Input Monitoring для приложения или Terminal и перезапустите его.")
        self._source = CoreFoundation.CFMachPortCreateRunLoopSource(None, self._tap, 0)
        CoreFoundation.CFRunLoopAddSource(CoreFoundation.CFRunLoopGetMain(), self._source, CoreFoundation.kCFRunLoopCommonModes)
        Quartz.CGEventTapEnable(self._tap, True)

    def stop(self) -> None:
        if self._tap is not None:
            import Quartz
            import CoreFoundation
            Quartz.CGEventTapEnable(self._tap, False)
            CoreFoundation.CFRunLoopRemoveSource(CoreFoundation.CFRunLoopGetMain(), self._source, CoreFoundation.kCFRunLoopCommonModes)
            self._tap = None
