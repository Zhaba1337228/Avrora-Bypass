from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from code_typing_utility.domain.models import TypingSettings, TypingState, WorkerEvent, WorkerEventKind
from code_typing_utility.platforms.pynput_adapter import GlobalHotkeys, PynputInputBackend, check_platform
from code_typing_utility.services.text_loader import load_text, normalise_line_endings
from code_typing_utility.services.typing_worker import TypingWorker
from code_typing_utility.ui.animated_header import AnimatedHeader


class TypingApp(tk.Tk):
    BACKGROUND = "#0B1220"
    CARD = "#121D30"
    FIELD = "#0D1728"
    TEXT = "#EAF0FF"
    MUTED = "#95A6C6"
    ACCENT = "#66E3D0"
    DANGER = "#FF6B81"

    def __init__(self) -> None:
        super().__init__()
        self.title("Code Typing Studio")
        self.minsize(860, 650)
        self.geometry("1000x720")
        self.configure(bg=self.BACKGROUND)

        self._source_text = ""
        self._events: queue.Queue[WorkerEvent] = queue.Queue()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._worker: TypingWorker | None = None
        self._active_settings: TypingSettings | None = None
        self._state = TypingState.IDLE

        self._speed = tk.IntVar(value=220)
        self._countdown = tk.IntVar(value=3)
        self._variation = tk.IntVar(value=18)
        self._seed = tk.StringVar(value="")
        self._file_name = tk.StringVar(value="Файл не выбран")
        self._status = tk.StringVar(value="Загрузите файл и поставьте курсор в редактор.")
        self._progress_text = tk.StringVar(value="0 / 0")
        self._state_text = tk.StringVar(value=TypingState.IDLE.value)
        self._progress_value = tk.DoubleVar(value=0)

        self._configure_styles()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._hotkeys = GlobalHotkeys(lambda: self.after(0, self.toggle), lambda: self.after(0, self.stop_typing))
        self._hotkeys.start()
        self._show_platform_status()
        self.after(40, self._consume_events)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Accent.Horizontal.TProgressbar", troughcolor=self.FIELD, background=self.ACCENT, bordercolor=self.FIELD, lightcolor=self.ACCENT, darkcolor=self.ACCENT)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root = tk.Frame(self, bg=self.BACKGROUND)
        root.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        AnimatedHeader(root).grid(row=0, column=0, sticky="ew")
        body = tk.Frame(root, bg=self.BACKGROUND, padx=22, pady=18)
        body.grid(row=1, column=0, rowspan=2, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(2, weight=1)

        settings_card = self._card(body)
        settings_card.grid(row=0, column=0, sticky="ew")
        settings_card.columnconfigure(9, weight=1)
        tk.Label(settings_card, text="Настройки ритма", bg=self.CARD, fg=self.TEXT, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))
        self._field(settings_card, "Симв./мин", self._speed, 40, 600, 0, 1)
        self._field(settings_card, "Отсчёт, с", self._countdown, 0, 15, 2, 1)
        self._field(settings_card, "Разброс, %", self._variation, 0, 45, 4, 1)
        self._text_field(settings_card, "Seed", self._seed, 6, 1)
        tk.Label(settings_card, text="Оставьте seed пустым для нового сценария каждый запуск.", bg=self.CARD, fg=self.MUTED, font=("Segoe UI", 9)).grid(row=2, column=0, columnspan=9, sticky="w", padx=16, pady=(4, 14))

        action_row = tk.Frame(body, bg=self.BACKGROUND)
        action_row.grid(row=1, column=0, sticky="ew", pady=14)
        action_row.columnconfigure(1, weight=1)
        self._button(action_row, "Paste clipboard", self.load_clipboard, self.ACCENT, "#07151A").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self._button(action_row, "Загрузить код", self.load_file, self.ACCENT, "#07151A").grid(row=0, column=0, sticky="w")
        tk.Label(action_row, textvariable=self._file_name, bg=self.BACKGROUND, fg=self.MUTED, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=12)
        self._toggle_button = self._button(action_row, "Старт  F8", self.toggle, self.ACCENT, "#07151A")
        self._toggle_button.grid(row=0, column=2, padx=(12, 8))
        self._button(action_row, "Стоп  F9", self.stop_typing, self.DANGER, "#250D18").grid(row=0, column=3)

        preview_card = self._card(body)
        preview_card.grid(row=2, column=0, sticky="nsew")
        preview_card.columnconfigure(0, weight=1)
        preview_card.rowconfigure(1, weight=1)
        tk.Label(preview_card, text="Предпросмотр", bg=self.CARD, fg=self.TEXT, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))
        tk.Label(preview_card, text="Табуляция показана как →; при вводе отправляется исходный символ Tab.", bg=self.CARD, fg=self.MUTED, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="e", padx=16, pady=(14, 2))
        frame = tk.Frame(preview_card, bg=self.CARD)
        frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(10, 16))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self._preview = tk.Text(frame, wrap="none", state="disabled", bg=self.FIELD, fg="#DCE8FF", insertbackground=self.TEXT, relief="flat", padx=14, pady=12, font=("Cascadia Code", 10))
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self._preview.yview)
        self._preview.configure(yscrollcommand=scroll.set)
        self._preview.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        footer = tk.Frame(body, bg=self.BACKGROUND)
        footer.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        footer.columnconfigure(0, weight=1)
        tk.Label(footer, textvariable=self._status, bg=self.BACKGROUND, fg=self.MUTED, anchor="w", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="ew")
        tk.Label(footer, textvariable=self._state_text, bg=self.BACKGROUND, fg=self.ACCENT, font=("Segoe UI", 10, "bold")).grid(row=0, column=1, padx=(16, 0))
        ttk.Progressbar(footer, style="Accent.Horizontal.TProgressbar", maximum=100, variable=self._progress_value).grid(row=1, column=0, sticky="ew", pady=(8, 0))
        tk.Label(footer, textvariable=self._progress_text, bg=self.BACKGROUND, fg=self.MUTED, font=("Segoe UI", 9)).grid(row=1, column=1, padx=(16, 0))

    def _card(self, parent: tk.Misc) -> tk.Frame:
        return tk.Frame(parent, bg=self.CARD, highlightbackground="#1D2C46", highlightthickness=1)

    def _field(self, parent: tk.Misc, label: str, variable: tk.IntVar, minimum: int, maximum: int, column: int, row: int) -> None:
        tk.Label(parent, text=label, bg=self.CARD, fg=self.MUTED, font=("Segoe UI", 9)).grid(row=row, column=column, sticky="w", padx=(16 if column == 0 else 10, 4))
        spinbox = tk.Spinbox(parent, from_=minimum, to=maximum, textvariable=variable, width=6, bg=self.FIELD, fg=self.TEXT, buttonbackground="#273955", insertbackground=self.TEXT, relief="flat", font=("Segoe UI", 10))
        spinbox.grid(row=row, column=column + 1, sticky="w", padx=(0, 6))

    def _text_field(self, parent: tk.Misc, label: str, variable: tk.StringVar, column: int, row: int) -> None:
        tk.Label(parent, text=label, bg=self.CARD, fg=self.MUTED, font=("Segoe UI", 9)).grid(row=row, column=column, sticky="w", padx=(10, 4))
        tk.Entry(parent, textvariable=variable, width=12, bg=self.FIELD, fg=self.TEXT, insertbackground=self.TEXT, relief="flat", font=("Segoe UI", 10)).grid(row=row, column=column + 1, sticky="w")

    @staticmethod
    def _button(parent: tk.Misc, text: str, command: object, background: str, foreground: str) -> tk.Button:
        return tk.Button(parent, text=text, command=command, bg=background, fg=foreground, activebackground=background, activeforeground=foreground, relief="flat", bd=0, padx=15, pady=9, cursor="hand2", font=("Segoe UI", 10, "bold"))

    def _show_platform_status(self) -> None:
        check = check_platform()
        self._status.set(check.message if check.supported else f"Недоступно: {check.message}")

    def load_file(self) -> None:
        selected = filedialog.askopenfilename(filetypes=[("Код и текст", "*.txt *.py *.js *.ts *.json *.md *.html *.css *.java *.c *.cpp"), ("Все файлы", "*.*")])
        if not selected:
            return
        path = Path(selected)
        try:
            self._source_text = load_text(path)
        except (OSError, UnicodeDecodeError) as error:
            messagebox.showerror("Не удалось загрузить файл", str(error))
            return
        visible = normalise_line_endings(self._source_text).replace("\t", "→   ")
        self._preview.configure(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", visible)
        self._preview.configure(state="disabled")
        self._file_name.set(f"{path.name} • {len(self._source_text)} символов")
        self._progress_value.set(0)
        self._progress_text.set(f"0 / {len(self._source_text)}")
        self._status.set("Файл готов. Поставьте курсор в редактор и нажмите F8.")

    def load_clipboard(self) -> None:
        try:
            text = self.clipboard_get()
        except tk.TclError:
            messagebox.showinfo("Clipboard is empty", "There is no text in the clipboard.")
            return
        if not text:
            messagebox.showinfo("Clipboard is empty", "There is no text in the clipboard.")
            return
        self._source_text = text
        visible = normalise_line_endings(text).replace("\t", "\u2192   ")
        self._preview.configure(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", visible)
        self._preview.configure(state="disabled")
        self._file_name.set(f"Clipboard \u2022 {len(text)} symbols")
        self._progress_value.set(0)
        self._progress_text.set(f"0 / {len(text)}")
        self._status.set("Clipboard text is ready. Focus the target editor and press F8.")

    def toggle(self) -> None:
        if self._state in (TypingState.IDLE, TypingState.ERROR):
            self.start_typing()
        elif self._state is TypingState.PAUSED:
            self._pause_event.clear()
            self._set_state(TypingState.RUNNING, "Ввод продолжен. F8 — пауза, F9 — стоп.")
        elif self._state in (TypingState.COUNTDOWN, TypingState.RUNNING):
            self._pause_event.set()
            self._set_state(TypingState.PAUSED, "Пауза. F8 — продолжить, F9 — стоп.")

    def start_typing(self) -> None:
        if not self._source_text:
            messagebox.showinfo("Нет текста", "Сначала загрузите файл с кодом или текстом.")
            return
        check = check_platform()
        if not check.supported:
            messagebox.showerror("Ввод недоступен", check.message)
            return
        try:
            settings = TypingSettings(self._speed.get(), self._countdown.get(), self._variation.get(), int(self._seed.get()) if self._seed.get().strip() else None)
            settings.validate()
        except (tk.TclError, ValueError) as error:
            messagebox.showerror("Некорректные настройки", str(error))
            return
        self._stop_event.clear()
        self._pause_event.clear()
        self._active_settings = settings
        self._worker = TypingWorker(self._source_text, settings, self._events, PynputInputBackend, self._stop_event, self._pause_event)
        self._set_state(TypingState.COUNTDOWN, f"Отсчёт: {settings.countdown_seconds} с. Переведите фокус в целевой редактор.")
        self._worker.start()

    def stop_typing(self) -> None:
        if self._state in (TypingState.COUNTDOWN, TypingState.RUNNING, TypingState.PAUSED):
            self._stop_event.set()
            self._pause_event.clear()
            self._set_state(TypingState.IDLE, "Остановка запрошена. Новые клавиши больше не отправляются.")

    def _consume_events(self) -> None:
        try:
            while True:
                self._handle_event(self._events.get_nowait())
        except queue.Empty:
            pass
        self.after(40, self._consume_events)

    def _handle_event(self, event: WorkerEvent) -> None:
        if event.kind is WorkerEventKind.COUNTDOWN:
            remaining = int(event.message)
            self._set_state(TypingState.RUNNING if remaining == 0 else TypingState.COUNTDOWN, "Ввод начался. F8 — пауза, F9 — стоп." if remaining == 0 else f"Отсчёт: {remaining} с. Переведите фокус в целевой редактор.")
        elif event.kind is WorkerEventKind.PROGRESS:
            self._update_progress(event.completed, event.total)
        elif event.kind is WorkerEventKind.FINISHED:
            self._set_state(TypingState.IDLE, "Ввод завершён.")
        elif event.kind is WorkerEventKind.STOPPED:
            self._set_state(TypingState.IDLE, "Ввод остановлен.")
        elif event.kind is WorkerEventKind.ERROR:
            self._set_state(TypingState.ERROR, f"Ошибка ввода: {event.message}")
            messagebox.showerror("Ошибка ввода", event.message)

    def _update_progress(self, completed: int, total: int) -> None:
        percent = completed / total * 100 if total else 0
        self._progress_value.set(percent)
        remaining_text = ""
        if self._active_settings:
            seconds = max(0, round((total - completed) * 60 / self._active_settings.characters_per_minute))
            remaining_text = f" • ≈ {seconds // 60}:{seconds % 60:02d} осталось"
        self._progress_text.set(f"{completed} / {total}{remaining_text}")

    def _set_state(self, state: TypingState, message: str) -> None:
        self._state = state
        self._status.set(message)
        self._state_text.set(state.value)
        labels = {
            TypingState.IDLE: "Старт  F8",
            TypingState.COUNTDOWN: "Пауза  F8",
            TypingState.RUNNING: "Пауза  F8",
            TypingState.PAUSED: "Продолжить  F8",
            TypingState.ERROR: "Повторить  F8",
        }
        self._toggle_button.configure(text=labels[state])

    def _close(self) -> None:
        self._stop_event.set()
        self._hotkeys.stop()
        self.destroy()


def run() -> None:
    TypingApp().mainloop()
