"""Exercise CLI decisions as users see them, including machine-readable errors."""

import json
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vibecheck.cli import app

runner = CliRunner()


@pytest.mark.parametrize("args,code", [(["--help"], 0), ([], 2), (["scan", "--help"], 0)])
def test_help(args, code):
    result = runner.invoke(app, args)
    assert result.exit_code == code
    assert "Usage:" in result.output


def test_version_matches_distribution():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"vibechecker {version('vibechecker')}"


@pytest.mark.parametrize("kind", ["missing", "empty", "unsupported", "oversized"])
def test_unscannable_targets_are_errors(tmp_path, kind):
    target = tmp_path / "input"
    if kind == "empty":
        target.mkdir()
    elif kind == "unsupported":
        target = target.with_suffix(".md")
        target.write_text("documentation\n", encoding="utf-8")
    elif kind == "oversized":
        target = target.with_suffix(".py")
        target.write_text(" " * 500_001, encoding="utf-8")
    result = runner.invoke(app, ["scan", str(target), "--json"])
    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["error"]
    assert "score" not in payload


def test_read_failure_is_not_clean_success(tmp_path, monkeypatch):
    target = tmp_path / "denied.py"
    target.write_text("pass\n", encoding="utf-8")
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path == target:
            raise PermissionError("synthetic permission failure")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    result = runner.invoke(app, ["scan", str(target), "--json"])
    assert result.exit_code == 3
    assert "Cannot read" in json.loads(result.stdout)["error"]


@pytest.mark.parametrize("flags", [
    ["--security", "--smells"], ["--security", "--no-security"],
    ["--smells", "--no-smells"], ["--no-security", "--no-smells"],
])
def test_conflicting_or_empty_rules_are_errors(tmp_path, flags):
    target = tmp_path / "source.py"
    target.write_text("pass\n", encoding="utf-8")
    result = runner.invoke(app, ["scan", str(target), "--json", *flags])
    assert result.exit_code == 3
    assert json.loads(result.stdout)["error"]


def test_repeated_critical_and_filtered_scans(tmp_path):
    target = tmp_path / "unsafe.py"
    target.write_text("value = eval(user_input)\n", encoding="utf-8")
    for _ in range(2):
        result = runner.invoke(app, ["scan", str(target), "--json"])
        assert result.exit_code == 2
        assert json.loads(result.stdout)["findings"]["critical"] == 1
        filtered = runner.invoke(app, ["scan", str(target), "--json", "--no-security"])
        assert filtered.exit_code == 0
        assert json.loads(filtered.stdout)["findings"]["critical"] == 0


def test_empty_supported_file_is_scanned(tmp_path):
    target = tmp_path / "empty.py"
    target.touch()
    result = runner.invoke(app, ["scan", str(target), "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["files_scanned"] == 1


def test_rich_report_works_with_legacy_terminal_encoding(tmp_path):
    target = tmp_path / "[source].py"
    target.write_text("eval(user_input)\n", encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING="cp1252", NO_COLOR="1")
    result = subprocess.run(
        [sys.executable, "-m", "vibecheck.cli", "scan", str(target)],
        capture_output=True, env=env,
    )
    assert result.returncode == 2, result.stderr.decode("cp1252")
    assert b"eval() Usage" in result.stdout
    assert b"[source].py" in result.stdout


def test_interrupted_scan_does_not_emit_score_and_can_be_repeated(tmp_path, monkeypatch):
    target = tmp_path / "safe.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt()

    with monkeypatch.context() as patch:
        patch.setattr("vibecheck.cli.scan_directory", interrupt)
        result = runner.invoke(app, ["scan", str(target), "--json"])
    assert result.exit_code != 0
    assert '"score"' not in result.stdout
    assert runner.invoke(app, ["scan", str(target), "--json"]).exit_code == 0
