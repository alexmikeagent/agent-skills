#!/usr/bin/env python3
"""Compare and audit VSDX Guard process maps."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree


DEFAULT_ALLOWED_COLORS = ("#e2f0d9", "#f4cccc")
WHITE_FILLS = {"", "#fff", "#ffffff", "none", "transparent"}
POINT_CELLS = ("PinX", "PinY", "Width", "Height", "Angle")
STYLE_CELLS = (
    "FillForegnd",
    "LineColor",
    "LinePattern",
    "LineWeight",
    "Character.0.Size",
    "Character.0.Style",
)
ENDPOINT_CELLS = ("BeginX", "BeginY", "EndX", "EndY")


class ToolError(RuntimeError):
    """A user-facing tool failure."""


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def cell_entries(shape: dict[str, Any], name: str) -> list[dict[str, Any]]:
    return [cell for cell in shape.get("cells", []) if cell.get("name") == name]


def cell_value(
    shape: dict[str, Any],
    name: str,
    *,
    nonempty: bool = True,
) -> Any:
    entries = cell_entries(shape, name)
    for cell in reversed(entries):
        value = cell.get("value")
        if not nonempty or value not in (None, ""):
            return value
    return None


def cell_formula(shape: dict[str, Any], name: str) -> str:
    entries = cell_entries(shape, name)
    for cell in reversed(entries):
        formula = cell.get("formula")
        if formula not in (None, ""):
            return str(formula)
    return ""


def numeric_cell(shape: dict[str, Any], name: str) -> float | None:
    value = cell_value(shape, name)
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def semantic_id(shape: dict[str, Any]) -> str:
    value = cell_value(shape, "User.VSDXGuardID.Value")
    return str(value) if value not in (None, "") else ""


def shape_box(shape: dict[str, Any]) -> dict[str, float] | None:
    x = numeric_cell(shape, "PinX")
    y = numeric_cell(shape, "PinY")
    width = numeric_cell(shape, "Width")
    height = numeric_cell(shape, "Height")
    angle = numeric_cell(shape, "Angle") or 0.0
    if None in (x, y, width, height):
        return None

    half_width = abs(width) / 2
    half_height = abs(height) / 2
    cos_angle = abs(math.cos(angle))
    sin_angle = abs(math.sin(angle))
    extent_x = half_width * cos_angle + half_height * sin_angle
    extent_y = half_width * sin_angle + half_height * cos_angle
    return {
        "left": x - extent_x,
        "right": x + extent_x,
        "bottom": y - extent_y,
        "top": y + extent_y,
        "centerX": x,
        "centerY": y,
        "width": extent_x * 2,
        "height": extent_y * 2,
    }


def shape_label(shape: dict[str, Any]) -> str:
    return semantic_id(shape) or str(shape.get("name") or f"shape:{shape.get('id')}")


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ToolError(f"{' '.join(command)} failed: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ToolError(
            f"{' '.join(command)} did not return JSON: {completed.stdout[:500]}"
        ) from exc
    if not isinstance(payload, dict):
        raise ToolError(f"{' '.join(command)} returned a non-object JSON value")
    return payload


def resolve_vsdx_binary(value: str | None) -> str:
    candidate = value or shutil.which("vsdx")
    if not candidate:
        raise ToolError("vsdx was not found on PATH; pass --vsdx /absolute/path")
    path = Path(candidate).expanduser()
    if not path.is_file():
        raise ToolError(f"vsdx binary does not exist: {path}")
    return str(path.resolve())


def inspect_vsdx(vsdx_binary: str, path: Path) -> dict[str, Any]:
    return run_json([vsdx_binary, "inspect", str(path)])


def validate_vsdx(vsdx_binary: str, path: Path) -> dict[str, Any]:
    return run_json([vsdx_binary, "validate", str(path)])


def normalize_warnings(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def render_vsdx(
    vsdx_binary: str,
    path: Path,
    inspection: dict[str, Any],
    output_dir: Path | None,
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if output_dir is None:
        temporary = tempfile.TemporaryDirectory(prefix="vsdx-map-audit-")
        target_dir = Path(temporary.name)
    else:
        target_dir = output_dir
        target_dir.mkdir(parents=True, exist_ok=True)

    try:
        for index, page in enumerate(inspection.get("pages", []), start=1):
            page_id = str(page.get("id") or index)
            safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", page_id)
            output = target_dir / f"page-{safe_id}.svg"
            if output.exists():
                raise ToolError(f"render output already exists: {output}")
            result = run_json(
                [
                    vsdx_binary,
                    "render",
                    "--page",
                    page_id,
                    "--output",
                    str(output),
                    str(path),
                ]
            )
            reports.append(
                {
                    "pageId": page_id,
                    "pageName": page.get("name"),
                    "output": str(output) if output_dir is not None else None,
                    "warnings": normalize_warnings(result.get("warnings")),
                }
            )
    finally:
        if temporary is not None:
            temporary.cleanup()
    return reports


def zip_metrics(path: Path, inspection: dict[str, Any]) -> dict[str, Any]:
    row_types: Counter[str] = Counter()
    connect_rows_by_page: dict[str, int] = {}
    connect_rows_by_connector: dict[str, int] = defaultdict(int)
    connector_topology = []
    relationship_types: Counter[str] = Counter()

    try:
        with zipfile.ZipFile(path) as archive:
            corrupt_member = archive.testzip()
            package_parts = sorted(archive.namelist())
            master_parts = [
                name
                for name in package_parts
                if re.fullmatch(r"visio/masters/master\d+\.xml", name)
            ]
            for relationship_part in (
                name for name in package_parts if name.endswith(".rels")
            ):
                root = ElementTree.fromstring(archive.read(relationship_part))
                for relationship in root.iter():
                    if local_name(relationship.tag) != "Relationship":
                        continue
                    relationship_type = relationship.attrib.get("Type", "")
                    relationship_types[relationship_type] += 1

            for page in inspection.get("pages", []):
                part = str(page.get("part") or "").lstrip("/")
                if not part:
                    continue
                try:
                    root = ElementTree.fromstring(archive.read(part))
                except KeyError as exc:
                    raise ToolError(f"page part is missing from VSDX: {part}") from exc

                page_connect_count = 0
                page_connectors: dict[str, list[dict[str, str]]] = defaultdict(
                    list
                )
                for element in root.iter():
                    if local_name(element.tag) == "Connect":
                        page_connect_count += 1
                        from_sheet = element.attrib.get("FromSheet", "")
                        connect_rows_by_connector[
                            f"{page.get('id')}:{from_sheet}"
                        ] += 1
                        page_connectors[from_sheet].append(dict(element.attrib))

                connect_rows_by_page[str(page.get("id"))] = page_connect_count
                shapes_by_id = {
                    str(shape.get("id")): shape
                    for shape in page.get("shapes", [])
                }
                for connector_id, rows in page_connectors.items():
                    source = None
                    target = None
                    for row in rows:
                        to_sheet = row.get("ToSheet", "")
                        target_shape = shapes_by_id.get(to_sheet, {})
                        endpoint = semantic_id(target_shape) or f"shape:{to_sheet}"
                        from_cell = row.get("FromCell", "")
                        if from_cell.startswith("Begin"):
                            source = endpoint
                        elif from_cell.startswith("End"):
                            target = endpoint
                    connector_shape = shapes_by_id.get(connector_id, {})
                    connector_topology.append(
                        {
                            "pageId": str(page.get("id")),
                            "source": source,
                            "target": target,
                            "label": str(connector_shape.get("text") or ""),
                        }
                    )

                for section in root.iter():
                    if (
                        local_name(section.tag) != "Section"
                        or section.attrib.get("N") != "Geometry"
                    ):
                        continue
                    for row in section:
                        if local_name(row.tag) == "Row":
                            row_types[row.attrib.get("T", "(unset)")] += 1
    except zipfile.BadZipFile as exc:
        raise ToolError(f"invalid ZIP/VSDX package: {path}") from exc

    connector_topology.sort(
        key=lambda item: (
            item["pageId"],
            str(item["source"]),
            str(item["target"]),
            item["label"],
        )
    )
    topology_json = json.dumps(
        connector_topology,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "zipCrcClean": corrupt_member is None,
        "corruptMember": corrupt_member,
        "packageParts": package_parts,
        "masterPartCount": len(master_parts),
        "relationshipTypeCounts": dict(sorted(relationship_types.items())),
        "connectRowsByPage": dict(connect_rows_by_page),
        "connectRowsByConnector": dict(connect_rows_by_connector),
        "connectorTopology": connector_topology,
        "connectorTopologySha256": hashlib.sha256(topology_json).hexdigest(),
        "geometryRowTypes": dict(sorted(row_types.items())),
    }


def content_metrics(page: dict[str, Any]) -> dict[str, Any]:
    boxes = []
    rotated_canvases = []
    for shape in page.get("shapes", []):
        if shape.get("oneD"):
            continue
        sid = semantic_id(shape)
        if sid == "page:canvas":
            angle = numeric_cell(shape, "Angle") or 0.0
            if abs(angle) > 1e-6:
                rotated_canvases.append(
                    {"shape": shape_label(shape), "angleRadians": angle}
                )
            continue
        box = shape_box(shape)
        if box:
            boxes.append(box)

    width = float(page.get("width") or 0)
    height = float(page.get("height") or 0)
    if not boxes or width <= 0 or height <= 0:
        return {
            "bounds": None,
            "widthUse": None,
            "heightUse": None,
            "rotatedCanvases": rotated_canvases,
        }

    bounds = {
        "left": min(box["left"] for box in boxes),
        "right": max(box["right"] for box in boxes),
        "bottom": min(box["bottom"] for box in boxes),
        "top": max(box["top"] for box in boxes),
    }
    return {
        "bounds": bounds,
        "widthUse": (bounds["right"] - bounds["left"]) / width,
        "heightUse": (bounds["top"] - bounds["bottom"]) / height,
        "rotatedCanvases": rotated_canvases,
    }


def lane_context(page: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    bands: dict[str, Any] = {}
    labels: dict[str, Any] = {}
    for shape in page.get("shapes", []):
        sid = semantic_id(shape)
        band_match = re.fullmatch(r"lane:([^:]+):band", sid)
        label_match = re.fullmatch(r"lane:([^:]+):label", sid)
        if band_match:
            bands[band_match.group(1)] = shape
        elif label_match:
            labels[label_match.group(1)] = shape
    return bands, labels


def assign_lane(shape: dict[str, Any], bands: dict[str, Any]) -> str | None:
    center = numeric_cell(shape, "PinY")
    if center is None:
        return None
    matches = []
    for lane, band in bands.items():
        box = shape_box(band)
        if box and box["bottom"] <= center <= box["top"]:
            matches.append(lane)
    return matches[0] if len(matches) == 1 else None


def minimum_record(
    current: dict[str, Any] | None,
    value: float,
    **context: Any,
) -> dict[str, Any]:
    if current is None or value < current["value"]:
        return {"value": value, **context}
    return current


def page_layout_audit(
    page: dict[str, Any],
    thresholds: dict[str, float],
    allowed_colors: set[str],
    color_lane_pattern: re.Pattern[str],
) -> dict[str, Any]:
    bands, labels = lane_context(page)
    nodes = []
    unassigned = []

    for shape in page.get("shapes", []):
        sid = semantic_id(shape)
        if not sid.startswith("node:"):
            continue
        box = shape_box(shape)
        if box is None:
            continue
        lane = assign_lane(shape, bands) if bands else ""
        if bands and lane is None:
            unassigned.append(sid)
        nodes.append(
            {
                "id": sid,
                "shape": shape,
                "box": box,
                "lane": lane,
                "fill": str(cell_value(shape, "FillForegnd") or "").lower(),
            }
        )

    minimum_horizontal_lane_padding = None
    minimum_vertical_lane_padding = None
    if bands:
        for node in nodes:
            lane_name = node["lane"]
            if lane_name is None:
                continue
            lane_box = shape_box(bands[lane_name])
            if lane_box is None:
                continue
            label_box = shape_box(labels[lane_name]) if lane_name in labels else None
            content_left = label_box["right"] if label_box else lane_box["left"]
            horizontal = min(
                node["box"]["left"] - content_left,
                lane_box["right"] - node["box"]["right"],
            )
            vertical = min(
                node["box"]["bottom"] - lane_box["bottom"],
                lane_box["top"] - node["box"]["top"],
            )
            minimum_horizontal_lane_padding = minimum_record(
                minimum_horizontal_lane_padding,
                horizontal,
                node=node["id"],
                lane=lane_name,
            )
            minimum_vertical_lane_padding = minimum_record(
                minimum_vertical_lane_padding,
                vertical,
                node=node["id"],
                lane=lane_name,
            )

    overlaps: list[list[str]] = []
    minimum_horizontal_peer_gap = None
    minimum_vertical_peer_gap = None
    for index, first in enumerate(nodes):
        for second in nodes[index + 1 :]:
            if first["lane"] != second["lane"]:
                continue
            overlap_x = min(first["box"]["right"], second["box"]["right"]) - max(
                first["box"]["left"], second["box"]["left"]
            )
            overlap_y = min(first["box"]["top"], second["box"]["top"]) - max(
                first["box"]["bottom"], second["box"]["bottom"]
            )
            if overlap_x > 1e-9 and overlap_y > 1e-9:
                overlaps.append([first["id"], second["id"]])
                continue
            if overlap_y > 1e-9:
                gap = max(first["box"]["left"], second["box"]["left"]) - min(
                    first["box"]["right"], second["box"]["right"]
                )
                minimum_horizontal_peer_gap = minimum_record(
                    minimum_horizontal_peer_gap,
                    gap,
                    pair=[first["id"], second["id"]],
                    lane=first["lane"],
                )
            if overlap_x > 1e-9:
                gap = max(first["box"]["bottom"], second["box"]["bottom"]) - min(
                    first["box"]["top"], second["box"]["top"]
                )
                minimum_vertical_peer_gap = minimum_record(
                    minimum_vertical_peer_gap,
                    gap,
                    pair=[first["id"], second["id"]],
                    lane=first["lane"],
                )

    rows: list[dict[str, Any]] = []
    nodes_by_lane: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        nodes_by_lane[str(node["lane"])].append(node)
    for lane, lane_nodes in nodes_by_lane.items():
        pending = sorted(lane_nodes, key=lambda node: node["box"]["centerY"])
        clusters: list[list[dict[str, Any]]] = []
        for node in pending:
            if (
                not clusters
                or abs(
                    node["box"]["centerY"]
                    - statistics.mean(
                        item["box"]["centerY"] for item in clusters[-1]
                    )
                )
                > thresholds["rowCenterTolerance"]
            ):
                clusters.append([node])
            else:
                clusters[-1].append(node)
        for cluster in clusters:
            if len(cluster) < 3:
                continue
            ordered = sorted(cluster, key=lambda node: node["box"]["centerX"])
            adjacent_groups: list[list[dict[str, Any]]] = [[ordered[0]]]
            for node in ordered[1:]:
                gap = node["box"]["left"] - adjacent_groups[-1][-1]["box"]["right"]
                if gap > thresholds["rowAdjacencyMaximum"]:
                    adjacent_groups.append([node])
                else:
                    adjacent_groups[-1].append(node)
            for group in adjacent_groups:
                if len(group) < 3:
                    continue
                gaps = [
                    group[index + 1]["box"]["left"]
                    - group[index]["box"]["right"]
                    for index in range(len(group) - 1)
                ]
                if any(gap < 0 for gap in gaps):
                    continue
                rows.append(
                    {
                        "lane": lane,
                        "nodes": [node["id"] for node in group],
                        "gaps": gaps,
                        "gapSpread": max(gaps) - min(gaps),
                        "balanced": (
                            max(gaps) - min(gaps)
                            <= thresholds["maximumPeerGapSpread"]
                        ),
                    }
                )

    colored_nodes = [
        {"id": node["id"], "lane": node["lane"], "fill": node["fill"]}
        for node in nodes
        if node["fill"] not in WHITE_FILLS
    ]
    invalid_colored_nodes = [
        node
        for node in colored_nodes
        if not color_lane_pattern.search(str(node["lane"]))
        or node["fill"] not in allowed_colors
    ]

    return {
        "pageId": str(page.get("id")),
        "pageName": page.get("name"),
        "nodeCount": len(nodes),
        "laneCount": len(bands),
        "unassignedNodes": unassigned,
        "overlaps": overlaps,
        "measurements": {
            "minimumHorizontalLanePadding": minimum_horizontal_lane_padding,
            "minimumVerticalLanePadding": minimum_vertical_lane_padding,
            "minimumHorizontalPeerGap": minimum_horizontal_peer_gap,
            "minimumVerticalPeerGap": minimum_vertical_peer_gap,
            "rows": rows,
        },
        "coloredNodes": colored_nodes,
        "invalidColoredNodes": invalid_colored_nodes,
    }


def semantic_metrics(inspection: dict[str, Any]) -> dict[str, Any]:
    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing = []
    for page in inspection.get("pages", []):
        for shape in page.get("shapes", []):
            sid = semantic_id(shape)
            record = {
                "pageId": str(page.get("id")),
                "shapeId": str(shape.get("id")),
                "name": shape.get("name"),
                "oneD": bool(shape.get("oneD")),
            }
            if sid:
                by_id[sid].append(record)
            else:
                missing.append(record)
    return {
        "missing": missing,
        "duplicates": {
            sid: records for sid, records in by_id.items() if len(records) > 1
        },
        "count": len(by_id),
    }


def connector_metrics(
    inspection: dict[str, Any],
    package: dict[str, Any],
) -> dict[str, Any]:
    connectors = []
    connect_row_failures = []
    formula_failures = []

    for page in inspection.get("pages", []):
        page_id = str(page.get("id"))
        for shape in page.get("shapes", []):
            if not shape.get("oneD"):
                continue
            shape_id = str(shape.get("id"))
            sid = semantic_id(shape)
            connect_count = package["connectRowsByConnector"].get(
                f"{page_id}:{shape_id}", 0
            )
            formulas = {name: cell_formula(shape, name) for name in ENDPOINT_CELLS}
            begin_coherent = (
                formulas["BeginX"]
                and formulas["BeginX"] == formulas["BeginY"]
                and "PNT(" in formulas["BeginX"].upper()
            )
            end_coherent = (
                formulas["EndX"]
                and formulas["EndX"] == formulas["EndY"]
                and "PNT(" in formulas["EndX"].upper()
            )
            record = {
                "pageId": page_id,
                "shapeId": shape_id,
                "semanticId": sid,
                "connectRows": connect_count,
                "beginFormulaCoherent": bool(begin_coherent),
                "endFormulaCoherent": bool(end_coherent),
            }
            connectors.append(record)
            if connect_count != 2:
                connect_row_failures.append(record)
            if not begin_coherent or not end_coherent:
                formula_failures.append(record)

    return {
        "count": len(connectors),
        "connectors": connectors,
        "connectRowFailures": connect_row_failures,
        "formulaFailures": formula_failures,
    }


def threshold_pass(
    measurement: dict[str, Any] | None,
    threshold: float,
) -> bool | None:
    if measurement is None:
        return None
    return float(measurement["value"]) >= threshold


def audit_document(
    path: Path,
    vsdx_binary: str,
    *,
    render: bool,
    render_dir: Path | None,
    thresholds: dict[str, float],
    allowed_colors: set[str],
    color_lane_regex: str,
    allow_missing_semantic_ids: bool,
    allow_render_warnings: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    inspection = inspect_vsdx(vsdx_binary, path)
    validation = validate_vsdx(vsdx_binary, path)
    package = zip_metrics(path, inspection)
    render_reports = (
        render_vsdx(vsdx_binary, path, inspection, render_dir) if render else []
    )
    render_warnings = [
        {"pageId": report["pageId"], "warning": warning}
        for report in render_reports
        for warning in report["warnings"]
    ]
    semantic = semantic_metrics(inspection)
    connectors = connector_metrics(inspection, package)
    color_lane_pattern = re.compile(color_lane_regex, re.IGNORECASE)

    page_reports = []
    for page in inspection.get("pages", []):
        page_reports.append(
            {
                "pageId": str(page.get("id")),
                "pageName": page.get("name"),
                "width": page.get("width"),
                "height": page.get("height"),
                "content": content_metrics(page),
                "layout": page_layout_audit(
                    page,
                    thresholds,
                    allowed_colors,
                    color_lane_pattern,
                ),
            }
        )

    horizontal_lane_measurements = [
        page["layout"]["measurements"]["minimumHorizontalLanePadding"]
        for page in page_reports
        if page["layout"]["measurements"]["minimumHorizontalLanePadding"]
        is not None
    ]
    vertical_lane_measurements = [
        page["layout"]["measurements"]["minimumVerticalLanePadding"]
        for page in page_reports
        if page["layout"]["measurements"]["minimumVerticalLanePadding"] is not None
    ]
    horizontal_peer_measurements = [
        page["layout"]["measurements"]["minimumHorizontalPeerGap"]
        for page in page_reports
        if page["layout"]["measurements"]["minimumHorizontalPeerGap"] is not None
    ]
    vertical_peer_measurements = [
        page["layout"]["measurements"]["minimumVerticalPeerGap"]
        for page in page_reports
        if page["layout"]["measurements"]["minimumVerticalPeerGap"] is not None
    ]

    def smallest(items: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
        values = list(items)
        return min(values, key=lambda item: item["value"]) if values else None

    minimums = {
        "horizontalLanePadding": smallest(horizontal_lane_measurements),
        "verticalLanePadding": smallest(vertical_lane_measurements),
        "horizontalPeerGap": smallest(horizontal_peer_measurements),
        "verticalPeerGap": smallest(vertical_peer_measurements),
    }
    checks: dict[str, bool | None] = {
        "vsdxValidation": bool(validation.get("valid")),
        "zipCrc": bool(package["zipCrcClean"]),
        "renderWarnings": (
            True
            if not render
            else allow_render_warnings or not render_warnings
        ),
        "pageFit": all(
            page["content"]["widthUse"] is not None
            and page["content"]["heightUse"] is not None
            and page["content"]["widthUse"] >= thresholds["minimumPageUse"]
            and page["content"]["heightUse"] >= thresholds["minimumPageUse"]
            for page in page_reports
        ),
        "canvasRotation": all(
            not page["content"]["rotatedCanvases"] for page in page_reports
        ),
        "nodeOverlaps": all(
            not page["layout"]["overlaps"] for page in page_reports
        ),
        "laneAssignment": all(
            not page["layout"]["unassignedNodes"] for page in page_reports
        ),
        "horizontalLanePadding": threshold_pass(
            minimums["horizontalLanePadding"],
            thresholds["horizontalLanePadding"],
        ),
        "verticalLanePadding": threshold_pass(
            minimums["verticalLanePadding"],
            thresholds["verticalLanePadding"],
        ),
        "horizontalPeerGap": threshold_pass(
            minimums["horizontalPeerGap"],
            thresholds["horizontalPeerGap"],
        ),
        "verticalPeerGap": threshold_pass(
            minimums["verticalPeerGap"],
            thresholds["verticalPeerGap"],
        ),
        "colorScope": all(
            not page["layout"]["invalidColoredNodes"] for page in page_reports
        ),
        "semanticIds": (
            not semantic["duplicates"]
            and (allow_missing_semantic_ids or not semantic["missing"])
        ),
        "connectorConnectRows": not connectors["connectRowFailures"],
        "connectorEndpointFormulas": not connectors["formulaFailures"],
    }
    passed = all(value is not False for value in checks.values())

    report = {
        "kind": "audit",
        "path": str(path),
        "sha256": inspection.get("sha256"),
        "pass": passed,
        "checks": checks,
        "thresholds": thresholds,
        "minimums": minimums,
        "pages": page_reports,
        "semanticIds": semantic,
        "connectors": connectors,
        "package": package,
        "render": render_reports,
        "renderWarnings": render_warnings,
        "validation": validation,
    }
    return report, inspection


def index_semantic_shapes(
    inspection: dict[str, Any],
) -> tuple[dict[str, tuple[dict[str, Any], dict[str, Any]]], dict[str, int]]:
    index: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    counts: Counter[str] = Counter()
    for page in inspection.get("pages", []):
        for shape in page.get("shapes", []):
            sid = semantic_id(shape)
            if not sid:
                continue
            counts[sid] += 1
            index.setdefault(sid, (page, shape))
    return index, dict(counts)


def page_lane_assignments(
    inspection: dict[str, Any],
) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for page in inspection.get("pages", []):
        bands, _ = lane_context(page)
        for shape in page.get("shapes", []):
            sid = semantic_id(shape)
            if sid.startswith("node:"):
                result[sid] = assign_lane(shape, bands) if bands else ""
    return result


def page_compare_summary(inspection: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "pageId": str(page.get("id")),
            "pageName": page.get("name"),
            "width": page.get("width"),
            "height": page.get("height"),
            "content": content_metrics(page),
        }
        for page in inspection.get("pages", [])
    ]


def diff_inspections(
    baseline: dict[str, Any],
    edited: dict[str, Any],
    *,
    tolerance: float,
) -> dict[str, Any]:
    baseline_index, baseline_counts = index_semantic_shapes(baseline)
    edited_index, edited_counts = index_semantic_shapes(edited)
    baseline_ids = set(baseline_index)
    edited_ids = set(edited_index)
    common_ids = sorted(baseline_ids & edited_ids)

    translation_samples_x = []
    translation_samples_y = []
    for sid in common_ids:
        baseline_shape = baseline_index[sid][1]
        edited_shape = edited_index[sid][1]
        if baseline_shape.get("oneD") or sid == "page:canvas":
            continue
        baseline_x = numeric_cell(baseline_shape, "PinX")
        baseline_y = numeric_cell(baseline_shape, "PinY")
        edited_x = numeric_cell(edited_shape, "PinX")
        edited_y = numeric_cell(edited_shape, "PinY")
        if None not in (baseline_x, edited_x):
            translation_samples_x.append(edited_x - baseline_x)
        if None not in (baseline_y, edited_y):
            translation_samples_y.append(edited_y - baseline_y)
    translation_x = (
        statistics.median(translation_samples_x) if translation_samples_x else 0.0
    )
    translation_y = (
        statistics.median(translation_samples_y) if translation_samples_y else 0.0
    )

    text_changes = []
    geometry_changes = []
    connector_geometry_changes = []
    style_changes = []
    for sid in common_ids:
        baseline_shape = baseline_index[sid][1]
        edited_shape = edited_index[sid][1]
        baseline_text = str(baseline_shape.get("text") or "")
        edited_text = str(edited_shape.get("text") or "")
        if baseline_text != edited_text:
            text_changes.append(
                {
                    "semanticId": sid,
                    "baseline": baseline_text,
                    "edited": edited_text,
                }
            )

        deltas: dict[str, float] = {}
        for name in POINT_CELLS:
            baseline_value = numeric_cell(baseline_shape, name)
            edited_value = numeric_cell(edited_shape, name)
            if None in (baseline_value, edited_value):
                continue
            delta = edited_value - baseline_value
            if name == "PinX":
                delta -= translation_x
            elif name == "PinY":
                delta -= translation_y
            if abs(delta) > tolerance:
                deltas[name] = delta
        if deltas:
            record = {
                "semanticId": sid,
                "residualDeltas": deltas,
                "baseline": {
                    name: numeric_cell(baseline_shape, name)
                    for name in POINT_CELLS
                },
                "edited": {
                    name: numeric_cell(edited_shape, name)
                    for name in POINT_CELLS
                },
            }
            if baseline_shape.get("oneD") or edited_shape.get("oneD"):
                connector_geometry_changes.append(record)
            else:
                geometry_changes.append(record)

        changed_styles = {}
        for name in STYLE_CELLS:
            baseline_value = cell_value(baseline_shape, name)
            edited_value = cell_value(edited_shape, name)
            if baseline_value != edited_value:
                changed_styles[name] = {
                    "baseline": baseline_value,
                    "edited": edited_value,
                }
        if changed_styles:
            style_changes.append(
                {"semanticId": sid, "changes": changed_styles}
            )

    baseline_lanes = page_lane_assignments(baseline)
    edited_lanes = page_lane_assignments(edited)
    lane_changes = [
        {
            "semanticId": sid,
            "baseline": baseline_lanes.get(sid),
            "edited": edited_lanes.get(sid),
        }
        for sid in sorted(set(baseline_lanes) & set(edited_lanes))
        if baseline_lanes.get(sid) != edited_lanes.get(sid)
    ]

    baseline_pages = page_compare_summary(baseline)
    edited_pages = page_compare_summary(edited)
    page_changes = []
    for index in range(max(len(baseline_pages), len(edited_pages))):
        before = baseline_pages[index] if index < len(baseline_pages) else None
        after = edited_pages[index] if index < len(edited_pages) else None
        if before != after:
            page_changes.append({"baseline": before, "edited": after})

    return {
        "globalTranslation": {"x": translation_x, "y": translation_y},
        "semanticIds": {
            "lost": sorted(baseline_ids - edited_ids),
            "gained": sorted(edited_ids - baseline_ids),
            "baselineDuplicates": sorted(
                sid for sid, count in baseline_counts.items() if count > 1
            ),
            "editedDuplicates": sorted(
                sid for sid, count in edited_counts.items() if count > 1
            ),
        },
        "pageChanges": page_changes,
        "textChanges": text_changes,
        "geometryChanges": geometry_changes,
        "connectorGeometryChanges": connector_geometry_changes,
        "laneOwnershipChanges": lane_changes,
        "styleChanges": style_changes,
    }


def compare_documents(
    baseline_path: Path,
    edited_path: Path,
    vsdx_binary: str,
    *,
    render: bool,
    tolerance: float,
) -> dict[str, Any]:
    thresholds = default_thresholds()
    audit_kwargs = {
        "render": render,
        "render_dir": None,
        "thresholds": thresholds,
        "allowed_colors": set(DEFAULT_ALLOWED_COLORS),
        "color_lane_regex": r"^status$",
        "allow_missing_semantic_ids": False,
        "allow_render_warnings": False,
    }
    baseline_audit, baseline_inspection = audit_document(
        baseline_path, vsdx_binary, **audit_kwargs
    )
    edited_audit, edited_inspection = audit_document(
        edited_path, vsdx_binary, **audit_kwargs
    )
    delta = diff_inspections(
        baseline_inspection,
        edited_inspection,
        tolerance=tolerance,
    )
    baseline_geometry = Counter(baseline_audit["package"]["geometryRowTypes"])
    edited_geometry = Counter(edited_audit["package"]["geometryRowTypes"])
    geometry_types = {
        key: {
            "baseline": baseline_geometry.get(key, 0),
            "edited": edited_geometry.get(key, 0),
            "delta": edited_geometry.get(key, 0) - baseline_geometry.get(key, 0),
        }
        for key in sorted(set(baseline_geometry) | set(edited_geometry))
        if baseline_geometry.get(key, 0) != edited_geometry.get(key, 0)
    }
    baseline_parts = set(baseline_audit["package"]["packageParts"])
    edited_parts = set(edited_audit["package"]["packageParts"])
    baseline_relationships = Counter(
        baseline_audit["package"]["relationshipTypeCounts"]
    )
    edited_relationships = Counter(
        edited_audit["package"]["relationshipTypeCounts"]
    )
    relationship_changes = {
        key: {
            "baseline": baseline_relationships.get(key, 0),
            "edited": edited_relationships.get(key, 0),
            "delta": (
                edited_relationships.get(key, 0)
                - baseline_relationships.get(key, 0)
            ),
        }
        for key in sorted(set(baseline_relationships) | set(edited_relationships))
        if baseline_relationships.get(key, 0)
        != edited_relationships.get(key, 0)
    }
    return {
        "kind": "compare",
        "baseline": str(baseline_path),
        "edited": str(edited_path),
        "delta": delta,
        "packageChanges": {
            "partsAdded": sorted(edited_parts - baseline_parts),
            "partsRemoved": sorted(baseline_parts - edited_parts),
            "masterPartCount": {
                "baseline": baseline_audit["package"]["masterPartCount"],
                "edited": edited_audit["package"]["masterPartCount"],
            },
            "relationshipTypeChanges": relationship_changes,
            "geometryRows": geometry_types,
            "connectorTopology": {
                "same": (
                    baseline_audit["package"]["connectorTopologySha256"]
                    == edited_audit["package"]["connectorTopologySha256"]
                ),
                "baselineSha256": baseline_audit["package"][
                    "connectorTopologySha256"
                ],
                "editedSha256": edited_audit["package"][
                    "connectorTopologySha256"
                ],
            },
        },
        "baselineAudit": {
            "pass": baseline_audit["pass"],
            "checks": baseline_audit["checks"],
            "pages": baseline_audit["pages"],
            "semanticIds": baseline_audit["semanticIds"],
            "connectors": {
                "count": baseline_audit["connectors"]["count"],
                "connectRowFailures": baseline_audit["connectors"][
                    "connectRowFailures"
                ],
                "formulaFailures": baseline_audit["connectors"][
                    "formulaFailures"
                ],
            },
            "renderWarnings": baseline_audit["renderWarnings"],
        },
        "editedAudit": {
            "pass": edited_audit["pass"],
            "checks": edited_audit["checks"],
            "pages": edited_audit["pages"],
            "semanticIds": edited_audit["semanticIds"],
            "connectors": {
                "count": edited_audit["connectors"]["count"],
                "connectRowFailures": edited_audit["connectors"][
                    "connectRowFailures"
                ],
                "formulaFailures": edited_audit["connectors"][
                    "formulaFailures"
                ],
            },
            "renderWarnings": edited_audit["renderWarnings"],
        },
    }


def default_thresholds() -> dict[str, float]:
    return {
        "horizontalLanePadding": 0.60,
        "verticalLanePadding": 0.40,
        "horizontalPeerGap": 0.60,
        "verticalPeerGap": 0.80,
        "minimumPageUse": 0.75,
        "rowCenterTolerance": 0.15,
        "rowAdjacencyMaximum": 3.00,
        "maximumPeerGapSpread": 0.50,
    }


def check_mark(value: bool | None) -> str:
    if value is None:
        return "N/A"
    return "PASS" if value else "FAIL"


def markdown_audit(report: dict[str, Any]) -> str:
    lines = [
        "# VSDX process-map audit",
        "",
        f"Result: **{'PASS' if report['pass'] else 'FAIL'}**",
        "",
        "## Checks",
        "",
    ]
    for name, value in report["checks"].items():
        lines.append(f"- {check_mark(value)} `{name}`")
    lines.extend(["", "## Pages", ""])
    lines.append("| Page | Size | Content use | Nodes | Lanes |")
    lines.append("|---|---:|---:|---:|---:|")
    for page in report["pages"]:
        content = page["content"]
        width_use = content["widthUse"]
        height_use = content["heightUse"]
        use = (
            "n/a"
            if width_use is None or height_use is None
            else f"{width_use:.1%} × {height_use:.1%}"
        )
        lines.append(
            f"| {page['pageName'] or page['pageId']} | "
            f"{page['width']} × {page['height']} | {use} | "
            f"{page['layout']['nodeCount']} | {page['layout']['laneCount']} |"
        )

    findings = []
    if report["semanticIds"]["missing"]:
        findings.append(
            f"{len(report['semanticIds']['missing'])} shapes lack semantic IDs."
        )
    if report["semanticIds"]["duplicates"]:
        findings.append("Duplicate semantic IDs are present.")
    if report["renderWarnings"]:
        findings.extend(
            f"Render warning on page {item['pageId']}: {item['warning']}"
            for item in report["renderWarnings"]
        )
    for page in report["pages"]:
        if page["content"]["rotatedCanvases"]:
            findings.append(
                f"Page {page['pageId']} contains a rotated page canvas."
            )
        if page["layout"]["overlaps"]:
            findings.append(
                f"Page {page['pageId']} has {len(page['layout']['overlaps'])} node overlaps."
            )
        if page["layout"]["invalidColoredNodes"]:
            findings.append(
                f"Page {page['pageId']} has color outside the approved lane or palette."
            )
        unbalanced = [
            row
            for row in page["layout"]["measurements"]["rows"]
            if not row["balanced"]
        ]
        for row in unbalanced:
            findings.append(
                f"Page {page['pageId']} row in lane {row['lane']} has "
                f"{row['gapSpread']:.3f} in gap spread."
            )
    if report["connectors"]["connectRowFailures"]:
        count = len(report["connectors"]["connectRowFailures"])
        findings.append(
            f"{count} connectors do not have two Connect rows."
        )
    if report["connectors"]["formulaFailures"]:
        count = len(report["connectors"]["formulaFailures"])
        findings.append(
            f"{count} connectors have incoherent endpoint formulas."
        )

    lines.extend(["", "## Findings", ""])
    lines.extend(f"- {finding}" for finding in findings)
    if not findings:
        lines.append("- No audit findings.")
    return "\n".join(lines) + "\n"


def markdown_compare(report: dict[str, Any]) -> str:
    delta = report["delta"]

    def use_text(content: dict[str, Any]) -> str:
        width_use = content.get("widthUse")
        height_use = content.get("heightUse")
        if width_use is None or height_use is None:
            return "n/a"
        return f"{width_use:.1%} × {height_use:.1%}"

    lines = [
        "# VSDX baseline-to-edit comparison",
        "",
        f"- Baseline audit: **{'PASS' if report['baselineAudit']['pass'] else 'FAIL'}**",
        f"- Edited audit: **{'PASS' if report['editedAudit']['pass'] else 'FAIL'}**",
        f"- Global translation: x `{delta['globalTranslation']['x']:.3f}`, "
        f"y `{delta['globalTranslation']['y']:.3f}` inches",
    ]
    failed_checks = [
        name
        for name, value in report["editedAudit"]["checks"].items()
        if value is False
    ]
    lines.append(
        f"- Edited failed checks: {', '.join(failed_checks) or 'none'}"
    )

    lines.extend(["", "## Page changes", ""])
    if delta["pageChanges"]:
        for item in delta["pageChanges"]:
            before = item["baseline"]
            after = item["edited"]
            if before is None or after is None:
                lines.append(
                    f"- Page set changed: {before or 'missing'} → {after or 'missing'}"
                )
                continue
            before_content = before["content"]
            after_content = after["content"]
            lines.append(
                f"- `{before['pageName'] or before['pageId']}`: "
                f"{before['width']} × {before['height']} "
                f"({use_text(before_content)} content use) → "
                f"{after['width']} × {after['height']} "
                f"({use_text(after_content)} content use)"
            )
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Semantic identity",
            "",
            f"- Lost IDs: {', '.join(delta['semanticIds']['lost']) or 'none'}",
            f"- Gained IDs: {', '.join(delta['semanticIds']['gained']) or 'none'}",
            "",
            "## Text changes",
            "",
        ]
    )
    if delta["textChanges"]:
        for item in delta["textChanges"]:
            lines.append(
                f"- `{item['semanticId']}`: "
                f"{json.dumps(item['baseline'])} → {json.dumps(item['edited'])}"
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Geometry changes after translation", ""])
    if delta["geometryChanges"]:
        for item in delta["geometryChanges"]:
            values = ", ".join(
                f"{name} {value:+.3f}"
                for name, value in item["residualDeltas"].items()
            )
            lines.append(f"- `{item['semanticId']}`: {values}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Connector route changes", ""])
    connector_changes = delta["connectorGeometryChanges"]
    if connector_changes:
        lines.append(
            f"- {len(connector_changes)} preserved connector shapes changed geometry."
        )
        material_changes = [
            item
            for item in connector_changes
            if any(
                abs(value) > 0.25
                for value in item["residualDeltas"].values()
            )
        ]
        for item in material_changes:
            values = ", ".join(
                f"{name} {value:+.3f}"
                for name, value in item["residualDeltas"].items()
            )
            lines.append(f"- Material: `{item['semanticId']}`: {values}")
        if len(material_changes) < len(connector_changes):
            lines.append(
                "- Smaller route-normalization deltas remain in the JSON report."
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Lane ownership changes", ""])
    if delta["laneOwnershipChanges"]:
        for item in delta["laneOwnershipChanges"]:
            lines.append(
                f"- `{item['semanticId']}`: `{item['baseline']}` → `{item['edited']}`"
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Package and render changes", ""])
    package_changes = report["packageChanges"]
    topology = package_changes["connectorTopology"]
    lines.append(
        f"- Connector source/target/label topology: "
        f"{'unchanged' if topology['same'] else 'changed'}"
    )
    master_parts = package_changes["masterPartCount"]
    if master_parts["baseline"] != master_parts["edited"]:
        lines.append(
            f"- Master parts: {master_parts['baseline']} → "
            f"{master_parts['edited']}"
        )
    if package_changes["partsAdded"] or package_changes["partsRemoved"]:
        lines.append(
            f"- Package parts: +{len(package_changes['partsAdded'])} / "
            f"-{len(package_changes['partsRemoved'])}"
        )
    if package_changes["relationshipTypeChanges"]:
        lines.append(
            f"- Relationship types changed: "
            f"{len(package_changes['relationshipTypeChanges'])}"
        )
    if package_changes["geometryRows"]:
        for name, values in package_changes["geometryRows"].items():
            lines.append(
                f"- `{name}` rows: {values['baseline']} → {values['edited']}"
            )
    else:
        lines.append("- Geometry row counts are unchanged.")
    for item in report["editedAudit"]["renderWarnings"]:
        lines.append(
            f"- Edited render warning on page {item['pageId']}: {item['warning']}"
        )
    return "\n".join(lines) + "\n"


def emit_report(report: dict[str, Any], format_name: str) -> str:
    if format_name == "json":
        return json.dumps(report, indent=2, sort_keys=True) + "\n"
    if report["kind"] == "audit":
        return markdown_audit(report)
    return markdown_compare(report)


def write_report(text: str, output: Path | None) -> None:
    if output is None:
        sys.stdout.write(text)
        return
    if output.exists():
        raise ToolError(f"report output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--vsdx", help="absolute path to the vsdx binary")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="report format",
    )
    parser.add_argument("--output", type=Path, help="new report output path")
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="skip render-warning inspection",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare and audit VSDX Guard process maps."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="audit one process map")
    audit.add_argument("file", type=Path)
    add_common_options(audit)
    audit.add_argument(
        "--render-dir",
        type=Path,
        help="new or existing directory for page SVG renders",
    )
    audit.add_argument(
        "--horizontal-lane-padding", type=float, default=0.60
    )
    audit.add_argument("--vertical-lane-padding", type=float, default=0.40)
    audit.add_argument("--horizontal-peer-gap", type=float, default=0.60)
    audit.add_argument("--vertical-peer-gap", type=float, default=0.80)
    audit.add_argument("--minimum-page-use", type=float, default=0.75)
    audit.add_argument("--row-center-tolerance", type=float, default=0.15)
    audit.add_argument("--row-adjacency-maximum", type=float, default=3.00)
    audit.add_argument("--maximum-peer-gap-spread", type=float, default=0.50)
    audit.add_argument(
        "--color-lane-regex",
        default=r"^status$",
        help="case-insensitive lane regex allowed to contain colored nodes",
    )
    audit.add_argument(
        "--allowed-color",
        action="append",
        dest="allowed_colors",
        help="allowed non-white fill; repeat for multiple colors",
    )
    audit.add_argument("--allow-missing-semantic-ids", action="store_true")
    audit.add_argument("--allow-render-warnings", action="store_true")

    compare = subparsers.add_parser(
        "compare", help="compare a generated baseline with a user-edited VSDX"
    )
    compare.add_argument("baseline", type=Path)
    compare.add_argument("edited", type=Path)
    add_common_options(compare)
    compare.add_argument("--tolerance", type=float, default=0.001)
    return parser


def ensure_input(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ToolError(f"input VSDX does not exist: {resolved}")
    return resolved


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        vsdx_binary = resolve_vsdx_binary(args.vsdx)
        if args.command == "audit":
            path = ensure_input(args.file)
            thresholds = {
                "horizontalLanePadding": args.horizontal_lane_padding,
                "verticalLanePadding": args.vertical_lane_padding,
                "horizontalPeerGap": args.horizontal_peer_gap,
                "verticalPeerGap": args.vertical_peer_gap,
                "minimumPageUse": args.minimum_page_use,
                "rowCenterTolerance": args.row_center_tolerance,
                "rowAdjacencyMaximum": args.row_adjacency_maximum,
                "maximumPeerGapSpread": args.maximum_peer_gap_spread,
            }
            allowed_colors = set(
                color.lower()
                for color in (args.allowed_colors or DEFAULT_ALLOWED_COLORS)
            )
            report, _ = audit_document(
                path,
                vsdx_binary,
                render=not args.skip_render,
                render_dir=args.render_dir,
                thresholds=thresholds,
                allowed_colors=allowed_colors,
                color_lane_regex=args.color_lane_regex,
                allow_missing_semantic_ids=args.allow_missing_semantic_ids,
                allow_render_warnings=args.allow_render_warnings,
            )
            write_report(emit_report(report, args.format), args.output)
            return 0 if report["pass"] else 1

        baseline = ensure_input(args.baseline)
        edited = ensure_input(args.edited)
        report = compare_documents(
            baseline,
            edited,
            vsdx_binary,
            render=not args.skip_render,
            tolerance=args.tolerance,
        )
        write_report(emit_report(report, args.format), args.output)
        return 0
    except (ToolError, OSError, ValueError, re.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
