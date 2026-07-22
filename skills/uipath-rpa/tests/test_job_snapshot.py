from pathlib import Path

from uipath_tooling.job_snapshot import create_snapshot


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
