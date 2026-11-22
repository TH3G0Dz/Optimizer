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
    source: str = "Desktop"
    identifier: str = ""
    uninstall_command: str = ""
    removable: bool = False
    protected_reason: str = ""


@dataclass(frozen=True)
class FileReview:
    path: Path
    size: int
    classification: Classification


@dataclass(frozen=True)
class DriveUsage:
    path: Path
    total: int
    used: int
    free: int


@dataclass(frozen=True)
class SystemFeature:
    name: str
    effect: str
    risk: str
    settings_uri: str
