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
