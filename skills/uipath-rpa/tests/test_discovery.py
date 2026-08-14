import subprocess
from pathlib import Path

from uipath_tooling.discovery import (
    all_xaml,
    load_project_json,
    resolve_project_root,
    scoped_xaml,
)


def test_resolves_project_from_workflow(valid_project: Path) -> None:
    assert (
        resolve_project_root(valid_project / "Tests" / "TC_Child.xaml") == valid_project
    )
    assert load_project_json(valid_project)["name"] == "ValidFixture"


def test_all_scope_finds_every_workflow(valid_project: Path) -> None:
    names = {
        path.relative_to(valid_project).as_posix() for path in all_xaml(valid_project)
    }
    assert names == {"Main.xaml", "Child.xaml", "Tests/TC_Child.xaml"}
    assert scoped_xaml(valid_project, "all") == all_xaml(valid_project)


def test_changed_scope_includes_staged_unstaged_and_untracked(
    valid_project: Path,
) -> None:
    subprocess.run(["git", "init", "-q", str(valid_project)], check=True)
    subprocess.run(["git", "-C", str(valid_project), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(valid_project),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    (valid_project / "Main.xaml").write_text(
        (valid_project / "Main.xaml").read_text() + "\n"
    )
    (valid_project / "Child.xaml").write_text(
        (valid_project / "Child.xaml").read_text() + "\n"
    )
    subprocess.run(
        ["git", "-C", str(valid_project), "add", "Child.xaml"], check=True
    )
    (valid_project / "New.xaml").write_text("<Activity />\n")

    names = {
        path.relative_to(valid_project).as_posix()
        for path in scoped_xaml(valid_project, "changed")
    }
    assert names == {"Child.xaml", "Main.xaml", "New.xaml"}
