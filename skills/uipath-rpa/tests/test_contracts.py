from pathlib import Path

from uipath_tooling.contracts import normalize_type, validate_contracts
from uipath_tooling.discovery import all_xaml
from uipath_tooling.xaml_parser import parse_workflow


def _workflows(project: Path):
    return {
        path.relative_to(project).as_posix(): parse_workflow(path, project)
        for path in all_xaml(project)
    }


def test_normalizes_equivalent_decimal_aliases() -> None:
    assert (
        normalize_type("s:Decimal")
        == normalize_type("x:Decimal")
        == normalize_type("System.Decimal")
    )


def test_valid_alias_contract_has_no_finding(valid_project: Path) -> None:
    workflows = _workflows(valid_project)
    assert validate_contracts(valid_project, workflows, {"Main.xaml"}) == []


def test_wrong_direct_child_argument_is_reported(valid_project: Path) -> None:
    main = valid_project / "Main.xaml"
    main.write_text(
        main.read_text().replace('x:Key="in_amount"', 'x:Key="unknown"'),
        encoding="utf-8",
    )
    findings = validate_contracts(
        valid_project, _workflows(valid_project), {"Main.xaml"}
    )
    assert [finding.code for finding in findings] == ["INV002"]


def test_nested_arguments_are_not_counted(valid_project: Path) -> None:
    main = parse_workflow(valid_project / "Main.xaml", valid_project)
    assert [argument.name for argument in main.invokes[0].arguments] == ["in_amount"]
