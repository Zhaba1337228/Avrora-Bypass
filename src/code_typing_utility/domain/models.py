from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TypingState(str, Enum):
    IDLE = "Готово"
    COUNTDOWN = "Отсчёт"
    RUNNING = "Ввод"
    PAUSED = "Пауза"
    ERROR = "Ошибка"


class WorkerEventKind(str, Enum):
    COUNTDOWN = "countdown"
    PROGRESS = "progress"
    FINISHED = "finished"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True)
class TypingSettings:
    characters_per_minute: int
    countdown_seconds: int
    variation_percent: int
    seed: int | None = None

    def validate(self) -> None:
        if not 40 <= self.characters_per_minute <= 600:
            raise ValueError("Скорость должна быть в диапазоне 40–600 символов в минуту.")
        if not 0 <= self.countdown_seconds <= 15:
            raise ValueError("Отсчёт должен быть в диапазоне 0–15 секунд.")
        if not 0 <= self.variation_percent <= 45:
            raise ValueError("Разброс должен быть в диапазоне 0–45 %.")


@dataclass(frozen=True)
class WorkerEvent:
    kind: WorkerEventKind
    completed: int = 0
    total: int = 0
    message: str = ""
