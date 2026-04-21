"""Scoring engine - calculates the vibe score."""

from dataclasses import dataclass

from .scanner import FileResult, Finding

SEVERITY_WEIGHTS = {
    "critical": 15,
    "warning": 5,
    "info": 1,
}

SEVERITY_CAPS = {
    "critical": 60,  # max points deducted for critical
    "warning": 40,   # max points deducted for warnings
    "info": 15,      # max points deducted for info
}


@dataclass
class ScoreResult:
    score: int
    total_files: int
    total_lines: int
    total_findings: int
    critical_count: int
    warning_count: int
    info_count: int
    grade: str
    emoji: str
    message: str


def calculate_score(results: list[FileResult]) -> ScoreResult:
    """Calculate vibe score from scan results."""
    total_files = len(results)
    total_lines = sum(r.lines_total for r in results)

    all_findings: list[Finding] = []
    for r in results:
        all_findings.extend(r.findings)

    critical = sum(1 for f in all_findings if f.pattern.severity == "critical")
    warnings = sum(1 for f in all_findings if f.pattern.severity == "warning")
    info = sum(1 for f in all_findings if f.pattern.severity == "info")

    # Calculate deductions
    critical_deduction = min(critical * SEVERITY_WEIGHTS["critical"], SEVERITY_CAPS["critical"])
    warning_deduction = min(warnings * SEVERITY_WEIGHTS["warning"], SEVERITY_CAPS["warning"])
    info_deduction = min(info * SEVERITY_WEIGHTS["info"], SEVERITY_CAPS["info"])

    total_deduction = critical_deduction + warning_deduction + info_deduction

    # Bonus for having tests
    has_tests = any("test" in r.path.lower() for r in results)
    test_bonus = 5 if has_tests else 0

    # Bonus for small files (indicates modular code)
    avg_lines = total_lines / max(total_files, 1)
    size_bonus = 5 if avg_lines < 100 else 0

    raw_score = 100 - total_deduction + test_bonus + size_bonus
    score = max(0, min(100, raw_score))

    # Determine grade and message
    if score >= 90:
        grade, emoji, message = "A", "🟢", "Clean code. You understand what you shipped."
    elif score >= 75:
        grade, emoji, message = "B", "🟡", "Mostly solid. A few things to clean up."
    elif score >= 60:
        grade, emoji, message = "C", "🟠", "Getting shaky. Review the warnings before deploying."
    elif score >= 40:
        grade, emoji, message = "D", "🔴", "Rough. You probably vibe-coded this. Go review."
    else:
        grade, emoji, message = "F", "💀", "Did you even read the code before shipping?"

    return ScoreResult(
        score=score,
        total_files=total_files,
        total_lines=total_lines,
        total_findings=len(all_findings),
        critical_count=critical,
        warning_count=warnings,
        info_count=info,
        grade=grade,
        emoji=emoji,
        message=message,
    )
