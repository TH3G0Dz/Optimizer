import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from optimizer.apps import (
    delete_leftover_folder,
    list_installed_apps,
    list_windows_apps,
    prepare_installed_apps,
    review_leftover_folder,
    uninstall_app,
)
from optimizer.models import InstalledApp


class WindowsAppTests(unittest.TestCase):
    def test_filters_frameworks_and_protects_system_packages(self) -> None:
        packages = [
            {
                "Name": "Microsoft.BingWeather",
                "PackageFullName": "Microsoft.BingWeather_1.0_x64__test",
                "NonRemovable": False,
                "IsFramework": False,
                "IsResourcePackage": False,
                "IsPartOfSystem": False,
                "InstallLocation": r"C:\Program Files\WindowsApps\Weather",
                "Publisher": "Microsoft",
            },
            {
                "Name": "Microsoft.WindowsStore",
                "PackageFullName": "Microsoft.WindowsStore_1.0_x64__test",
                "NonRemovable": False,
                "IsFramework": False,
                "IsResourcePackage": False,
                "IsPartOfSystem": False,
                "InstallLocation": r"C:\Program Files\WindowsApps\Store",
                "Publisher": "Microsoft",
            },
            {
                "Name": "Microsoft.VCLibs.140.00",
                "PackageFullName": "Microsoft.VCLibs_1.0_x64__test",
                "NonRemovable": False,
                "IsFramework": True,
                "IsResourcePackage": False,
                "IsPartOfSystem": False,
                "InstallLocation": r"C:\Program Files\WindowsApps\VCLibs",
                "Publisher": "Microsoft",
            },
            {
                "Name": "MicrosoftCorporationII.WinAppRuntime.Main.2",
                "PackageFullName": "MicrosoftCorporationII.WinAppRuntime.Main.2_test",
                "NonRemovable": False,
                "IsFramework": False,
                "IsResourcePackage": False,
                "IsPartOfSystem": False,
                "InstallLocation": r"C:\Program Files\WindowsApps\Runtime",
                "Publisher": "Microsoft",
            },
        ]
        with patch("optimizer.apps._run_powershell", return_value=json.dumps(packages)):
            apps = list_windows_apps()

        self.assertEqual(3, len(apps))
        weather = next(app for app in apps if "BingWeather" in app.name)
        store = next(app for app in apps if "WindowsStore" in app.name)
        self.assertTrue(weather.removable)
        self.assertFalse(store.removable)
        self.assertTrue(store.protected_reason)
        runtime = next(app for app in apps if "Runtime" in app.name)
        self.assertFalse(runtime.removable)

    def test_removes_windows_app_for_current_user(self) -> None:
        app = InstalledApp(
            "Weather",
            "Microsoft",
            "",
            "",
            source="Windows",
            identifier="Microsoft.BingWeather_1.0_x64__test",
            removable=True,
        )
        with patch("optimizer.apps._run_powershell") as run:
            uninstall_app(app)
        script = run.call_args.args[0]
        self.assertIn("Remove-AppxPackage", script)
        self.assertNotIn("-AllUsers", script)

    def test_uses_registered_desktop_uninstaller(self) -> None:
        app = InstalledApp(
            "Editor",
            "Vendor",
            "1",
            r"C:\Apps\Editor",
            identifier="desktop:test",
            uninstall_command=r'"C:\Apps\Editor\uninstall.exe" /remove',
            removable=True,
        )
        with patch("optimizer.apps.subprocess.Popen") as popen:
            uninstall_app(app)
        popen.assert_called_once_with(app.uninstall_command, shell=False)

    def test_inventory_reports_partial_windows_failure(self) -> None:
        desktop = InstalledApp("Editor", "Vendor", "1", r"C:\Apps\Editor")
        with (
            patch("optimizer.apps.list_desktop_apps", return_value=[desktop]),
            patch(
                "optimizer.apps.list_windows_apps",
                side_effect=OSError("PowerShell bloqueado"),
            ),
        ):
            inventory = list_installed_apps()
        self.assertEqual((desktop,), inventory.apps)
        self.assertIn("PowerShell bloqueado", inventory.warnings[0])

    def test_filters_apps_and_marks_pending_leftover(self) -> None:
        desktop = InstalledApp(
            "Editor",
            "Vendor",
            "1",
            r"C:\Apps\Editor",
            identifier="desktop:editor",
            removable=True,
        )
        protected = InstalledApp(
            "System Host",
            "Microsoft",
            "",
            "",
            source="Windows",
            identifier="windows:host",
            protected_reason="Protegido",
        )
        pending = InstalledApp(
            "Old Tool",
            "Vendor",
            "1",
            r"C:\Apps\OldTool",
            identifier="desktop:old",
        )
        removable = prepare_installed_apps(
            [desktop, protected], [pending], category="Removíveis"
        )
        residual = prepare_installed_apps(
            [desktop, protected], [pending], category="Resíduos"
        )
        searched = prepare_installed_apps(
            [desktop, protected], [pending], query="microsoft"
        )
        self.assertEqual([desktop], removable)
        self.assertEqual("Old Tool", residual[0].name)
        self.assertTrue(residual[0].pending_leftover)
        self.assertEqual([protected], searched)


class LeftoverTests(unittest.TestCase):
    def test_deletes_unregistered_residual_folder(self) -> None:
        with tempfile.TemporaryDirectory(dir=".") as parent:
            folder = Path(parent) / "old-app"
            folder.mkdir()
            (folder / "cache.bin").write_bytes(b"data")
            app = InstalledApp(
                "Old App", "Vendor", "1", str(folder), identifier="desktop:old"
            )
            deleted = delete_leftover_folder(app, [])
            self.assertEqual(folder.resolve(), deleted)
            self.assertFalse(folder.exists())

    def test_blocks_folder_while_app_is_registered(self) -> None:
        with tempfile.TemporaryDirectory(dir=".") as parent:
            folder = Path(parent) / "installed-app"
            folder.mkdir()
            app = InstalledApp(
                "Installed App",
                "Vendor",
                "1",
                str(folder),
                identifier="desktop:installed",
            )
            with self.assertRaisesRegex(ValueError, "ainda está registrado"):
                review_leftover_folder(app, [app])

    def test_never_allows_windowsapps_folder(self) -> None:
        app = InstalledApp(
            "Store App",
            "Microsoft",
            "",
            r"C:\Program Files\WindowsApps\StoreApp",
            source="Windows",
            identifier="store:test",
        )
        with self.assertRaisesRegex(ValueError, "gerenciadas pelo sistema"):
            review_leftover_folder(app, [])

    def test_never_allows_a_broad_system_folder(self) -> None:
        profile = os.environ.get("USERPROFILE")
        if not profile:
            self.skipTest("USERPROFILE não está definido")
        app = InstalledApp(
            "Unsafe App", "Vendor", "", profile, identifier="desktop:unsafe"
        )
        with self.assertRaisesRegex(ValueError, "ampla do sistema"):
            review_leftover_folder(app, [])


if __name__ == "__main__":
    unittest.main()
