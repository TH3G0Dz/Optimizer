import shutil
import subprocess

from .models import DriveUsage
from .scanner import list_drives


def list_drive_usage() -> list[DriveUsage]:
    drives: list[DriveUsage] = []
    for drive in list_drives():
        try:
            total, used, free = shutil.disk_usage(drive)
        except OSError:
            continue
        drives.append(DriveUsage(drive, total, used, free))
    return drives


def open_storage_settings() -> None:
    _open_setting("ms-settings:storage")


def open_startup_settings() -> None:
    _open_setting("ms-settings:startupapps")


def open_task_manager() -> None:
    subprocess.Popen(["taskmgr.exe"])


def open_optimize_drives() -> None:
    subprocess.Popen(["dfrgui.exe"])


def _open_setting(uri: str) -> None:
    subprocess.Popen(["cmd", "/c", "start", "", uri], shell=False)
