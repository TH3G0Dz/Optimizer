import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from optimizer.cleanup import delete_file, delete_files, review_file, review_files
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
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder, self.assertRaises(IsADirectoryError):
            review_file(Path(folder))

    def test_rejects_critical_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder:
            path = Path(folder, "protected.bin")
            path.touch()
            critical = Classification(Importance.CRITICAL, "Protegido")
            with (
                patch("optimizer.cleanup.classify", return_value=critical),
                self.assertRaises(PermissionError),
            ):
                review_file(path)

    def test_deletes_reviewed_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder:
            path = Path(folder, "candidate.bin")
            path.touch()
            delete_file(path)
            self.assertFalse(path.exists())

    def test_reviews_and_deletes_multiple_files(self) -> None:
        with tempfile.TemporaryDirectory(dir="D:\\Optimizer") as folder:
            paths = [Path(folder, "one.bin"), Path(folder, "two.bin")]
            for path in paths:
                path.touch()
            self.assertEqual(2, len(review_files(paths)))
            deleted, failures = delete_files(paths)
            self.assertEqual(2, len(deleted))
            self.assertEqual([], failures)
            self.assertTrue(all(not path.exists() for path in paths))


if __name__ == "__main__":
    unittest.main()
