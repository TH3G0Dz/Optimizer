import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from .models import InstalledApp

PROTECTED_APPX_NAMES = {
    "aimgr",
    "Microsoft.DesktopAppInstaller",
    "Microsoft.BingSearch",
    "Microsoft.SecHealthUI",
    "Microsoft.StartExperiencesApp",
    "Microsoft.StorePurchaseApp",
    "Microsoft.WidgetsPlatformRuntime",
    "Microsoft.Winget.Source",
    "Microsoft.WindowsStore",
    "Microsoft.Xbox.TCUI",
    "Microsoft.XboxIdentityProvider",
    "Microsoft.XboxSpeechToTextOverlay",
    "MicrosoftCorporationII.WinAppRuntime.Singleton",
    "MicrosoftWindows.Client.WebExperience",
    "MicrosoftWindows.CrossDevice",
}
PROTECTED_APPX_PREFIXES = (
    "Microsoft.AAD.",
    "Microsoft.AccountsControl",
    "Microsoft.ApplicationCompatibility",
    "Microsoft.GamingServices",
    "Microsoft.Ink.Handwriting.",
    "Microsoft.LanguageExperiencePack",
    "Microsoft.MicrosoftEdge",
    "Microsoft.NET.",
    "Microsoft.Office",
    "Microsoft.OneDrive",
    "Microsoft.UI.",
    "Microsoft.VCLibs.",
    "Microsoft.WinAppRuntime",
    "Microsoft.WindowsAppRuntime",
    "Microsoft.Windows.CloudExperienceHost",
    "Microsoft.Windows.StartMenuExperienceHost",
    "Microsoft.Windows.ShellExperienceHost",
)


def list_installed_apps() -> list[InstalledApp]:
    apps = list_desktop_apps()
    try:
        apps.extend(list_windows_apps())
    except OSError:
        pass
    return sorted(apps, key=lambda app: (app.name.casefold(), app.source))


def list_desktop_apps() -> list[InstalledApp]:
    if os.name != "nt":
        return []

    import winreg

    locations = (
        (
            "Computador",
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            "Computador (32 bits)",
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            "Usuário",
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
    )
    apps: dict[tuple[str, str], InstalledApp] = {}
    for scope, hive, location in locations:
        try:
            with winreg.OpenKey(hive, location) as root:
                for index in range(winreg.QueryInfoKey(root)[0]):
                    key_name = winreg.EnumKey(root, index)
                    try:
                        with winreg.OpenKey(root, key_name) as app_key:
                            name = _value(app_key, "DisplayName")
                            if not name or _value(app_key, "SystemComponent") == 1:
                                continue
                            command = str(
                                _value(app_key, "QuietUninstallString")
                                or _value(app_key, "UninstallString")
                                or ""
                            ).strip()
                            app = InstalledApp(
                                name=str(name),
                                publisher=str(_value(app_key, "Publisher") or ""),
                                version=str(_value(app_key, "DisplayVersion") or ""),
                                location=str(_value(app_key, "InstallLocation") or ""),
                                source="Desktop",
                                identifier=f"{scope}:{location}\\{key_name}",
                                uninstall_command=command,
                                removable=bool(command),
                                protected_reason=(
                                    ""
                                    if command
                                    else "O aplicativo não registrou um desinstalador oficial."
                                ),
                            )
                            apps[(app.name.casefold(), app.version.casefold())] = app
                    except OSError:
                        continue
        except OSError:
            continue
    return sorted(apps.values(), key=lambda app: app.name.casefold())


def list_windows_apps() -> list[InstalledApp]:
    if os.name != "nt":
        return []
    script = (
        "Get-AppxPackage | Select-Object Name,PackageFullName,NonRemovable,"
        "IsFramework,IsResourcePackage,IsPartOfSystem,InstallLocation,Publisher | "
        "ConvertTo-Json -Compress"
    )
    output = _run_powershell(script)
    if not output.strip():
        return []
    try:
        data = json.loads(output)
    except json.JSONDecodeError as error:
        raise OSError(
            "O Windows retornou uma lista de aplicativos inválida."
        ) from error
    packages = data if isinstance(data, list) else [data]
    apps: dict[str, InstalledApp] = {}
    for package in packages:
        name = str(package.get("Name") or "")
        if not name or package.get("IsFramework") or package.get("IsResourcePackage"):
            continue
        non_removable = bool(package.get("NonRemovable"))
        protected = _protected_appx_reason(
            name, non_removable, bool(package.get("IsPartOfSystem"))
        )
        app = InstalledApp(
            name=_friendly_appx_name(name),
            publisher=str(package.get("Publisher") or "Microsoft/Windows"),
            version="",
            location=str(package.get("InstallLocation") or ""),
            source="Windows",
            identifier=str(package.get("PackageFullName") or ""),
            removable=not protected,
            protected_reason=protected,
        )
        apps[name.casefold()] = app
    return sorted(apps.values(), key=lambda app: app.name.casefold())


def uninstall_app(app: InstalledApp) -> None:
    if not app.removable:
        raise ValueError(app.protected_reason or "Este aplicativo está protegido.")
    if app.source == "Windows":
        if not re.fullmatch(r"[\w.\-]+", app.identifier):
            raise ValueError("Identificador do pacote Windows inválido.")
        package = app.identifier.replace("'", "''")
        _run_powershell(
            f"Remove-AppxPackage -Package '{package}' -Confirm:$false -ErrorAction Stop"
        )
        return
    if not app.uninstall_command:
        raise ValueError("O aplicativo não registrou um desinstalador oficial.")
    subprocess.Popen(os.path.expandvars(app.uninstall_command), shell=False)


def review_leftover_folder(
    app: InstalledApp, installed_apps: list[InstalledApp]
) -> Path:
    if app.source != "Desktop":
        raise ValueError("Pastas de aplicativos Windows são gerenciadas pelo sistema.")
    if any(item.identifier == app.identifier for item in installed_apps):
        raise ValueError("O aplicativo ainda está registrado como instalado.")
    if not app.location:
        raise ValueError("O aplicativo não informou uma pasta de instalação.")

    raw_candidate = Path(app.location)
    if raw_candidate.is_symlink():
        raise ValueError("Links de pasta não podem ser excluídos como resíduos.")
    candidate = raw_candidate.resolve(strict=True)
    if not candidate.is_dir():
        raise ValueError("A pasta residual não é uma pasta local válida.")
    if candidate == Path(candidate.anchor):
        raise ValueError("A raiz de uma unidade nunca pode ser excluída.")
    if "windowsapps" in {part.casefold() for part in candidate.parts}:
        raise ValueError("WindowsApps é gerenciada exclusivamente pelo Windows.")

    protected = _protected_folder_roots()
    if candidate in protected:
        raise ValueError("Esta pasta ampla do sistema está protegida.")
    windows_root = Path(os.environ.get("WINDIR", r"C:\Windows")).resolve()
    if _is_relative_to(candidate, windows_root):
        raise ValueError("Pastas internas do Windows estão protegidas.")

    for other in installed_apps:
        if not other.location:
            continue
        try:
            other_path = Path(other.location).resolve()
        except OSError:
            continue
        if _is_relative_to(other_path, candidate):
            raise ValueError(
                f"A pasta também contém o aplicativo instalado {other.name}."
            )
    return candidate


def delete_leftover_folder(
    app: InstalledApp, installed_apps: list[InstalledApp]
) -> Path:
    folder = review_leftover_folder(app, installed_apps)
    shutil.rmtree(folder)
    return folder


def _protected_folder_roots() -> set[Path]:
    names = (
        "WINDIR",
        "ProgramFiles",
        "ProgramFiles(x86)",
        "ProgramData",
        "USERPROFILE",
        "LOCALAPPDATA",
        "APPDATA",
    )
    return {Path(value).resolve() for name in names if (value := os.environ.get(name))}


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _protected_appx_reason(
    name: str, non_removable: bool, is_part_of_system: bool
) -> str:
    if non_removable:
        return "O Windows marcou este pacote como não removível."
    if is_part_of_system:
        return "O Windows marcou este pacote como parte do sistema."
    lowered = name.casefold()
    if "runtime" in lowered or re.fullmatch(r"Microsoft\.[0-9A-F]+", name):
        return "Runtime ou componente interno protegido para não quebrar outros apps."
    if name in PROTECTED_APPX_NAMES or name.startswith(PROTECTED_APPX_PREFIXES):
        return "Componente protegido para evitar falhas no Windows ou em outros apps."
    return ""


def _friendly_appx_name(name: str) -> str:
    return name.removeprefix("Microsoft.").replace(".", " ")


def _run_powershell(script: str) -> str:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
        creationflags=flags,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or "Falha ao executar o PowerShell."
        raise OSError(detail)
    return result.stdout


def _value(key, name: str):
    try:
        import winreg

        return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None


def open_windows_apps_settings() -> None:
    if os.name != "nt":
        raise OSError("Recurso disponível somente no Windows.")
    subprocess.Popen(
        ["cmd", "/c", "start", "", "ms-settings:appsfeatures"], shell=False
    )
