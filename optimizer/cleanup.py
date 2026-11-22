import ctypes
import os
from ctypes import wintypes
from pathlib import Path

from .importance import classify
from .models import FileReview, Importance


FO_DELETE = 3
FOF_ALLOWUNDO = 0x0040
FOF_WANTNUKEWARNING = 0x4000
DRIVE_FIXED = 3


class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = (
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", wintypes.WORD),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", wintypes.LPVOID),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    )


def review_file(path: Path) -> FileReview:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    if path.is_symlink():
        raise ValueError("Links não podem ser excluídos nesta versão.")
    if not path.is_file():
        raise IsADirectoryError("Somente arquivos podem ser enviados à Lixeira nesta versão.")

    result = classify(path)
    if result.importance is Importance.CRITICAL:
        raise PermissionError("Arquivos críticos são protegidos pelo Optimizer.")
    return FileReview(path.resolve(), path.stat().st_size, result)


def move_to_recycle_bin(path: Path) -> None:
    review = review_file(path)
    if os.name != "nt":
        raise OSError("A Lixeira está disponível somente no Windows.")
    if not _is_fixed_drive(review.path):
        raise OSError("O volume não oferece a proteção exigida para esta operação.")

    operation = SHFILEOPSTRUCTW()
    operation.wFunc = FO_DELETE
    operation.pFrom = f"{review.path}\0"
    operation.fFlags = FOF_ALLOWUNDO | FOF_WANTNUKEWARNING
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
    if operation.fAnyOperationsAborted:
        raise OSError("Operação cancelada.")
    if result:
        raise OSError(result, "O Windows não conseguiu mover o arquivo para a Lixeira.")


def _is_fixed_drive(path: Path) -> bool:
    return ctypes.windll.kernel32.GetDriveTypeW(path.anchor) == DRIVE_FIXED
