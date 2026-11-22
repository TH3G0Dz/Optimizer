import unittest
from pathlib import Path
from unittest.mock import patch

from optimizer.system import list_drive_usage


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


if __name__ == "__main__":
    unittest.main()
