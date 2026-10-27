<div align="center">

# vibechecker

**Audit your AI-generated code.**

Catch anti-patterns, security issues, and get a vibe score.

[![PyPI](https://img.shields.io/pypi/v/vibechecker.svg)](https://pypi.org/project/vibechecker/)
[![Python](https://img.shields.io/pypi/pyversions/vibechecker.svg)](https://pypi.org/project/vibechecker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/thakoreh/vibecheck/actions/workflows/ci.yml/badge.svg)](https://github.com/thakoreh/vibecheck/actions/workflows/ci.yml)

</div>

---

```
pip install vibechecker
vibechecker scan .
```

## What it does

VibeChecker scans your codebase for patterns commonly found in AI-generated code:

- **🚨 Security issues** — hardcoded secrets, eval(), SQL injection, shell=True, pickle.load
- **⚠️ AI code smells** — generic exception handling, placeholder variable names, leftover console.log, TODO comments, magic numbers
- **💡 Suggestions** — overly verbose comments, generic function names, over-documented trivial code

Then it gives you a **vibe score** from 0-100.

This is a local, heuristic scanner. A high score means few configured patterns
matched; it does not prove code is secure, correct, or AI-generated. Findings
need human review. Rules do not follow imports, aliases, data flow, or all
multiline expressions. Python call checks ignore ordinary literal strings and comments;
Python 3.9-3.11 f-strings are scanned conservatively, including their literal text.
JavaScript/TypeScript rules remain regex-based and can match examples in strings
or comments. Use language-specific linters and security tools alongside it.
Unused-import detection is not provided because matching an import alone cannot
establish whether it is used.

## Demo

```
$ vibechecker scan ./src

╭─────────────────── Vibe Score ───────────────────╮
│                                                   │
│  72/100  🟠  Grade C                             │
│                                                   │
│  Getting shaky. Review the warnings first.        │
│                                                   │
╰───────────────────────────────────────────────────╯

  23 files · 3,412 lines · 14 findings

  🚨 Security Issues (2)
    Hardcoded Secret config.py:12
      → Use environment variables. Never commit secrets.
    eval() Usage parser.py:45
      → Use ast.literal_eval() or JSON.parse().

  ⚠️  AI Code Smells (5)
    Broad Exception Handler utils.py:15
      → Catch specific exceptions (ValueError, KeyError, etc.)
    Placeholder Variable Names handler.py:23
      → Use descriptive names that explain the variable's purpose.
    ...

  ⚡ Quick Wins
    • Move secrets to environment variables
    • Replace generic exception handlers
    • Rename placeholder variables
```

## Install

```bash
pip install vibechecker
```

Requires Python 3.9 or newer. For an isolated install, create a virtual environment
with `python -m venv .venv`, activate it, then run the command above. On Windows,
activation is `.venv\Scripts\Activate.ps1`; on macOS/Linux, use
`source .venv/bin/activate`. `vibechecker --version` shows the installed version.

To upgrade an existing installation, run `python -m pip install --upgrade vibechecker`.
See [CHANGELOG.md](CHANGELOG.md) for changes. A source version or GitHub tag alone
does not update the package installed from PyPI.

## Usage

```bash
# Scan current directory
vibechecker scan .

# Scan specific directory
vibechecker scan ./src

# JSON output (for CI/CD)
vibechecker scan . --json

# Security issues only
vibechecker scan . --security

# Skip security checks
vibechecker scan . --no-security

# Ignore directories
vibechecker scan . --ignore vendor --ignore generated
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Score at least 60, no critical patterns found |
| 1 | Score below 60 |
| 2 | Critical patterns found |
| 3 | Scan could not complete: missing/unreadable input, no eligible files, or conflicting rule options |

Exit 2 takes precedence over the score and also covers critical code-smell
patterns such as bare `except`. Exit 0 means the configured thresholds passed,
not that the code is safe. With `--json`, operational errors return an
`{"error": "..."}` object and exit 3; ordinary terminal errors go to stderr.
CLI syntax errors use exit 2 and show usage.

Only `.py`, `.js`, `.jsx`, `.ts`, and `.tsx` files of at most 500,000 bytes are
scanned. Empty supported files count as scanned; a directory with no eligible
files is an error. Source must be UTF-8 (a UTF-8 BOM is accepted); unreadable or
invalidly encoded source stops the scan rather than producing a partial score.
Generated/dependency directories are pruned by default. `--ignore` accepts
directory names or glob patterns relative to the scan target, for example
`--ignore '*.egg-info'`. Explicit file targets use the same type/size limits.

Perfect for CI pipelines:

```yaml
# GitHub Actions
- name: VibeChecker
  run: |
    pip install vibechecker
    vibechecker scan . --json > vibecheck-report.json
    vibechecker scan .
```

## Languages Supported

- Python (`.py`)
- JavaScript (`.js`, `.jsx`)
- TypeScript (`.ts`, `.tsx`)

More languages welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## How Scoring Works

| Component | Impact |
|-----------|--------|
| Start | 100 |
| Critical issue | -15 each (max -60) |
| Warning | -5 each (max -40) |
| Info | -1 each (max -15) |
| Has tests | +5 |
| Small files (< 100 lines avg) | +5 |

## Contributing

We welcome contributions! Especially:

- **New language support** (Go, Rust, Java, Ruby, PHP, etc.)
- **New pattern detection rules**
- **CI/CD integrations** (GitHub Action, pre-commit hook, GitLab CI)
- **IDE extensions** (VS Code, JetBrains)
- **Bug fixes and pattern improvements**

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Why "vibechecker"?

Because "vibe coding" is how most of us use AI now. Ship fast, but know what you shipped.

## License

[MIT](LICENSE)
