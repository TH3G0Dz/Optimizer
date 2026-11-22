import unittest
from pathlib import Path
from unittest.mock import patch

from optimizer.importance import classify
from optimizer.models import Importance


class ImportanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(
            "os.environ",
            {
                "WINDIR": r"C:\Windows",
                "ProgramFiles": r"C:\Program Files",
                "ProgramFiles(x86)": r"C:\Program Files (x86)",
                "ProgramData": r"C:\ProgramData",
            },
        )
        self.environment.start()

    def tearDown(self) -> None:
        self.environment.stop()

    def test_windows_content_is_critical_even_when_temporary(self) -> None:
        result = classify(Path(r"C:\Windows\Temp\update.tmp"))
        self.assertEqual(Importance.CRITICAL, result.importance)

    def test_personal_document_is_high(self) -> None:
        result = classify(Path(r"C:\Users\Ana\Documents\contrato.pdf"))
        self.assertEqual(Importance.HIGH, result.importance)

    def test_user_cache_is_low(self) -> None:
        result = classify(Path(r"C:\Users\Ana\AppData\Local\Example\Cache\item.bin"))
        self.assertEqual(Importance.LOW, result.importance)

    def test_unknown_file_requires_review(self) -> None:
        result = classify(Path(r"D:\dados\arquivo.bin"))
        self.assertEqual(Importance.REVIEW, result.importance)

    def test_link_requires_review(self) -> None:
        result = classify(Path(r"D:\atalho"), is_link=True)
        self.assertEqual(Importance.REVIEW, result.importance)


if __name__ == "__main__":
    unittest.main()
