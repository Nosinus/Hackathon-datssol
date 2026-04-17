from __future__ import annotations

import os
import subprocess
import sys


def test_live_module_dry_run_entrypoint() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "games.datssol.live",
            "--dry-run-submit",
            "--ticks",
            "1",
            "--fixture",
            "tests/fixtures/datssol/arena_sample.json",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert '"dry_run": true' in result.stdout
