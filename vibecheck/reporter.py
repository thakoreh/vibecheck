"""Reporter - formats and displays scan results."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .scanner import FileResult, Finding
from .scorer import ScoreResult


SEVERITY_STYLE = {
    "critical": "bold red",
    "warning": "yellow",
    "info": "dim cyan",
}

SEVERITY_ICON = {
    "critical": "🚨",
    "warning": "⚠️",
    "info": "💡",
}


def _relative_path(filepath: str) -> str:
    """Make path relative to cwd."""
    try:
        return str(Path(filepath).relative_to(Path.cwd()))
    except ValueError:
        return filepath


def report_rich(
    results: list[FileResult],
    score: ScoreResult,
    target: str,
    json_output: bool = False,
) -> None:
    """Print a rich terminal report."""
    console = Console()

    # Header
    console.print()
    console.print(
        Panel(
            f"[bold]VibeCheck[/bold] — AI Code Quality Scanner",
            style="blue",
            padding=(0, 2),
        )
    )
    console.print(f"\n  Scanning [cyan]{target}[/cyan]...\n")

    # Collect all findings
    all_findings: list[Finding] = []
    for r in results:
        all_findings.extend(r.findings)

    # Group by severity
    critical = [f for f in all_findings if f.pattern.severity == "critical"]
    warnings = [f for f in all_findings if f.pattern.severity == "warning"]
    infos = [f for f in all_findings if f.pattern.severity == "info"]

    # ── Score Panel ─────────────────────────────────────────────
    score_color = "green" if score.score >= 75 else "yellow" if score.score >= 50 else "red"
    console.print(
        Panel(
            f"[bold {score_color}]{score.score}/100[/bold {score_color}]  "
            f"{score.emoji}  Grade {score.grade}\n\n"
            f"{score.message}",
            title="[bold]Vibe Score[/bold]",
            border_style=score_color,
            padding=(1, 2),
        )
    )

    # ── Stats ───────────────────────────────────────────────────
    console.print(
        f"\n  [dim]{score.total_files} files · {score.total_lines} lines · "
        f"{score.total_findings} findings[/dim]\n"
    )

    # ── Security Issues ─────────────────────────────────────────
    if critical:
        console.print(f"  🚨 [bold red]Security Issues ({len(critical)})[/bold red]")
        _print_findings(console, critical, indent="    ")
        console.print()

    # ── Warnings ────────────────────────────────────────────────
    if warnings:
        console.print(f"  ⚠️  [yellow]AI Code Smells ({len(warnings)})[/yellow]")
        _print_findings(console, warnings, indent="    ")
        console.print()

    # ── Info ────────────────────────────────────────────────────
    if infos:
        console.print(f"  💡 [dim cyan]Suggestions ({len(infos)})[/dim cyan]")
        _print_findings(console, infos, indent="    ", show_suggestion=False)
        console.print()

    # ── Top Files by Issues ─────────────────────────────────────
    file_issues = {}
    for r in results:
        count = len(r.findings)
        if count > 0:
            file_issues[_relative_path(r.path)] = count

    if file_issues:
        sorted_files = sorted(file_issues.items(), key=lambda x: x[1], reverse=True)[:5]
        console.print("  📁 [bold]Top Files by Issues[/bold]")
        for filepath, count in sorted_files:
            bar = "█" * min(count, 20)
            console.print(f"    [dim]{filepath}[/dim] {bar} {count}")
        console.print()

    # ── Quick Wins ──────────────────────────────────────────────
    quick_wins = _get_quick_wins(all_findings)
    if quick_wins:
        console.print("  ⚡ [bold green]Quick Wins[/bold green]")
        for win in quick_wins[:5]:
            console.print(f"    [green]•[/green] {win}")
        console.print()

    # ── Footer ──────────────────────────────────────────────────
    if score.total_findings == 0:
        console.print(
            Panel(
                "No issues found. Your code is clean!\n\n"
                "Either you write great code, or the AI is getting really good.",
                style="green",
                padding=(1, 2),
            )
        )
    console.print(
        f"  [dim]Run with --json for machine-readable output[/dim]\n"
    )


def _print_findings(
    console: Console,
    findings: list[Finding],
    indent: str = "  ",
    show_suggestion: bool = True,
    max_items: int = 15,
) -> None:
    """Print a list of findings."""
    # Deduplicate by pattern id + file
    seen = set()
    unique = []
    for f in findings:
        key = (f.pattern.id, _relative_path(f.file), f.line)
        if key not in seen:
            seen.add(key)
            unique.append(f)

    for i, f in enumerate(unique[:max_items]):
        path = _relative_path(f.file)
        style = SEVERITY_STYLE.get(f.pattern.severity, "white")

        console.print(
            f"{indent}[{style}]{f.pattern.name}[/{style}] "
            f"[dim]{path}:{f.line}[/dim]"
        )
        if show_suggestion and f.pattern.suggestion:
            console.print(f"{indent}  [dim]→ {f.pattern.suggestion}[/dim]")

    remaining = len(unique) - max_items
    if remaining > 0:
        console.print(f"{indent}[dim]... and {remaining} more[/dim]")


def _get_quick_wins(findings: list[Finding]) -> list[str]:
    """Generate actionable quick wins."""
    wins = []
    seen_ids = set()

    for f in findings:
        pid = f.pattern.id
        if pid in seen_ids:
            continue
        seen_ids.add(pid)

        if pid == "hardcoded-secret":
            wins.append("Move secrets to environment variables or .env file")
        elif pid == "broad-except":
            wins.append("Replace generic exception handlers with specific ones")
        elif pid == "bare-except":
            wins.append("Fix bare except clauses - they swallow everything")
        elif pid == "eval-usage":
            wins.append("Replace eval() with safe alternatives")
        elif pid == "shell-true":
            wins.append("Remove shell=True from subprocess calls")
        elif pid == "sql-concat":
            wins.append("Switch to parameterized SQL queries")
        elif pid == "placeholder-var":
            wins.append("Rename placeholder variables to descriptive names")
        elif pid == "js-console-log":
            wins.append("Remove debug console.log statements")
        elif pid == "todo-left-in":
            wins.append("Resolve TODO/FIXME comments or create issues")

    return wins


def report_json(
    results: list[FileResult],
    score: ScoreResult,
) -> dict:
    """Generate JSON output."""
    findings_list = []
    for r in results:
        for f in r.findings:
            findings_list.append({
                "file": _relative_path(f.file),
                "line": f.line,
                "severity": f.pattern.severity,
                "rule": f.pattern.id,
                "name": f.pattern.name,
                "description": f.pattern.description,
                "suggestion": f.pattern.suggestion,
                "code": f.code,
            })

    return {
        "score": score.score,
        "grade": score.grade,
        "message": score.message,
        "files_scanned": score.total_files,
        "lines_scanned": score.total_lines,
        "findings": {
            "total": score.total_findings,
            "critical": score.critical_count,
            "warnings": score.warning_count,
            "info": score.info_count,
        },
        "issues": findings_list,
    }
