import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from optimizer.cleanup import delete_file, review_file
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

    def test_deletes_reviewed_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder:
            path = Path(folder, "candidate.bin")
            path.touch()
            delete_file(path)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
