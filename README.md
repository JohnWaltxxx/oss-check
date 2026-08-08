# oss-check

`oss-check` is a small, dependency-free command-line tool for checking whether an open-source repository has the basic ingredients for healthy maintenance.

It checks for:

- a README and an open-source license
- tests and continuous integration
- contribution guidance and project metadata
- a `.gitignore`
- a few common accidental-secret patterns

The tool is intentionally conservative: it reports useful signals, not a certification or a security guarantee.

## Quick start

Requires Python 3.10 or newer.

```bash
python -m pip install -e .
oss-check .
```

Example output:

```text
oss-check: /path/to/project
Score: 100/100
[PASS] README: README found
[PASS] License: License file found
[PASS] Tests: Test suite found
```

For CI and scripts, use JSON output and strict mode:

```bash
oss-check . --json
oss-check . --strict
```

## Development

The project has no runtime dependencies. Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

If you discover a possible security issue, please follow the process in [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Roadmap

- configurable checks for different languages and package ecosystems
- GitHub Actions annotations for failed checks
- an allowlist for documented example tokens
- improved secret detection with fewer false positives

## License

MIT. See [LICENSE](LICENSE).
