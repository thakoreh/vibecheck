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


def test_multiline_silent_exception(tmp_path):
    target = _write_tmp(tmp_path, "silent.py", "try:\n    work()\nexcept ValueError:\n    pass\n")
    matches = [f for f in scan_file(target, AI_SMELLS).findings if f.pattern.id == "pass-in-except"]
    assert [f.line for f in matches] == [3]


def test_long_function_at_eof_and_before_next_function(tmp_path):
    content = "def calculate():\n" + "    step()\n" * 55
    for ending in ("", "\ndef next_function():\n    pass\n"):
        target = _write_tmp(tmp_path, "long.py", content + ending)
        matches = [f for f in scan_file(target, AI_SMELLS).findings if f.pattern.id == "long-function"]
        assert [f.line for f in matches] == [1]


def test_python_comments_strings_and_used_import_are_not_dangerous_calls(tmp_path):
    target = _write_tmp(tmp_path, "safe.py", '# eval(user_input)\nmessage = "eval(user_input)"\nimport os\nprint(os.name)\n')
    matches = scan_file(target, AI_SMELLS + SECURITY_PATTERNS).findings
    assert not {f.pattern.id for f in matches} & {"eval-usage", "unused-import"}


def test_real_call_after_string_still_detected(tmp_path):
    target = _write_tmp(tmp_path, "danger.py", 'message = "example"; eval(user_input)\n')
    matches = [f for f in scan_file(target, SECURITY_PATTERNS).findings if f.pattern.id == "eval-usage"]
    assert [f.line for f in matches] == [1]


def test_unsupported_files_do_not_inflate_scan_metrics(tmp_path):
    _write_tmp(tmp_path, "README.md", "hello\n")
    _write_tmp(tmp_path, "source.py", "pass\n")
    assert [Path(r.path).name for r in scan_directory(tmp_path, AI_SMELLS)] == ["source.py"]


def test_ignore_applies_relative_to_target_not_ancestors(tmp_path):
    target = tmp_path / "build" / "project"
    _write_tmp(target, "source.py", "eval(user_input)\n")
    assert len(scan_directory(target, SECURITY_PATTERNS)) == 1


def test_ignore_prunes_generated_directories(tmp_path):
    _write_tmp(tmp_path, "sample.egg-info/metadata.py", "eval(user_input)\n")
    _write_tmp(tmp_path, "generated/danger.py", "eval(user_input)\n")
    _write_tmp(tmp_path, "app.py", "pass\n")
    assert len(scan_directory(tmp_path, SECURITY_PATTERNS, ignore=["generated"])) == 1


def test_unsafe_yaml_loader_does_not_bypass_rule(tmp_path):
    for loader in ("yaml.Loader", "yaml.UnsafeLoader"):
        target = _write_tmp(tmp_path, "yaml_input.py", f"yaml.load(payload, Loader={loader})\n")
        assert "unsafe-yaml" in {f.pattern.id for f in scan_file(target, SECURITY_PATTERNS).findings}
    for loader in ("yaml.SafeLoader", "yaml.CSafeLoader"):
        target = _write_tmp(tmp_path, "yaml_input.py", f"yaml.load(payload, Loader={loader})\n")
        assert "unsafe-yaml" not in {f.pattern.id for f in scan_file(target, SECURITY_PATTERNS).findings}


def test_invalid_encoding_fails_explicitly(tmp_path):
    import pytest
    from vibecheck.scanner import ScanError

    target = tmp_path / "broken.py"
    target.write_bytes(b"eval(\xff)\n")
    with pytest.raises(ScanError, match="Cannot read"):
        scan_file(target, SECURITY_PATTERNS)


def test_eval_detected_in_every_supported_language(tmp_path):
    for extension in (".py", ".js", ".jsx", ".ts", ".tsx"):
        target = _write_tmp(tmp_path, "unsafe" + extension, "eval(user_input)\n")
        assert "eval-usage" in {f.pattern.id for f in scan_file(target, SECURITY_PATTERNS).findings}


def test_python_fstring_executable_interpolation_is_not_hidden(tmp_path):
    target = _write_tmp(tmp_path, "interpolated.py", 'print(f"answer: {eval(user_input)}")\n')
    assert "eval-usage" in {f.pattern.id for f in scan_file(target, SECURITY_PATTERNS).findings}
