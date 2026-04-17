from __future__ import annotations

from pathlib import Path

from scripts.prepare_datssol_import import _resolve_required_path


def test_resolve_required_path_for_import_dir_file(tmp_path: Path) -> None:
    target_dir = tmp_path / "imports"
    resolved = _resolve_required_path("20260417T180000Z_openapi.json", target_dir=target_dir)
    assert resolved == target_dir / "20260417T180000Z_openapi.json"


def test_resolve_required_path_for_repo_relative_file(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path / "repo"
    truth_table = repo_root / "docs/contract/current_truth_table.md"
    truth_table.parent.mkdir(parents=True, exist_ok=True)
    truth_table.write_text("# ok\n", encoding="utf-8")
    monkeypatch.setattr("scripts.prepare_datssol_import.REPO_ROOT", repo_root)

    resolved = _resolve_required_path("docs/contract/current_truth_table.md", target_dir=tmp_path)

    assert resolved == truth_table
    assert resolved.exists()
