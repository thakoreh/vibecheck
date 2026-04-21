<div align="center">

# vibechecker

**Audit your AI-generated code.**

Catch anti-patterns, security issues, and get a vibe score.

[![PyPI](https://img.shields.io/pypi/v/vibechecker.svg)](https://pypi.org/project/vibechecker/)
[![Python](https://img.shields.io/pypi/pyversions/vibechecker.svg)](https://pypi.org/project/vibechecker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-9%20passing-green)](tests/)

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
| 0 | Clean, no critical issues |
| 1 | Score below 60 |
| 2 | Critical security issues found |

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
