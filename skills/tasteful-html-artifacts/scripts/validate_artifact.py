#!/usr/bin/env python3
"""Lightweight structural validator for self-contained HTML artifacts."""

from __future__ import annotations
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

class ArtifactParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.has_title = False
        self.has_main = False
        self.has_h1 = False
        self.has_viewport = False
        self.external_scripts: list[str] = []
        self.external_styles: list[str] = []
        self.images_without_alt = 0
        self.buttons_without_text = 0
        self._in_title = False
        self._in_button = False
        self._button_text = ""

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        data = dict(attrs)
        if "id" in data:
            self.ids.add(data["id"])
        if tag == "a" and "href" in data:
            self.hrefs.append(data["href"])
        if tag == "main":
            self.has_main = True
        if tag == "h1":
            self.has_h1 = True
        if tag == "title":
            self._in_title = True
        if tag == "meta" and data.get("name", "").lower() == "viewport":
            self.has_viewport = True
        if tag == "script" and data.get("src"):
            self.external_scripts.append(data["src"])
        if tag == "link" and data.get("rel") == "stylesheet" and data.get("href"):
            self.external_styles.append(data["href"])
        if tag == "img" and not data.get("alt"):
            self.images_without_alt += 1
        if tag == "button":
            self._in_button = True
            self._button_text = ""

    def handle_data(self, data):
        if self._in_title and data.strip():
            self.has_title = True
        if self._in_button:
            self._button_text += data.strip()

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "button":
            if not self._button_text:
                self.buttons_without_text += 1
            self._in_button = False

def is_external(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} or url.startswith("//")

def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_artifact.py artifact.html")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2

    source = path.read_text(encoding="utf-8")
    parser = ArtifactParser()
    parser.feed(source)

    errors: list[str] = []
    warnings: list[str] = []

    if "<!doctype html" not in source.lower():
        errors.append("Missing HTML doctype.")
    if not parser.has_title:
        errors.append("Missing non-empty <title>.")
    if not parser.has_viewport:
        errors.append("Missing viewport meta tag.")
    if not parser.has_main:
        warnings.append("Missing <main> landmark.")
    if not parser.has_h1:
        errors.append("Missing <h1>.")
    if parser.images_without_alt:
        errors.append(f"{parser.images_without_alt} image(s) missing alt text.")
    if parser.buttons_without_text:
        warnings.append(f"{parser.buttons_without_text} button(s) lack visible text; verify aria-label.")
    if parser.external_scripts:
        warnings.append("External scripts found: " + ", ".join(parser.external_scripts))
    if parser.external_styles:
        warnings.append("External stylesheets found: " + ", ".join(parser.external_styles))

    broken = []
    for href in parser.hrefs:
        if href.startswith("#") and len(href) > 1 and href[1:] not in parser.ids:
            broken.append(href)
    if broken:
        errors.append("Broken internal anchors: " + ", ".join(sorted(set(broken))))

    if "prefers-reduced-motion" not in source:
        warnings.append("No prefers-reduced-motion handling detected.")
    if "@media print" not in source:
        warnings.append("No print stylesheet detected.")
    if re.search(r"\b(lorem ipsum|todo:|replace me|placeholder)\b", source, re.I):
        warnings.append("Possible placeholder text detected.")
    if re.search(r"<script[^>]*>\s*.*innerHTML\s*=", source, re.I | re.S):
        warnings.append("innerHTML assignment detected; verify source text is escaped.")

    print(f"Validated: {path}")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARNING: {item}")
    if not errors and not warnings:
        print("PASS: no structural issues detected.")
    elif not errors:
        print("PASS WITH WARNINGS")
    else:
        print("FAIL")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
