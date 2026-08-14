from pathlib import Path

import subprocess

import pytest

from uipath_tooling.job_snapshot import SnapshotSafetyError, create_snapshot


def test_snapshot_hashes_project_files_and_excludes_git(
    valid_project: Path, tmp_path: Path
) -> None:
    (valid_project / ".git").mkdir()
    (valid_project / ".git" / "secret").write_text("no")
    destination = tmp_path / "snapshot"
    manifest = create_snapshot(valid_project, destination)
    names = {item["path"] for item in manifest["files"]}
    assert "project.json" in names
    assert ".git/secret" not in names
    assert (destination / ".uipath-snapshot.json").is_file()


def test_snapshot_includes_safe_untracked_source_files_in_git_project(
    valid_project: Path, tmp_path: Path
) -> None:
    subprocess.run(["git", "init", "-q", str(valid_project)], check=True)
    subprocess.run(["git", "-C", str(valid_project), "add", "."], check=True)
    (valid_project / "untracked.xaml").write_text("<Activity />")
    manifest = create_snapshot(valid_project, tmp_path / "snapshot")
    names = {item["path"] for item in manifest["files"]}
    assert "Main.xaml" in names
    assert "untracked.xaml" in names


def test_snapshot_fails_closed_on_untracked_non_source_file(
    valid_project: Path, tmp_path: Path
) -> None:
    subprocess.run(["git", "init", "-q", str(valid_project)], check=True)
    subprocess.run(["git", "-C", str(valid_project), "add", "."], check=True)
    (valid_project / "input.xlsx").write_bytes(b"not-a-real-workbook")
    with pytest.raises(SnapshotSafetyError, match="untracked non-source"):
        create_snapshot(valid_project, tmp_path / "snapshot")


def test_snapshot_refuses_to_silently_drop_tracked_excluded_file(
    valid_project: Path, tmp_path: Path
) -> None:
    (valid_project / "outputs").mkdir()
    (valid_project / "outputs" / "evidence.json").write_text("{}")
    subprocess.run(["git", "init", "-q", str(valid_project)], check=True)
    subprocess.run(["git", "-C", str(valid_project), "add", "."], check=True)
    with pytest.raises(SnapshotSafetyError, match="refuses to omit tracked"):
        create_snapshot(valid_project, tmp_path / "snapshot")


def test_snapshot_fails_closed_on_credential_like_file(
    valid_project: Path, tmp_path: Path
) -> None:
    (valid_project / ".env").write_text("TOKEN=do-not-copy")
    with pytest.raises(SnapshotSafetyError, match="credential-like"):
        create_snapshot(valid_project, tmp_path / "snapshot")
    assert not (tmp_path / "snapshot").exists()
