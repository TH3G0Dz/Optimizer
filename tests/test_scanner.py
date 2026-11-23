import unittest
from pathlib import Path

from optimizer.models import Classification, FileEntry, Importance
from optimizer.scanner import filter_entries, format_size


class FormatSizeTests(unittest.TestCase):
    def test_formats_bytes(self) -> None:
        self.assertEqual("42 B", format_size(42))

    def test_formats_megabytes(self) -> None:
        self.assertEqual("2.0 MB", format_size(2 * 1024 * 1024))

    def test_folder_has_no_size(self) -> None:
        self.assertEqual("", format_size(None))


class FilterEntriesTests(unittest.TestCase):
    @staticmethod
    def entry(
        name: str,
        *,
        importance: Importance = Importance.REVIEW,
        size: int | None = 0,
        is_dir: bool = False,
    ) -> FileEntry:
        return FileEntry(
            Path("D:/") / name,
            is_dir,
            None if is_dir else size,
            Classification(importance, "teste"),
        )

    def test_low_importance_filter_keeps_folders_visible(self) -> None:
        folder = self.entry("Cache", is_dir=True)
        low = self.entry("trace.tmp", importance=Importance.LOW)
        high = self.entry("photo.jpg", importance=Importance.HIGH)

        result = filter_entries([high, low, folder], importance=Importance.LOW)

        self.assertEqual([folder, low], result)

    def test_query_matches_name_or_extension(self) -> None:
        log = self.entry("optimizer.log")
        image = self.entry("photo.png")

        result = filter_entries([image, log], query=".LOG")

        self.assertEqual([log], result)

    def test_minimum_size_and_largest_first_sort(self) -> None:
        folder = self.entry("Projetos", is_dir=True)
        medium = self.entry("medium.bin", size=150 * 1024**2)
        large = self.entry("large.bin", size=500 * 1024**2)
        small = self.entry("small.bin", size=2 * 1024**2)

        result = filter_entries(
            [small, medium, folder, large],
            minimum_size=100 * 1024**2,
            sort_by="Maior primeiro",
        )

        self.assertEqual([folder, large, medium], result)


if __name__ == "__main__":
    unittest.main()
