import os
import subprocess

from .models import InstalledApp


def list_installed_apps() -> list[InstalledApp]:
    if os.name != "nt":
        return []

    import winreg

    locations = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    )
    apps: dict[tuple[str, str], InstalledApp] = {}
    for hive, location in locations:
        try:
            with winreg.OpenKey(hive, location) as root:
                for index in range(winreg.QueryInfoKey(root)[0]):
                    try:
                        with winreg.OpenKey(root, winreg.EnumKey(root, index)) as app_key:
                            name = _value(app_key, "DisplayName")
                            if not name or _value(app_key, "SystemComponent") == 1:
                                continue
                            app = InstalledApp(
                                str(name),
                                str(_value(app_key, "Publisher") or ""),
                                str(_value(app_key, "DisplayVersion") or ""),
                                str(_value(app_key, "InstallLocation") or ""),
                            )
                            apps[(app.name.casefold(), app.version.casefold())] = app
                    except OSError:
                        continue
        except OSError:
            continue
    return sorted(apps.values(), key=lambda app: app.name.casefold())


def _value(key, name: str):
    try:
        import winreg

        return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None


def open_windows_apps_settings() -> None:
    if os.name != "nt":
        raise OSError("Recurso disponível somente no Windows.")
    subprocess.Popen(["cmd", "/c", "start", "", "ms-settings:appsfeatures"], shell=False)

