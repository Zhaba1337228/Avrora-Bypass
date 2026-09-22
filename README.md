<div align="center">

# Avrora MIREA Bypass

### Сделано студентом для студентов

Локальная утилита для обхода вставки в приложение Avrora

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
![Platforms](https://img.shields.io/badge/Platforms-Windows%20%7C%20macOS%20%7C%20Linux-66E3D0)
![UI](https://img.shields.io/badge/UI-Tkinter-4E89FF)
![License](https://img.shields.io/badge/Status-MVP-FFB86B)

</div>

---

## Что умеет

| Функция | Как работает |
| --- | --- |
| Загрузка кода | Сохраняет текст, пробелы, табуляции, пустые строки и переносы. |
| Управление | `F8` запускает, ставит на паузу и продолжает ввод. `F9` останавливает сразу. |
| Ритм ввода | Базовая скорость, плавное изменение темпа, расстояние между клавишами и паузы в синтаксисе. |
| Контроль | Отсчёт перед стартом, прогресс и примерное время до окончания. |
| Интерфейс | Тёмная тема, предпросмотр с видимыми табуляциями. |

## Быстрый старт

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run.ps1
```

### macOS / Linux

```bash
bash scripts/run.sh
```

### Ручной запуск

```bash
python -m pip install -e .
python -m code_typing_utility
```

Скрипты сами создают `.venv`, ставят зависимости и открывают приложение.

## Как пользоваться

```text
Загрузить файл → настроить ритм → поставить курсор в редактор → нажать F8
```

1. Нажмите **«Загрузить код»** и выберите текстовый файл.
2. Укажите скорость, отсчёт и разброс ритма.
3. Поставьте курсор в нужное текстовое поле.
4. Нажмите `F8` и за время отсчёта вернитесь в редактор.
5. Нажмите `F8`, чтобы поставить ввод на паузу, или `F9`, чтобы остановить его.

## Горячие клавиши

| Клавиша | Действие |
| --- | --- |
| `F8` | Старт / пауза / продолжение |
| `F9` | Немедленная остановка |

## Сборка приложения

| Платформа | Команда | Результат |
| --- | --- | --- |
| Windows | `powershell -ExecutionPolicy Bypass -File scripts/build.ps1` | `dist/CodeTypingStudio.exe` |
| macOS / Linux | `bash scripts/build.sh` | приложение в `dist/` текущей ОС |

Сборку выполняют на целевой платформе: Windows-версию собирают на Windows, macOS-версию — на macOS, Linux-версию — на Linux.

## Поддержка платформ

| ОС | Статус | Детали |
| --- | --- | --- |
| Windows | ✅ Поддерживается | Системные события через `pynput`. |
| macOS | ✅ Поддерживается | Перед первым вводом выдайте приложению разрешение **Accessibility**. |
| Linux X11 | ✅ Поддерживается | Используется X11 backend `pynput`. |
| Linux Wayland | ⏳ В планах | Нужен отдельный backend через desktop portals. |

## Архитектура

```text
src/code_typing_utility/
├── domain/       # настройки, состояния, расчёт задержек
├── services/     # загрузка текста и фоновый поток ввода
├── platforms/    # системный ввод и глобальные клавиши
└── ui/           # Tkinter-окно и Canvas-анимация

scripts/          # запуск и сборка для Windows / macOS / Linux
tests/            # unit-тесты без реального системного ввода
```

```text
UI → TypingWorker → KeystrokePlanner → PynputInputBackend → active window
```

`domain` не зависит от UI и ОС, поэтому модель задержек тестируется отдельно. `platforms` изолирует системный ввод, а `ui` отвечает только за окно и отображение состояния.

## Проверка

```bash
python -m unittest discover -s tests -v
python -m py_compile main.py
```

В тестах системный ввод заменён capture-backend, поэтому тестовый прогон не отправляет текст в активное окно.

---

<div align="center">

Built with Python, Tkinter and `pynput`.

</div>
