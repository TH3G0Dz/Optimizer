import unittest
from pathlib import Path
from unittest.mock import patch

from optimizer.system import list_drive_usage, list_system_features


class DriveUsageTests(unittest.TestCase):
    def test_lists_available_drive_usage(self) -> None:
        usage = (1000, 600, 400)
        with (
            patch("optimizer.system.list_drives", return_value=[Path("D:/")]),
            patch("optimizer.system.shutil.disk_usage", return_value=usage),
        ):
            drives = list_drive_usage()
        self.assertEqual(1, len(drives))
        self.assertEqual(400, drives[0].free)

    def test_system_features_use_official_settings_pages(self) -> None:
        features = list_system_features()
        self.assertGreaterEqual(len(features), 5)
        self.assertTrue(
            all(feature.settings_uri.startswith("ms-settings:") for feature in features)
        )


if __name__ == "__main__":
    unittest.main()
