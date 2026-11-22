from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Importance(Enum):
    CRITICAL = "Crítico"
    HIGH = "Alto"
    MEDIUM = "Médio"
    LOW = "Baixo"
    REVIEW = "Revisar"


@dataclass(frozen=True)
class Classification:
    importance: Importance
    reason: str


@dataclass(frozen=True)
class FileEntry:
    path: Path
    is_dir: bool
    size: int | None
    classification: Classification


@dataclass(frozen=True)
class InstalledApp:
    name: str
    publisher: str
    version: str
    location: str


@dataclass(frozen=True)
class FileReview:
    path: Path
    size: int
    classification: Classification

