import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from optimizer.cleanup import move_to_recycle_bin, review_file
from optimizer.models import Classification, Importance


class CleanupTests(unittest.TestCase):
    def test_reviews_regular_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder:
            path = Path(folder, "candidate.bin")
            path.write_bytes(b"1234")
            review = review_file(path)
            self.assertEqual(4, review.size)
            self.assertEqual(path.resolve(), review.path)

    def test_rejects_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder:
            with self.assertRaises(IsADirectoryError):
                review_file(Path(folder))

    def test_rejects_critical_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder:
            path = Path(folder, "protected.bin")
            path.touch()
            critical = Classification(Importance.CRITICAL, "Protegido")
            with patch("optimizer.cleanup.classify", return_value=critical), self.assertRaises(PermissionError):
                review_file(path)

    def test_recycle_uses_validated_fixed_drive_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder:
            path = Path(folder, "candidate.bin")
            path.touch()
            with patch("optimizer.cleanup._is_fixed_drive", return_value=False):
                with self.assertRaisesRegex(OSError, "volume"):
                    move_to_recycle_bin(path)

    def test_recycle_calls_windows_for_fixed_drive_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder:
            path = Path(folder, "candidate.bin")
            path.touch()
            with (
                patch("optimizer.cleanup._is_fixed_drive", return_value=True),
                patch("optimizer.cleanup.ctypes.windll.shell32.SHFileOperationW", return_value=0) as operation,
            ):
                move_to_recycle_bin(path)
            operation.assert_called_once()


if __name__ == "__main__":
    unittest.main()
