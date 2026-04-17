from __future__ import annotations

import json
from pathlib import Path

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


def test_cli_fixture_run_passes_selected_fixture(monkeypatch, tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text("[]", encoding="utf-8")
    called: dict[str, object] = {}

    def _fake_fixture_main(
        fixture_path: Path | None = None, *, ticks: int = 3, replay_dir: Path = Path("logs/replay")
    ) -> None:
        called["fixture_path"] = fixture_path
        called["ticks"] = ticks
        called["replay_dir"] = replay_dir

    monkeypatch.setattr("scripts.run_runtime_fixture_loop.main", _fake_fixture_main)
    monkeypatch.setattr("sys.argv", ["cli", "fixture-run", "--fixture", str(fixture)])

    rc = cli.main()
    assert rc == 0
    assert called["fixture_path"] == fixture


def test_cli_loop_dry_run_uses_fixture_and_send_margin(monkeypatch, tmp_path: Path, capsys) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "scan": {"myShips": [], "enemyShips": [], "zone": None, "tick": 1},
                    "success": True,
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATASTEAM_SEND_MARGIN_MS", "77")
    monkeypatch.setenv("DATASTEAM_API_KEY", "replace_me")

    captured: dict[str, object] = {}

    class _FakeLoop:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def step(self) -> dict[str, object]:
            return {"success": True}

    monkeypatch.setattr("datsteam_core.runtime.loop.RuntimeLoop", _FakeLoop)
    monkeypatch.setattr(
        "sys.argv",
        ["cli", "datsblack", "loop", "--dry-run", "--ticks", "1", "--fixture", str(fixture)],
    )

    rc = cli.main()
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert payload["results"][0]["success"] is True
    assert payload["manifest"]["policy_id"] == "safe_baseline"
    assert captured["send_margin_ms"] == 77


def test_cli_ops_create_manifest(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "cli",
            "ops",
            "create-manifest",
            "--output",
            str(tmp_path / "run.json"),
            "--policy-id",
            "p1",
            "--mode",
            "training",
            "--environment",
            "local",
        ],
    )
    rc = cli.main()
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["policy_id"] == "p1"
    assert (tmp_path / "run.json").exists()


def test_cli_datssol_dry_run(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "cli",
            "datssol",
            "dry-run",
            "--fixture",
            "tests/fixtures/datssol/arena_sample.json",
        ],
    )
    rc = cli.main()
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["dry_run"] is True
    assert isinstance(out["action"], dict)


def test_cli_datssol_doctor(monkeypatch, capsys) -> None:
    monkeypatch.setenv("DATASTEAM_GAME", "datssol")
    monkeypatch.setenv("DATASTEAM_API_BASE_URL", "https://games-test.datsteam.dev")
    monkeypatch.setenv("DATASTEAM_AUTH_HEADER", "X-Auth-Token")
    monkeypatch.setenv("DATASTEAM_API_KEY", "token")
    monkeypatch.setattr("sys.argv", ["cli", "datssol", "doctor"])
    rc = cli.main()
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["token_loaded"] is True
    assert out["auth_header"] == "X-Auth-Token"
