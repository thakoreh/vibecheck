"""Code scanner - walks directories and matches patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
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


def should_scan(path: Path) -> bool:
    """Check if a file should be scanned."""
    if path.suffix in SKIP_EXTENSIONS:
        return False
    if any(part.endswith(".min.js") or part.endswith(".min.css") for part in path.parts):
        return False
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return False
    except OSError:
        return False
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


def scan_file(path: Path, patterns: list[Pattern]) -> FileResult:
    """Scan a single file against given patterns."""
    result = FileResult(
        path=str(path),
        language=get_language(path),
        lines_total=0,
    )

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return result

    lines = content.splitlines()
    result.lines_total = len(lines)

    ext = path.suffix

    for pattern in patterns:
        if ext not in pattern.languages:
            continue

        try:
            regex = re.compile(pattern.pattern, re.IGNORECASE)
        except re.error:
            continue

        if pattern.id == "long-function":
            # Special handling: count lines in function bodies
            in_func = False
            func_start = 0
            indent_level = 0
            for i, line in enumerate(lines, 1):
                stripped = line.rstrip()
                if regex.search(stripped):
                    in_func = True
                    func_start = i
                    indent_level = len(line) - len(line.lstrip())
                    continue
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
        else:
            for i, line in enumerate(lines, 1):
                if regex.search(line):
                    result.findings.append(Finding(
                        file=str(path),
                        line=i,
                        col=0,
                        pattern=pattern,
                        code=line.strip()[:100],
                    ))

    return result


def scan_directory(
    target: Path,
    patterns: list[Pattern],
    ignore: list[str] | None = None,
) -> list[FileResult]:
    """Scan all files in a directory."""
    ignore = ignore or []
    skip = SKIP_DIRS | set(ignore)
    results = []

    files: list[Path] = []
    if target.is_file():
        files = [target]
    else:
        for path in target.rglob("*"):
            if any(part in skip for part in path.parts):
                continue
            if path.is_file() and should_scan(path):
                files.append(path)

    for f in sorted(files):
        result = scan_file(f, patterns)
        if result.lines_total > 0:
            results.append(result)

    return results
