"""VibeCheck CLI - Audit your AI-generated code."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .patterns import AI_SMELLS, SECURITY_PATTERNS
from .reporter import report_json, report_rich
from .scanner import scan_directory
from .scorer import calculate_score

app = typer.Typer(
    name="vibecheck",
    help="Audit your AI-generated code. Catch anti-patterns, security issues, and get a vibe score.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"vibecheck {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version.",
    ),
):
    pass


@app.command()
def scan(
    target: str = typer.Argument(".", help="Directory or file to scan."),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON."),
    security_only: bool = typer.Option(False, "--security", "-s", help="Security issues only."),
    smells_only: bool = typer.Option(False, "--smells", help="AI code smells only."),
    ignore: Optional[list[str]] = typer.Option(None, "--ignore", "-i", help="Directories to ignore."),
    no_security: bool = typer.Option(False, "--no-security", help="Skip security checks."),
    no_smells: bool = typer.Option(False, "--no-smells", help="Skip AI smell checks."),
):
    """Scan code for AI-generated anti-patterns and security issues."""
    path = Path(target).resolve()

    if not path.exists():
        console.print(f"[red]Error: {target} does not exist[/red]")
        raise typer.Exit(1)

    # Select patterns
    patterns = []
    if security_only:
        patterns = SECURITY_PATTERNS
    elif smells_only:
        patterns = AI_SMELLS
    else:
        if not no_security:
            patterns.extend(SECURITY_PATTERNS)
        if not no_smells:
            patterns.extend(AI_SMELLS)

    # Scan
    results = scan_directory(path, patterns, ignore=ignore or [])
    score = calculate_score(results)

    # Output
    if json_out:
        output = report_json(results, score)
        print(json.dumps(output, indent=2))
    else:
        report_rich(results, score, target)

    # Exit with non-zero if critical issues found
    if score.critical_count > 0:
        raise typer.Exit(2)
    elif score.score < 60:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
