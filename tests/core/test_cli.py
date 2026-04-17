from __future__ import annotations

import json

from scripts import cli


def test_cli_dry_run_command(monkeypatch, capsys) -> None:
    monkeypatch.setenv("DATASTEAM_API_KEY", "token")
    monkeypatch.setattr("sys.argv", ["cli", "datsblack", "dry-run"])
    code = cli.main()
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert code == 0
    assert payload["dry_run"] is True


def test_cli_requires_auth_for_live_actions(monkeypatch) -> None:
    monkeypatch.setenv("DATASTEAM_API_KEY", "replace_me")
    monkeypatch.setattr("sys.argv", ["cli", "datsblack", "scan"])
    try:
        cli.main()
    except SystemExit as exc:
        assert "Missing auth token" in str(exc)
    else:
        raise AssertionError("Expected SystemExit for missing auth token")
