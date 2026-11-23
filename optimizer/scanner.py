import os
import string
from collections.abc import Iterable
from pathlib import Path

from .importance import classify
from .models import FileEntry, Importance


def list_drives() -> list[Path]:
    if hasattr(os, "listdrives"):
        return [Path(drive) for drive in os.listdrives()]
    return [
        Path(f"{letter}:\\")
        for letter in string.ascii_uppercase
        if Path(f"{letter}:\\").exists()
    ]


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
            entries.append(
                FileEntry(
                    path, is_dir, size, classify(path, is_dir=is_dir, is_link=is_link)
                )
            )
    return sorted(
        entries, key=lambda entry: (not entry.is_dir, entry.path.name.casefold())
    )


def filter_entries(
    entries: Iterable[FileEntry],
    *,
    query: str = "",
    importance: Importance | None = None,
    minimum_size: int = 0,
    sort_by: str = "Nome",
) -> list[FileEntry]:
    """Filter files while keeping directory navigation available."""
    needle = query.strip().casefold()
    visible: list[FileEntry] = []
    for entry in entries:
        name_matches = not needle or needle in entry.path.name.casefold()
        if entry.is_dir:
            if name_matches:
                visible.append(entry)
            continue
        if not name_matches:
            continue
        if importance is not None and entry.classification.importance is not importance:
            continue
        if (entry.size or 0) < minimum_size:
            continue
        visible.append(entry)

    def sort_key(entry: FileEntry) -> tuple:
        name = entry.path.name.casefold()
        if entry.is_dir:
            return (0, name)
        if sort_by == "Maior primeiro":
            return (1, -(entry.size or 0), name)
        if sort_by == "Menor primeiro":
            return (1, entry.size or 0, name)
        return (1, name)

    return sorted(visible, key=sort_key)


def format_size(size: int | None) -> str:
    if size is None:
        return ""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return ""
