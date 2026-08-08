"""Command-line interface for oss-check."""

from __future__ import annotations

import argparse
import json
import sys

from .checks import inspect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oss-check",
        description="Check an open-source repository for basic maintenance essentials.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Repository path (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable JSON report")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when any check fails")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = inspect(args.path)
    except NotADirectoryError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"oss-check: {report.path}")
        print(f"Score: {report.score}/100")
        for check in report.checks:
            marker = "PASS" if check.passed else "FAIL"
            print(f"[{marker}] {check.name}: {check.message}")

    return 1 if args.strict and not report.passed else 0
