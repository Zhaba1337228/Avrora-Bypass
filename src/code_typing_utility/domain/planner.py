from __future__ import annotations

import math
import random

from code_typing_utility.domain.models import TypingSettings


KEY_COORDINATES = {
    **{key: (index, 0) for index, key in enumerate("1234567890-=")},
    **{key: (index + 0.25, 1) for index, key in enumerate("qwertyuiop[]\\")},
    **{key: (index + 0.65, 2) for index, key in enumerate("asdfghjkl;'")},
    **{key: (index + 1.05, 3) for index, key in enumerate("zxcvbnm,./")},
    " ": (5.0, 4.0),
}


class KeystrokePlanner:
    """Creates reproducible, bounded intervals for a text sequence."""

    def __init__(self, settings: TypingSettings) -> None:
        settings.validate()
        self._settings = settings
        self._random = random.Random(settings.seed)
        self._base_delay = 60.0 / settings.characters_per_minute
        self._tempo = 1.0

    def delay_after(self, current: str, following: str | None) -> float:
        self._tempo = min(1.30, max(0.75, self._tempo + self._random.gauss(0, 0.018)))
        variation = self._settings.variation_percent / 100
        jitter = self._random.gauss(1.0, variation * 0.22)
        delay = self._base_delay * self._tempo * jitter * self._distance_factor(current, following)
        return max(0.018, delay + self._context_pause(current))

    @staticmethod
    def _distance_factor(current: str, following: str | None) -> float:
        if not following:
            return 1.0
        source = KEY_COORDINATES.get(current.lower())
        target = KEY_COORDINATES.get(following.lower())
        if source is None or target is None:
            return 1.08
        return min(1.35, 0.86 + math.dist(source, target) * 0.055)

    def _context_pause(self, current: str) -> float:
        ranges = {
            "\n": (0.12, 0.36),
            "\t": (0.035, 0.09),
            ".,;:": (0.045, 0.18),
            ")]}": (0.015, 0.06),
            " ": (0.0, 0.05),
        }
        for characters, (lower, upper) in ranges.items():
            if current in characters:
                return self._random.uniform(lower, upper)
        return 0.0
