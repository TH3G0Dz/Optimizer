from pathlib import Path

from .importance import classify
from .models import FileReview, Importance


def review_file(path: Path) -> FileReview:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    if path.is_symlink():
        raise ValueError("Links não podem ser excluídos nesta versão.")
    if not path.is_file():
        raise IsADirectoryError("Somente arquivos podem ser excluídos nesta versão.")

    result = classify(path)
    if result.importance is Importance.CRITICAL:
        raise PermissionError("Arquivos críticos são protegidos pelo Optimizer.")
    return FileReview(path.resolve(), path.stat().st_size, result)


def delete_file(path: Path) -> FileReview:
    review = review_file(path)
    review.path.unlink()
    return review
