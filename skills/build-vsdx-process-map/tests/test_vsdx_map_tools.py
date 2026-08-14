from __future__ import annotations

import importlib.util
import math
import re
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "vsdx_map_tools.py"
)
SPEC = importlib.util.spec_from_file_location("vsdx_map_tools", SCRIPT)
assert SPEC and SPEC.loader
TOOLS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOLS)


def shape(
    shape_id: str,
    sid: str | None,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str = "",
    angle: float = 0.0,
    fill: str = "#ffffff",
    one_d: bool = False,
) -> dict:
    cells = [
        {"name": "PinX", "value": str(x)},
        {"name": "PinY", "value": str(y)},
        {"name": "Width", "value": str(width)},
        {"name": "Height", "value": str(height)},
        {"name": "Angle", "value": str(angle)},
        {"name": "FillForegnd", "value": fill},
    ]
    if sid is not None:
        cells.append({"name": "User.VSDXGuardID.Value", "value": sid})
    return {
        "id": shape_id,
        "name": sid or f"shape-{shape_id}",
        "oneD": one_d,
        "text": text,
        "cells": cells,
    }


def page(
    shapes: list[dict],
    *,
    page_id: str = "1",
    width: float = 20.0,
    height: float = 10.0,
) -> dict:
    return {
        "id": page_id,
        "name": "Process",
        "part": "visio/pages/page1.xml",
        "width": width,
        "height": height,
        "shapes": shapes,
    }


class CellTests(unittest.TestCase):
    def test_last_nonempty_cell_value_wins(self) -> None:
        sample = {
            "cells": [
                {"name": "FillForegnd", "value": "#f4cccc"},
                {"name": "FillForegnd", "value": None},
            ]
        }
        self.assertEqual(
            TOOLS.cell_value(sample, "FillForegnd"), "#f4cccc"
        )


class GeometryTests(unittest.TestCase):
    def test_rotated_box_uses_axis_aligned_extent(self) -> None:
        sample = shape(
            "1",
            "page:canvas",
            x=5,
            y=5,
            width=8,
            height=2,
            angle=math.pi / 2,
        )
        box = TOOLS.shape_box(sample)
        assert box
        self.assertAlmostEqual(box["width"], 2.0)
        self.assertAlmostEqual(box["height"], 8.0)

    def test_content_metrics_detect_rotated_canvas_and_page_bloat(self) -> None:
        sample_page = page(
            [
                shape(
                    "1",
                    "page:canvas",
                    x=5,
                    y=15,
                    width=20,
                    height=10,
                    angle=math.pi / 2,
                ),
                shape(
                    "2",
                    "lane:robot:band",
                    x=10,
                    y=5,
                    width=18,
                    height=4,
                ),
            ],
            height=30,
        )
        metrics = TOOLS.content_metrics(sample_page)
        self.assertEqual(len(metrics["rotatedCanvases"]), 1)
        self.assertLess(metrics["heightUse"], 0.2)


class LayoutTests(unittest.TestCase):
    def test_layout_finds_overlap_and_color_outside_status_lane(self) -> None:
        sample_page = page(
            [
                shape(
                    "1",
                    "lane:robot:band",
                    x=10,
                    y=7.5,
                    width=20,
                    height=5,
                ),
                shape(
                    "2",
                    "lane:status:band",
                    x=10,
                    y=2.5,
                    width=20,
                    height=5,
                ),
                shape(
                    "3",
                    "node:first",
                    x=5,
                    y=7.5,
                    width=4,
                    height=2,
                    fill="#e2f0d9",
                ),
                shape(
                    "4",
                    "node:second",
                    x=6,
                    y=7.5,
                    width=4,
                    height=2,
                ),
            ]
        )
        report = TOOLS.page_layout_audit(
            sample_page,
            TOOLS.default_thresholds(),
            set(TOOLS.DEFAULT_ALLOWED_COLORS),
            re.compile(r"^status$", re.IGNORECASE),
        )
        self.assertEqual(
            report["overlaps"], [["node:first", "node:second"]]
        )
        self.assertEqual(
            report["invalidColoredNodes"][0]["id"], "node:first"
        )


class PackageTests(unittest.TestCase):
    def test_zip_metrics_builds_semantic_connector_topology(self) -> None:
        source = shape(
            "1", "node:source", x=2, y=5, width=2, height=1
        )
        target = shape(
            "2", "node:target", x=8, y=5, width=2, height=1
        )
        connector = shape(
            "10",
            "edge:source_to_target",
            x=5,
            y=5,
            width=4,
            height=0,
            text="Continue",
            one_d=True,
        )
        inspection = {
            "pages": [
                page(
                    [source, target, connector],
                    width=10,
                    height=10,
                )
            ]
        }
        page_xml = """\
<PageContents xmlns="http://schemas.microsoft.com/office/visio/2012/main">
  <Shapes/>
  <Connects>
    <Connect FromSheet="10" FromCell="BeginX" ToSheet="1"/>
    <Connect FromSheet="10" FromCell="EndX" ToSheet="2"/>
  </Connects>
</PageContents>
"""
        rels_xml = """\
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="urn:test:master" Target="../masters/master1.xml"/>
</Relationships>
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "sample.vsdx"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("visio/pages/page1.xml", page_xml)
                archive.writestr(
                    "visio/pages/_rels/page1.xml.rels", rels_xml
                )
                archive.writestr("visio/masters/master1.xml", "<Master/>")
            metrics = TOOLS.zip_metrics(package, inspection)

        self.assertTrue(metrics["zipCrcClean"])
        self.assertEqual(metrics["masterPartCount"], 1)
        self.assertEqual(metrics["relationshipTypeCounts"], {"urn:test:master": 1})
        self.assertEqual(
            metrics["connectorTopology"],
            [
                {
                    "pageId": "1",
                    "source": "node:source",
                    "target": "node:target",
                    "label": "Continue",
                }
            ],
        )
        self.assertEqual(len(metrics["connectorTopologySha256"]), 64)


class ComparisonTests(unittest.TestCase):
    def test_diff_normalizes_translation_and_surfaces_semantic_changes(self) -> None:
        baseline_shapes = [
            shape(
                "1",
                "page:canvas",
                x=10,
                y=5,
                width=20,
                height=10,
            ),
            shape(
                "2",
                "lane:robot:band",
                x=10,
                y=7.5,
                width=20,
                height=5,
            ),
            shape(
                "3",
                "lane:status:band",
                x=10,
                y=2.5,
                width=20,
                height=5,
            ),
            shape(
                "4",
                "node:action",
                x=5,
                y=7.5,
                width=4,
                height=2,
                text="Send email",
            ),
            shape(
                "5",
                "edge:action",
                x=7,
                y=7.5,
                width=1,
                height=0,
                one_d=True,
            ),
        ]
        edited_shapes = [
            shape(
                "1",
                "page:canvas",
                x=10,
                y=15,
                width=20,
                height=10,
                angle=math.pi / 2,
            ),
            shape(
                "2",
                "lane:robot:band",
                x=10,
                y=17.5,
                width=20,
                height=5,
            ),
            shape(
                "3",
                "lane:status:band",
                x=10,
                y=12.5,
                width=20,
                height=5,
            ),
            shape(
                "4",
                "node:action",
                x=7,
                y=12.5,
                width=3,
                height=2,
                text="Notify stakeholders",
            ),
            shape(
                "5",
                None,
                x=7,
                y=17.5,
                width=1,
                height=0,
                one_d=True,
            ),
        ]
        baseline = {"pages": [page(baseline_shapes)]}
        edited = {"pages": [page(edited_shapes, height=30)]}

        report = TOOLS.diff_inspections(
            baseline,
            edited,
            tolerance=0.001,
        )

        self.assertEqual(report["globalTranslation"], {"x": 0.0, "y": 10.0})
        self.assertEqual(
            report["semanticIds"]["lost"], ["edge:action"]
        )
        self.assertEqual(
            report["textChanges"][0]["semanticId"], "node:action"
        )
        self.assertEqual(
            report["laneOwnershipChanges"],
            [
                {
                    "semanticId": "node:action",
                    "baseline": "robot",
                    "edited": "status",
                }
            ],
        )
        action_delta = next(
            item
            for item in report["geometryChanges"]
            if item["semanticId"] == "node:action"
        )
        self.assertEqual(action_delta["residualDeltas"]["PinX"], 2.0)
        self.assertEqual(action_delta["residualDeltas"]["PinY"], -5.0)
        canvas_delta = next(
            item
            for item in report["geometryChanges"]
            if item["semanticId"] == "page:canvas"
        )
        self.assertAlmostEqual(
            canvas_delta["residualDeltas"]["Angle"], math.pi / 2
        )


if __name__ == "__main__":
    unittest.main()
