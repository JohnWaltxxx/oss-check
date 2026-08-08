"""Checks used by the :mod:`osscheck` command-line interface."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class CheckResult:
    """The result of one repository check."""

    name: str
    passed: bool
    message: str
    severity: str = "info"


@dataclass(frozen=True)
class Report:
    """A complete repository health report."""

    path: str
    score: int
    checks: list[CheckResult]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "score": self.score,
            "passed": self.passed,
            "checks": [asdict(check) for check in self.checks],
        }


_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[\"'][^\"']{12,}[\"']"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
_IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}
_TEXT_SUFFIXES = {".c", ".cc", ".cpp", ".go", ".java", ".js", ".json", ".md", ".py", ".rb", ".rs", ".sh", ".toml", ".ts", ".tsx", ".yaml", ".yml"}


def _has_any(root: Path, names: tuple[str, ...]) -> bool:
    return any((root / name).exists() for name in names)


def check_readme(root: Path) -> CheckResult:
    found = _has_any(root, ("README.md", "README.rst", "README.txt"))
    return CheckResult("README", found, "README found" if found else "Add a README file", "error")


def check_license(root: Path) -> CheckResult:
    found = any(root.glob("LICENSE*")) or any(root.glob("COPYING*"))
    return CheckResult("License", found, "License file found" if found else "Add a LICENSE or COPYING file", "error")


def check_tests(root: Path) -> CheckResult:
    test_dirs = (root / "tests").is_dir() or (root / "test").is_dir()
    test_files = any(root.rglob("test_*.py")) or any(root.rglob("*_test.go"))
    found = test_dirs or test_files
    return CheckResult("Tests", found, "Test suite found" if found else "Add a tests/ directory or test files", "error")


def check_ci(root: Path) -> CheckResult:
    workflows = root / ".github" / "workflows"
    found = workflows.is_dir() and any(workflows.glob("*.y*ml"))
    return CheckResult("Continuous integration", found, "GitHub Actions workflow found" if found else "Add a workflow under .github/workflows", "warning")


def check_contributing(root: Path) -> CheckResult:
    found = _has_any(root, ("CONTRIBUTING.md", "CONTRIBUTING.rst"))
    return CheckResult("Contribution guide", found, "Contribution guide found" if found else "Add CONTRIBUTING.md to explain how to help", "warning")


def check_project_metadata(root: Path) -> CheckResult:
    pyproject = root / "pyproject.toml"
    package_json = root / "package.json"
    found = False
    if pyproject.exists():
        found = "[project]" in pyproject.read_text(encoding="utf-8", errors="ignore")
    elif package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            found = bool(data.get("name") and data.get("description"))
        except json.JSONDecodeError:
            found = False
    return CheckResult("Project metadata", found, "Project metadata found" if found else "Add package metadata with a name and description", "warning")


def check_gitignore(root: Path) -> CheckResult:
    found = (root / ".gitignore").is_file()
    return CheckResult("Git hygiene", found, ".gitignore found" if found else "Add a .gitignore file", "warning")


def check_secrets(root: Path) -> CheckResult:
    matches: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _TEXT_SUFFIXES or any(part in _IGNORED_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(pattern.search(text) for pattern in _SECRET_PATTERNS):
            matches.append(str(path.relative_to(root)))
    if matches:
        return CheckResult("Secret scan", False, "Possible secret found in: " + ", ".join(matches[:3]), "error")
    return CheckResult("Secret scan", True, "No obvious secrets found", "info")


CHECKS: tuple[Callable[[Path], CheckResult], ...] = (
    check_readme,
    check_license,
    check_tests,
    check_ci,
    check_contributing,
    check_project_metadata,
    check_gitignore,
    check_secrets,
)


def inspect(root: str | Path) -> Report:
    """Inspect *root* and return a report without changing any files."""

    path = Path(root).expanduser().resolve()
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
    checks = [check(path) for check in CHECKS]
    score = round(sum(check.passed for check in checks) / len(checks) * 100)
    return Report(str(path), score, checks)
