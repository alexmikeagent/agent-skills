from pathlib import Path

from uipath_tooling.discovery import all_xaml, load_project_json
from uipath_tooling.workflow_graph import mermaid, project_map
from uipath_tooling.xaml_parser import parse_workflow


def test_graph_contains_real_invoke_edge(valid_project: Path) -> None:
    workflows = {
        path.relative_to(valid_project).as_posix(): parse_workflow(path, valid_project)
        for path in all_xaml(valid_project)
    }
    value = project_map(load_project_json(valid_project), workflows, valid_project)
    assert {edge["callee"] for edge in value["edges"]} == {"Child.xaml"}
    assert "Main.xaml" in mermaid(value)
    assert value["schema"] == "uipath-project-map/v1"
    child = next(node for node in value["nodes"] if node["path"] == "Child.xaml")
    assert child["argument_contracts"] == [
        {"name": "in_amount", "direction": "In", "type": "s:Decimal"}
    ]
