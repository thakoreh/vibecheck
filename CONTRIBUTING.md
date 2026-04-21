# Contributing to VibeCheck

Thanks for your interest! This project is early and there's lots of room to contribute.

## Quick Start

```bash
git clone https://github.com/thakoreh/vibecheck.git
cd vibecheck
pip install -e ".[dev]"
pytest
```

## What to Contribute

### High Priority
- **New language support** — Add patterns for Go, Rust, Java, Ruby, PHP, C#, etc.
- **GitHub Action** — Wrap vibechecker in a reusable action
- **Pre-commit hook** — `.pre-commit-hooks.yaml`
- **New pattern rules** — See `vibecheck/patterns.py` for examples

### Nice to Have
- VS Code extension
- GitLab CI template
- Web dashboard for reports
- `--fix` flag for auto-fixing simple issues
- `--explain` mode using AI to explain flagged code

## Adding a New Pattern

Patterns live in `vibecheck/patterns.py`. Each pattern is a `Pattern` dataclass:

```python
Pattern(
    id="unique-id",           # kebab-case identifier
    name="Human Name",         # short display name
    severity="warning",        # "critical", "warning", or "info"
    description="What's wrong",# one-line explanation
    pattern=r"regex_here",     # Python regex
    languages=[".py"],         # file extensions it applies to
    suggestion="How to fix",   # actionable advice
)
```

Add it to `AI_SMELLS` or `SECURITY_PATTERNS`, then add a test in `tests/test_scanner.py`.

## Adding a New Language

1. Add file extension mappings in `scanner.py` (`get_language()`)
2. Add patterns with the new extension in `languages` list
3. Add tests
4. Update README

## Running Tests

```bash
pytest -v
```

## PR Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make changes + add tests
4. Ensure tests pass (`pytest`)
5. Submit PR with a clear description

## Code Style

- Python 3.9+ compatible (no `match` statements, use `from __future__ import annotations`)
- Use `rich` for all terminal output
- Keep the CLI dependency-light (only `rich` and `typer`)
- Pure regex for pattern matching (no AST dependencies)
