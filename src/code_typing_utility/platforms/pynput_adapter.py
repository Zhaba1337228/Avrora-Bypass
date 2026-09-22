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
        return PlatformCheck(True, "macOS: перед вводом предоставьте приложению доступ Accessibility.")
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
