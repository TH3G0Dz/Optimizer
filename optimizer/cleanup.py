from collections.abc import Iterable
from pathlib import Path

from .importance import classify
from .models import FileReview, Importance


def review_file(path: Path) -> FileReview:
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Links não podem ser excluídos nesta versão.")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Arquivo não encontrado: {path}") from error
    if not resolved.is_file():
        raise IsADirectoryError("Somente arquivos podem ser excluídos nesta versão.")

    result = classify(resolved)
    if result.importance is Importance.CRITICAL:
        raise PermissionError("Arquivos críticos são protegidos pelo Optimizer.")
    return FileReview(resolved, resolved.stat().st_size, result)


def delete_file(path: Path) -> FileReview:
    review = review_file(path)
    review.path.unlink()
    return review


def review_files(paths: Iterable[Path]) -> list[FileReview]:
    reviews: list[FileReview] = []
    seen: set[Path] = set()
    for path in paths:
        review = review_file(path)
        if review.path not in seen:
            reviews.append(review)
            seen.add(review.path)
    if not reviews:
        raise ValueError("Selecione pelo menos um arquivo.")
    return reviews


def delete_files(paths: Iterable[Path]) -> tuple[list[Path], list[tuple[Path, str]]]:
    deleted: list[Path] = []
    failures: list[tuple[Path, str]] = []
    for path in paths:
        try:
            deleted.append(delete_file(path).path)
        except (OSError, ValueError) as error:
            failures.append((Path(path), str(error)))
    return deleted, failures
