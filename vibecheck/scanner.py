"""Code scanner - walks directories and matches patterns."""

from __future__ import annotations

import io
import os
import re
import tokenize
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional

from .patterns import Pattern


@dataclass
class Finding:
    file: str
    line: int
    col: int
    pattern: Pattern
    code: str


@dataclass
class FileResult:
    path: str
    language: str
    lines_total: int
    findings: list[Finding] = field(default_factory=list)


# Directories to always skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".next", ".nuxt", "dist", "build", "out", ".tox", ".mypy_cache",
    ".pytest_cache", ".hg", ".svn", "target", "vendor", ".idea",
    ".vscode", ".eggs", "*.egg-info", "coverage", ".coverage",
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".db", ".sqlite", ".sqlite3",
    ".lock", ".min.js", ".min.css",
}

MAX_FILE_SIZE = 500_000  # skip files > 500KB
SUPPORTED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}


class ScanError(Exception):
    """The requested scan could not be completed."""


def should_scan(path: Path) -> bool:
    """Check if a file should be scanned."""
    if path.suffix not in SUPPORTED_EXTENSIONS:
        return False
    if path.suffix in SKIP_EXTENSIONS:
        return False
    if any(part.endswith(".min.js") or part.endswith(".min.css") for part in path.parts):
        return False
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return False
    except OSError as exc:
        raise ScanError(f"Cannot inspect {path}: {exc}") from exc
    return True


def get_language(path: Path) -> str:
    """Map file extension to language category."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
    }
    return ext_map.get(path.suffix, "unknown")


def _python_code(content: str) -> str:
    """Mask literal strings/comments for call rules, preserving source positions."""
    lines = content.splitlines(keepends=True)
    try:
        for token in tokenize.generate_tokens(io.StringIO(content).readline):
            if token.type not in (tokenize.STRING, tokenize.COMMENT, getattr(tokenize, "FSTRING_MIDDLE", -1)):
                continue
            if token.type == tokenize.STRING and re.match(r"(?i)^[rubf]*f[rubf]*['\"]", token.string):
                # Python <=3.11 tokenizes whole f-strings as STRING; retain
                # interpolations so executable calls are not hidden.
                continue
            (start_row, start_col), (end_row, end_col) = token.start, token.end
            for row in range(start_row - 1, end_row):
                start = start_col if row == start_row - 1 else 0
                end = end_col if row == end_row - 1 else len(lines[row])
                piece = lines[row][start:end]
                masked = "".join("\n" if char == "\n" else " " for char in piece)
                lines[row] = lines[row][:start] + masked + lines[row][end:]
    except (tokenize.TokenError, IndentationError):
        # Keep scanning incomplete source; tokens consumed so far are still masked.
        pass
    return "".join(lines)


def scan_file(path: Path, patterns: list[Pattern]) -> FileResult:
    """Scan a single file against given patterns."""
    result = FileResult(
        path=str(path),
        language=get_language(path),
        lines_total=0,
    )

    try:
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise ScanError(f"Cannot read {path}: {exc}") from exc

    lines = content.splitlines()
    result.lines_total = len(lines)

    ext = path.suffix
    code = _python_code(content) if ext == ".py" else content
    call_rules = {"eval-usage", "exec-usage", "pickle-load", "unsafe-yaml"}

    for pattern in patterns:
        if ext not in pattern.languages:
            continue

        try:
            regex = re.compile(pattern.pattern, re.IGNORECASE)
        except re.error as exc:
            raise ScanError(f"Invalid rule {pattern.id}: {exc}") from exc

        if pattern.id == "long-function":
            # Special handling: count lines in function bodies
            in_func = False
            func_start = 0
            indent_level = 0
            # A sentinel closes the final function at EOF as well as at dedent.
            for i, line in enumerate(lines + ["<EOF>"], 1):
                stripped = line.rstrip()
                if in_func:
                    if stripped == "":
                        continue
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= indent_level and stripped:
                        func_lines = i - func_start - 1
                        if func_lines > 50:
                            result.findings.append(Finding(
                                file=str(path),
                                line=func_start,
                                col=0,
                                pattern=pattern,
                                code=f"Function is {func_lines} lines long",
                            ))
                        in_func = False
                if regex.search(stripped):
                    in_func = True
                    func_start = i
                    indent_level = len(line) - len(line.lstrip())
        elif pattern.id == "pass-in-except":
            for match in regex.finditer(code):
                line_number = code.count("\n", 0, match.start()) + 1
                result.findings.append(Finding(
                    file=str(path), line=line_number, col=0, pattern=pattern,
                    code=lines[line_number - 1].strip()[:100],
                ))
        else:
            searchable = code.splitlines() if pattern.id in call_rules else lines
            for i, line in enumerate(searchable, 1):
                if regex.search(line):
                    result.findings.append(Finding(
                        file=str(path),
                        line=i,
                        col=0,
                        pattern=pattern,
                        code=lines[i - 1].strip()[:100],
                    ))

    return result


def scan_directory(
    target: Path,
    patterns: list[Pattern],
    ignore: list[str] | None = None,
) -> list[FileResult]:
    """Scan all files in a directory."""
    if not target.exists():
        raise ScanError(f"{target} does not exist")
    ignore = ignore or []
    skip = SKIP_DIRS | set(ignore)
    results = []

    files: list[Path] = []
    if target.is_file():
        if should_scan(target):
            files = [target]
    else:
        def walk_error(exc):
            raise ScanError(f"Cannot traverse {exc.filename}: {exc}") from exc

        for root, directories, filenames in os.walk(target, onerror=walk_error):
            # Prune before descending, and only inspect names inside the target.
            directories[:] = [
                name for name in directories
                if not any(fnmatch(name, excluded) for excluded in skip)
            ]
            for name in filenames:
                path = Path(root) / name
                if should_scan(path):
                    files.append(path)

    for f in sorted(files):
        result = scan_file(f, patterns)
        results.append(result)

    return results
