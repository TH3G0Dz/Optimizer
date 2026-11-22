import os
import string
from pathlib import Path

from .importance import classify
from .models import FileEntry


def list_drives() -> list[Path]:
    if hasattr(os, "listdrives"):
        return [Path(drive) for drive in os.listdrives()]
    return [Path(f"{letter}:\\") for letter in string.ascii_uppercase if Path(f"{letter}:\\").exists()]


def list_children(folder: Path) -> list[FileEntry]:
    entries: list[FileEntry] = []
    with os.scandir(folder) as iterator:
        for item in iterator:
            try:
                is_dir = item.is_dir(follow_symlinks=False)
                is_link = item.is_symlink()
                size = None if is_dir else item.stat(follow_symlinks=False).st_size
            except OSError:
                is_dir = False
                is_link = True
                size = None
            path = Path(item.path)
            entries.append(FileEntry(path, is_dir, size, classify(path, is_dir=is_dir, is_link=is_link)))
    return sorted(entries, key=lambda entry: (not entry.is_dir, entry.path.name.casefold()))


def format_size(size: int | None) -> str:
    if size is None:
        return ""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return ""

