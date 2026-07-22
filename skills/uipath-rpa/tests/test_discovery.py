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
