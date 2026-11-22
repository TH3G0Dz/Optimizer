import os
from pathlib import Path

from .models import Classification, Importance

PERSONAL_FOLDERS = {"desktop", "documents", "downloads", "music", "pictures", "videos"}
PERSONAL_EXTENSIONS = {
    ".doc",
    ".docx",
    ".jpg",
    ".jpeg",
    ".mov",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".txt",
    ".xls",
    ".xlsx",
    ".zip",
}
EXECUTABLE_EXTENSIONS = {".bat", ".cmd", ".dll", ".exe", ".msi", ".ps1", ".sys"}
DATA_EXTENSIONS = {".cfg", ".db", ".ini", ".json", ".sqlite", ".yaml", ".yml"}
CACHE_PARTS = {"cache", "caches", "crashdumps", "temp", "tmp"}


def _normalized(path: Path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _is_within(path: str, root: str | None) -> bool:
    if not root:
        return False
    normalized_root = os.path.normcase(os.path.abspath(root))
    try:
        return os.path.commonpath((path, normalized_root)) == normalized_root
    except ValueError:
        return False


def classify(
    path: Path, *, is_dir: bool = False, is_link: bool = False
) -> Classification:
    normalized = _normalized(path)
    protected_roots = (
        os.environ.get("WINDIR", r"C:\Windows"),
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("ProgramData", r"C:\ProgramData"),
    )

    if is_link:
        return Classification(
            Importance.REVIEW, "Atalho ou ligação; o destino precisa ser verificado."
        )
    if any(_is_within(normalized, root) for root in protected_roots):
        return Classification(
            Importance.CRITICAL, "Área do Windows ou de programas instalados."
        )

    parts = {part.casefold() for part in path.parts}
    suffix = path.suffix.casefold()
    if parts & PERSONAL_FOLDERS or suffix in PERSONAL_EXTENSIONS:
        return Classification(
            Importance.HIGH, "Arquivo pessoal ou conteúdo difícil de recriar."
        )
    if suffix in EXECUTABLE_EXTENSIONS:
        return Classification(
            Importance.HIGH, "Executável, instalador ou componente de software."
        )
    if parts & CACHE_PARTS:
        return Classification(
            Importance.LOW, "Cache ou temporário provável; confirme se está em uso."
        )
    if suffix in DATA_EXTENSIONS:
        return Classification(
            Importance.MEDIUM, "Configuração ou banco de dados local."
        )
    if is_dir:
        return Classification(
            Importance.REVIEW, "Pasta ainda não analisada por contexto."
        )
    return Classification(Importance.REVIEW, "Impacto não identificado com confiança.")
