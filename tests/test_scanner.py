"""Tests for vibecheck scanner."""

import tempfile
from pathlib import Path

from vibecheck.patterns import AI_SMELLS, SECURITY_PATTERNS
from vibecheck.scanner import scan_directory, scan_file
from vibecheck.scorer import calculate_score


def _write_tmp(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def test_detects_bare_except():
    with tempfile.TemporaryDirectory() as tmp:
        _write_tmp(Path(tmp), "bad.py", "try:\n    x = 1\nexcept:\n    pass\n")
        results = scan_directory(Path(tmp), AI_SMELLS)
        findings = [f for r in results for f in r.findings if f.pattern.id == "bare-except"]
        assert len(findings) >= 1


def test_detects_hardcoded_secret():
    with tempfile.TemporaryDirectory() as tmp:
        _write_tmp(Path(tmp), "config.py", 'api_key = "sk-1234567890abcdef"\n')
        results = scan_directory(Path(tmp), SECURITY_PATTERNS)
        findings = [f for r in results for f in r.findings if f.pattern.id == "hardcoded-secret"]
        assert len(findings) >= 1


def test_detects_eval():
    with tempfile.TemporaryDirectory() as tmp:
        _write_tmp(Path(tmp), "danger.py", 'result = eval(user_input)\n')
        results = scan_directory(Path(tmp), SECURITY_PATTERNS)
        findings = [f for r in results for f in r.findings if f.pattern.id == "eval-usage"]
        assert len(findings) >= 1


def test_detects_console_log():
    with tempfile.TemporaryDirectory() as tmp:
        _write_tmp(Path(tmp), "debug.js", 'console.log("debug here");\n')
        results = scan_directory(Path(tmp), AI_SMELLS)
        findings = [f for r in results for f in r.findings if f.pattern.id == "js-console-log"]
        assert len(findings) >= 1


def test_detects_placeholder_vars():
    with tempfile.TemporaryDirectory() as tmp:
        _write_tmp(Path(tmp), "vague.py", "temp = get_data()\nresult = process(temp)\n")
        results = scan_directory(Path(tmp), AI_SMELLS)
        findings = [f for r in results for f in r.findings if f.pattern.id == "placeholder-var"]
        assert len(findings) >= 1


def test_score_perfect():
    with tempfile.TemporaryDirectory() as tmp:
        _write_tmp(Path(tmp), "clean.py", "def add(a: int, b: int) -> int:\n    return a + b\n")
        _write_tmp(Path(tmp), "test_clean.py", "def test_add():\n    assert add(1, 2) == 3\n")
        results = scan_directory(Path(tmp), AI_SMELLS + SECURITY_PATTERNS)
        score = calculate_score(results)
        assert score.score >= 90


def test_score_drops_with_critical():
    with tempfile.TemporaryDirectory() as tmp:
        _write_tmp(Path(tmp), "bad.py", 'api_key = "sk-super-secret-key-12345"\nresult = eval(data)\n')
        results = scan_directory(Path(tmp), SECURITY_PATTERNS)
        score = calculate_score(results)
        assert score.score < 80


def test_skips_node_modules():
    with tempfile.TemporaryDirectory() as tmp:
        _write_tmp(Path(tmp), "node_modules/pkg/index.js", 'console.log("hidden");\n')
        _write_tmp(Path(tmp), "src/app.js", '// clean code\n')
        results = scan_directory(Path(tmp), AI_SMELLS)
        assert all("node_modules" not in r.path for r in results)


def test_json_output():
    from vibecheck.reporter import report_json
    with tempfile.TemporaryDirectory() as tmp:
        _write_tmp(Path(tmp), "test.py", "try:\n    x = 1\nexcept:\n    pass\n")
        results = scan_directory(Path(tmp), SECURITY_PATTERNS + AI_SMELLS)
        score = calculate_score(results)
        output = report_json(results, score)
        assert "score" in output
        assert "issues" in output
        assert isinstance(output["issues"], list)
