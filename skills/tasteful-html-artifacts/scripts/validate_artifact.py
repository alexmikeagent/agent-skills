#!/usr/bin/env python3
"""Structural validator for portable, self-contained HTML artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ARIA_REFERENCE_ATTRIBUTES = ("aria-controls", "aria-labelledby", "aria-describedby")
FORM_CONTROL_TAGS = {"input", "select", "textarea"}
NON_LABEL_INPUT_TYPES = {"hidden", "button", "submit", "reset", "image"}
RESOURCE_ATTRIBUTES = {
    "script": ("src",),
    "link": ("href",),
    "img": ("src", "srcset"),
    "source": ("src", "srcset"),
    "video": ("src", "poster"),
    "audio": ("src",),
    "iframe": ("src",),
    "object": ("data",),
}
RESOURCE_LINK_RELS = {
    "stylesheet",
    "preload",
    "modulepreload",
    "icon",
    "manifest",
    "preconnect",
    "dns-prefetch",
}


class ArtifactParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.hrefs: list[str] = []
        self.aria_references: list[tuple[str, str]] = []
        self.external_resources: list[str] = []
        self.labels_for: set[str] = set()
        self.form_controls: list[dict[str, object]] = []
        self.heading_levels: list[int] = []

        self.has_title = False
        self.has_viewport = False
        self.has_charset = False
        self.html_lang = ""
        self.main_count = 0
        self.h1_count = 0
        self.images_without_alt = 0
        self.buttons_without_name = 0
        self.svgs_without_name = 0
        self.interactive_count = 0
        self.target_blank_without_rel = 0

        self._in_title = False
        self._in_button = False
        self._button_text = ""
        self._button_has_name_attr = False
        self._label_depth = 0
        self._svg_stack: list[dict[str, bool]] = []
        self._in_svg_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)

        element_id = data.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)

        if tag == "html":
            self.html_lang = data.get("lang", "").strip()
        elif tag == "meta":
            if data.get("name", "").lower() == "viewport":
                self.has_viewport = True
            if "charset" in data:
                self.has_charset = True
        elif tag == "main":
            self.main_count += 1
        elif re.fullmatch(r"h[1-6]", tag):
            level = int(tag[1])
            self.heading_levels.append(level)
            if level == 1:
                self.h1_count += 1
        elif tag == "title":
            if self._svg_stack:
                self._in_svg_title = True
            else:
                self._in_title = True
        elif tag == "a":
            href = data.get("href")
            if href:
                self.hrefs.append(href)
                self.interactive_count += 1
            if data.get("target", "").lower() == "_blank":
                rel = set(data.get("rel", "").lower().split())
                if not ({"noopener", "noreferrer"} & rel):
                    self.target_blank_without_rel += 1
        elif tag == "button":
            self.interactive_count += 1
            self._in_button = True
            self._button_text = ""
            self._button_has_name_attr = any(
                data.get(attr, "").strip()
                for attr in ("aria-label", "aria-labelledby", "title")
            )
        elif tag == "details":
            self.interactive_count += 1

        if tag == "label":
            self._label_depth += 1
            label_for = data.get("for")
            if label_for:
                self.labels_for.add(label_for)

        if tag in FORM_CONTROL_TAGS:
            input_type = data.get("type", "text").lower() if tag == "input" else ""
            if input_type not in NON_LABEL_INPUT_TYPES:
                self.interactive_count += 1
                self.form_controls.append(
                    {
                        "tag": tag,
                        "id": data.get("id", ""),
                        "inside_label": self._label_depth > 0,
                        "has_name_attr": any(
                            data.get(attr, "").strip()
                            for attr in ("aria-label", "aria-labelledby")
                        ),
                    }
                )

        if tag == "img" and "alt" not in data:
            self.images_without_alt += 1

        if tag == "svg":
            self._svg_stack.append(
                {
                    "named": any(
                        data.get(attr, "").strip()
                        for attr in ("aria-label", "aria-labelledby")
                    ),
                    "decorative": (
                        data.get("aria-hidden", "").lower() == "true"
                        or data.get("role", "").lower() in {"presentation", "none"}
                    ),
                    "has_title": False,
                }
            )

        for attribute in ARIA_REFERENCE_ATTRIBUTES:
            value = data.get(attribute, "")
            for target_id in value.split():
                self.aria_references.append((attribute, target_id))

        for attribute in RESOURCE_ATTRIBUTES.get(tag, ()):
            if tag == "link":
                rel = set(data.get("rel", "").lower().split())
                if not (rel & RESOURCE_LINK_RELS):
                    continue
            value = data.get(attribute)
            if value and is_external(value):
                self.external_resources.append(f"{tag}[{attribute}]={value}")

    def handle_data(self, data: str) -> None:
        if self._in_title and data.strip():
            self.has_title = True
        if self._in_svg_title and self._svg_stack and data.strip():
            self._svg_stack[-1]["has_title"] = True
        if self._in_button:
            self._button_text += data.strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            if self._in_svg_title:
                self._in_svg_title = False
            else:
                self._in_title = False
        elif tag == "button":
            if not self._button_text and not self._button_has_name_attr:
                self.buttons_without_name += 1
            self._in_button = False
        elif tag == "label":
            self._label_depth = max(0, self._label_depth - 1)
        elif tag == "svg" and self._svg_stack:
            svg = self._svg_stack.pop()
            if not (svg["named"] or svg["decorative"] or svg["has_title"]):
                self.svgs_without_name += 1


def is_external(url: str) -> bool:
    candidate = url.strip().split()[0]
    parsed = urlparse(candidate)
    return parsed.scheme in {"http", "https"} or candidate.startswith("//")


def heading_jumps(levels: list[int]) -> list[tuple[int, int]]:
    return [
        (previous, current)
        for previous, current in zip(levels, levels[1:])
        if current > previous + 1
    ]


def validate_source(source: str) -> tuple[list[str], list[str]]:
    parser = ArtifactParser()
    parser.feed(source)
    parser.close()

    errors: list[str] = []
    warnings: list[str] = []

    if "<!doctype html" not in source.lower():
        errors.append("Missing HTML doctype.")
    if not parser.html_lang:
        errors.append("Missing non-empty lang attribute on <html>.")
    if not parser.has_charset:
        warnings.append("Missing charset meta tag.")
    if not parser.has_title:
        errors.append("Missing non-empty <title>.")
    if not parser.has_viewport:
        errors.append("Missing viewport meta tag.")
    if parser.main_count != 1:
        errors.append(f"Expected exactly one <main> landmark; found {parser.main_count}.")
    if parser.h1_count == 0:
        errors.append("Missing <h1>.")
    elif parser.h1_count > 1:
        warnings.append(f"Multiple <h1> elements found: {parser.h1_count}.")

    if parser.duplicate_ids:
        errors.append("Duplicate IDs: " + ", ".join(sorted(parser.duplicate_ids)))

    broken_anchors = {
        href
        for href in parser.hrefs
        if href.startswith("#") and len(href) > 1 and href[1:] not in parser.ids
    }
    if broken_anchors:
        errors.append("Broken internal anchors: " + ", ".join(sorted(broken_anchors)))

    unsafe_hrefs = sorted(
        {href for href in parser.hrefs if href.strip().lower().startswith("javascript:")}
    )
    if unsafe_hrefs:
        errors.append("Unsafe javascript: links found: " + ", ".join(unsafe_hrefs))

    broken_aria = sorted(
        {
            f"{attribute}={target_id}"
            for attribute, target_id in parser.aria_references
            if target_id not in parser.ids
        }
    )
    if broken_aria:
        errors.append("Broken ARIA references: " + ", ".join(broken_aria))

    if parser.images_without_alt:
        errors.append(
            f"{parser.images_without_alt} image(s) missing an alt attribute. "
            'Use alt="" for decorative images.'
        )
    if parser.buttons_without_name:
        errors.append(
            f"{parser.buttons_without_name} button(s) lack visible text or an accessible name."
        )
    if parser.svgs_without_name:
        warnings.append(
            f"{parser.svgs_without_name} SVG(s) lack a title/accessible name "
            "or explicit decorative state."
        )

    unlabeled_controls = [
        control
        for control in parser.form_controls
        if not (
            control["inside_label"]
            or control["has_name_attr"]
            or (control["id"] and control["id"] in parser.labels_for)
        )
    ]
    if unlabeled_controls:
        warnings.append(
            f"{len(unlabeled_controls)} form control(s) may lack an associated label."
        )

    jumps = heading_jumps(parser.heading_levels)
    if jumps:
        formatted = ", ".join(f"h{start}→h{end}" for start, end in jumps)
        warnings.append("Heading levels skip: " + formatted)

    if parser.target_blank_without_rel:
        warnings.append(
            f"{parser.target_blank_without_rel} target=\"_blank\" link(s) lack "
            'rel="noopener" or rel="noreferrer".'
        )

    if parser.external_resources:
        warnings.append(
            "External resources found: " + ", ".join(sorted(parser.external_resources))
        )

    external_css_urls = sorted(
        {
            match.group(1)
            for match in re.finditer(
                r"url\(\s*['\"]?((?:https?:)?//[^)'\"\s]+)",
                source,
                re.IGNORECASE,
            )
        }
    )
    if external_css_urls:
        warnings.append("External CSS URLs found: " + ", ".join(external_css_urls))

    local_path_patterns = (
        r"file://",
        r"/Users/[^/\s]+/",
        r"/home/[^/\s]+/",
        r"[A-Za-z]:\\Users\\[^\\\s]+\\",
    )
    if any(re.search(pattern, source, re.IGNORECASE) for pattern in local_path_patterns):
        errors.append("Possible unresolved local filesystem path found.")

    css_definitions = set(
        re.findall(r"(?<![\w-])(--[A-Za-z0-9_-]+)\s*:", source)
    )
    css_uses_without_fallback = {
        name
        for name, separator in re.findall(
            r"var\(\s*(--[A-Za-z0-9_-]+)\s*([,)])", source
        )
        if separator == ")" and name not in css_definitions
    }
    if css_uses_without_fallback:
        warnings.append(
            "CSS variables used without definitions or fallbacks: "
            + ", ".join(sorted(css_uses_without_fallback))
        )

    has_motion = bool(
        re.search(
            r"(?:scroll-behavior\s*:\s*smooth|"
            r"\btransition(?:-[\w-]+)?\s*:|"
            r"\banimation(?:-[\w-]+)?\s*:|"
            r"@keyframes\b)",
            source,
            re.IGNORECASE,
        )
    )
    if has_motion and "prefers-reduced-motion" not in source:
        warnings.append("Motion detected without prefers-reduced-motion handling.")

    if parser.interactive_count and ":focus-visible" not in source:
        warnings.append("Interactive elements found without :focus-visible styling.")
    if "@media print" not in source:
        warnings.append("No print stylesheet detected.")

    placeholder_patterns = (
        r"\blorem ipsum\b",
        r"\bTODO\b",
        r"\bFIXME\b",
        r"\bREPLACE_THIS\b",
        r"\bArtifact title\b",
        r"\bReplace with\b",
    )
    if any(re.search(pattern, source, re.IGNORECASE) for pattern in placeholder_patterns):
        warnings.append("Possible placeholder or template text detected.")

    if re.search(r"\.innerHTML\s*=", source):
        warnings.append("innerHTML assignment detected; verify source text is escaped.")

    return errors, warnings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a portable, self-contained HTML artifact."
    )
    parser.add_argument("artifact", type=Path)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a failing exit code when warnings remain.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    path: Path = args.artifact

    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2
    if not path.is_file():
        print(f"ERROR: not a file: {path}")
        return 2

    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"ERROR: file is not valid UTF-8: {path}")
        return 2

    errors, warnings = validate_source(source)

    print(f"Validated: {path}")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARNING: {item}")

    if errors:
        print("FAIL")
        return 1
    if warnings:
        if args.strict:
            print("FAIL: warnings remain in strict mode.")
            return 1
        print("PASS WITH WARNINGS")
        return 0

    print("PASS: no structural issues detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
