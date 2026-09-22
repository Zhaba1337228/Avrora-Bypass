from __future__ import annotations

import math
import tkinter as tk


class AnimatedHeader(tk.Canvas):
    """A small Canvas animation that keeps the UI lively without dependencies."""

    BACKGROUND = "#101827"
    ACCENT = "#66E3D0"
    MUTED = "#8EA2C2"

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, height=118, highlightthickness=0, bg=self.BACKGROUND)
        self._phase = 0.0
        self.bind("<Configure>", lambda _: self._draw())
        self.after(32, self._tick)

    def _tick(self) -> None:
        self._phase += 0.055
        self._draw()
        self.after(32, self._tick)

    def _draw(self) -> None:
        width = max(self.winfo_width(), 760)
        self.delete("scene")
        self.create_rectangle(0, 0, width, 118, fill=self.BACKGROUND, outline="", tags="scene")
        self.create_text(28, 39, anchor="w", text="CODE TYPING STUDIO", fill="#F5F8FF", font=("Segoe UI", 20, "bold"), tags="scene")
        self.create_text(29, 69, anchor="w", text="Local paced input • F8 pause / resume • F9 stop", fill=self.MUTED, font=("Segoe UI", 10), tags="scene")
        start_x = width - 170
        for index in range(4):
            wave = (math.sin(self._phase + index * 0.9) + 1) / 2
            radius = 8 + wave * 10
            x = start_x + index * 38
            y = 59 + math.sin(self._phase * 0.8 + index) * 11
            color = self.ACCENT if index % 2 == 0 else "#4E89FF"
            self.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline="", tags="scene")
