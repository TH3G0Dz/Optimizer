import shutil
import subprocess

from .models import DriveUsage, SystemFeature
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


SYSTEM_FEATURES = (
    SystemFeature(
        "Aplicativos de inicialização",
        "Reduz programas executados ao entrar no Windows.",
        "Baixo",
        "ms-settings:startupapps",
    ),
    SystemFeature(
        "Xbox Game Bar",
        "Controla sobreposição e gravação de jogos.",
        "Baixo",
        "ms-settings:gaming-gamebar",
    ),
    SystemFeature(
        "Capturas em segundo plano",
        "Controla gravação contínua de jogos.",
        "Médio",
        "ms-settings:gaming-gamedvr",
    ),
    SystemFeature(
        "Efeitos visuais",
        "Ajusta animações e transparência da interface.",
        "Baixo",
        "ms-settings:easeofaccess-visualeffects",
    ),
    SystemFeature(
        "Diagnóstico opcional",
        "Controla dados opcionais enviados ao Windows.",
        "Baixo",
        "ms-settings:privacy-feedback",
    ),
    SystemFeature(
        "Notificações",
        "Reduz notificações e atividade associada.",
        "Baixo",
        "ms-settings:notifications",
    ),
    SystemFeature(
        "Recursos opcionais",
        "Permite remover componentes opcionais suportados.",
        "Alto",
        "ms-settings:optionalfeatures",
    ),
)


def list_system_features() -> tuple[SystemFeature, ...]:
    return SYSTEM_FEATURES


def open_system_feature(feature: SystemFeature) -> None:
    _open_setting(feature.settings_uri)


def _open_setting(uri: str) -> None:
    subprocess.Popen(["cmd", "/c", "start", "", uri], shell=False)
