# Changelog

## 0.1.2

Release prepared from the fresh-user fixes merged in PR #1. PyPI publication is
pending; the public registry remains at 0.1.1 until the upload is verified.

- Return explicit operational errors for missing or unreadable input, no eligible
  source files, and conflicting rule selections. JSON errors use exit code 3.
- Apply supported-file and size limits consistently, count empty supported files,
  and prune ignored directories relative to the selected target.
- Avoid Python direct-call false positives in ordinary strings and comments.
  Remove the import-only rule that incorrectly marked used imports as unused.
- Detect multiline silent exception handlers, long final functions, unsafe YAML
  loaders, and the existing security patterns in supported JSX/TSX source.
- Correct the reported package version and support legacy Windows terminal
  encodings and filenames containing markup characters.
- Clarify heuristic limits and validate installed wheels and source distributions
  across Python 3.9-3.14 on Linux and Python 3.13 on Windows.

## 0.1.1

Published on PyPI on 2026-04-21.
