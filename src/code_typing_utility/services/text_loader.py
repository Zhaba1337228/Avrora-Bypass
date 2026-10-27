from pathlib import Path


def load_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("text", raw, 0, min(len(raw), 1), "Поддерживаются UTF-8 и CP1251")


def normalise_line_endings(text: str) -> str:
    """Produce one Enter event for CRLF, CR and LF line endings."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def leading_spaces_to_tabs(text: str, width: int) -> str:
    """Replace full runs of leading spaces, retaining existing tabs and line endings."""
    if not 1 <= width <= 16:
        raise ValueError("Ширина табуляции должна быть от 1 до 16.")
    import re

    def convert(match: re.Match[str]) -> str:
        prefix = match.group(0)
        return re.sub(r" +", lambda run: "\t" * (len(run.group()) // width) + " " * (len(run.group()) % width), prefix)

    return re.sub(r"(?m)^[ \t]+", convert, text)
