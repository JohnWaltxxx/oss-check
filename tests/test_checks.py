import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from osscheck.checks import inspect
from osscheck.cli import main


class InspectTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        directory = Path(tempfile.mkdtemp())
        for name, content in files.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return directory

    def test_healthy_repository_scores_full_marks(self):
        root = self.make_repo(
            {
                "README.md": "# Demo\n",
                "LICENSE": "MIT\n",
                "CONTRIBUTING.md": "How to contribute\n",
                ".gitignore": "__pycache__/\n",
                "pyproject.toml": "[project]\nname='demo'\ndescription='demo'\n",
                "tests/test_demo.py": "def test_ok(): pass\n",
                ".github/workflows/test.yml": "name: test\n",
            }
        )
        report = inspect(root)
        self.assertEqual(report.score, 100)
        self.assertTrue(report.passed)

    def test_missing_essentials_are_reported(self):
        report = inspect(self.make_repo({"README.md": "# Demo\n"}))
        self.assertLess(report.score, 100)
        self.assertFalse(report.passed)
        self.assertIn("License", {check.name for check in report.checks})

    def test_secret_scan_finds_common_token_shape(self):
        fake_token = "sk-" + "12345678901234567890"
        key_name = "api" + "_key"
        root = self.make_repo({"README.md": f"{key_name} = '{fake_token}'\n"})
        report = inspect(root)
        secret_check = next(check for check in report.checks if check.name == "Secret scan")
        self.assertFalse(secret_check.passed)

    def test_json_output_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main([str(root), "--json"]), 0)
            data = json.loads(output.getvalue())
            self.assertEqual(data["path"], str(root.resolve()))
            self.assertEqual(data["score"], 25)

    def test_strict_mode_fails_when_a_warning_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main([str(root), "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
