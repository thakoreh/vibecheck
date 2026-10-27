"""Run against an installed distribution, outside the source checkout.

Usage: python tests/package_smoke.py
Run after installing the wheel or sdist into the active environment.
"""

import json
from importlib.metadata import version
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile


def main():
    executable = Path(sysconfig.get_path("scripts")) / (
        "vibechecker.exe" if os.name == "nt" else "vibechecker"
    )
    checkout = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        home = root / "home"
        home.mkdir()
        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                   XDG_CONFIG_HOME=str(home / "config"), PYTHONPATH="", NO_COLOR="1")

        def run(args, expected):
            result = subprocess.run([str(executable), *args], cwd=root, env=env,
                                    capture_output=True, text=True)
            expected_codes = (expected,) if isinstance(expected, int) else expected
            assert result.returncode in expected_codes, (args, result.returncode, result.stdout, result.stderr)
            return result.stdout

        # Verify that this tests an installed copy, rather than the working tree.
        origin = subprocess.check_output(
            [sys.executable, "-c", "import vibecheck; print(vibecheck.__file__)"],
            cwd=root, env=env, text=True,
        ).strip()
        assert checkout not in Path(origin).resolve().parents, origin
        run(["--help"], 0)
        run([], (0, 2))  # Older Typer on Python 3.9 returns 0 after showing help.
        assert run(["--version"], 0).strip() == f"vibechecker {version('vibechecker')}"
        target = root / "source.py"
        target.write_text("print('hello')\n", encoding="utf-8")
        assert json.loads(run(["scan", "--json"], 0))["files_scanned"] == 1
        assert "No configured patterns found" in run(["scan", str(target)], 0)
        target.write_text("eval(user_input)\n", encoding="utf-8")
        for _ in range(2):
            assert json.loads(run(["scan", str(target), "--json"], 2))["findings"]["critical"] == 1
        assert json.loads(run(["scan", str(target), "--json", "--no-security"], 0))["findings"]["critical"] == 0
        assert json.loads(run(["scan", str(root / "missing"), "--json"], 3))["error"]
        empty = root / "empty"
        empty.mkdir()
        assert json.loads(run(["scan", str(empty), "--json"], 3))["error"]
        print(f"Installed package smoke passed: {origin}")


if __name__ == "__main__":
    main()
