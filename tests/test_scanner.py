import unittest

from optimizer.scanner import format_size


class FormatSizeTests(unittest.TestCase):
    def test_formats_bytes(self) -> None:
        self.assertEqual("42 B", format_size(42))

    def test_formats_megabytes(self) -> None:
        self.assertEqual("2.0 MB", format_size(2 * 1024 * 1024))

    def test_folder_has_no_size(self) -> None:
        self.assertEqual("", format_size(None))


if __name__ == "__main__":
    unittest.main()
