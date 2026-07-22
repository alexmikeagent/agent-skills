from pathlib import Path

from uipath_tooling.expressions import parenthesis_error
from uipath_tooling.xaml_parser import parse_workflow
from uipath_tooling.expressions import check_workflow


def test_parenthesis_and_string_hazards() -> None:
    assert parenthesis_error("If(flag, 1, 0") == "has 1 unclosed parenthesis(es)"
    assert (
        parenthesis_error('"unterminated')
        == "contains an unterminated VB string literal"
    )
    assert parenthesis_error("If(flag, 1, 0)") is None


def test_unqualified_regex_requires_import(valid_project: Path) -> None:
    main = valid_project / "Main.xaml"
    main.write_text(
        main.read_text().replace("[1D]", '[Regex.IsMatch("x", "x") ? 1D : 0D]'),
        encoding="utf-8",
    )
    workflow = parse_workflow(main, valid_project)
    assert "VB003" in {finding.code for finding in check_workflow(workflow)}
