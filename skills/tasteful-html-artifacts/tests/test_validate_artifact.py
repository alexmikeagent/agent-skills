from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_artifact.py"
SPEC = importlib.util.spec_from_file_location("validate_artifact", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def document(body: str, extra_css: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Decision report</title>
  <style>
    :root {{ --ink: #171817; }}
    body {{ color: var(--ink); }}
    :focus-visible {{ outline: 3px solid #005fcc; }}
    @media print {{ nav {{ display: none; }} }}
    {extra_css}
  </style>
</head>
<body>
  <main>
    <h1>Decision report</h1>
    {body}
  </main>
</body>
</html>
"""


class ValidateArtifactTests(unittest.TestCase):
    def test_clean_document_passes(self) -> None:
        errors, warnings = VALIDATOR.validate_source(
            document("<section><h2>Outcome</h2><p>Approved.</p></section>")
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_empty_alt_is_valid_for_decorative_image(self) -> None:
        errors, warnings = VALIDATOR.validate_source(
            document('<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="">')
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_alt_is_an_error(self) -> None:
        errors, _ = VALIDATOR.validate_source(document('<img src="diagram.png">'))
        self.assertTrue(any("missing an alt attribute" in item for item in errors))

    def test_duplicate_ids_and_broken_references_are_errors(self) -> None:
        errors, _ = VALIDATOR.validate_source(
            document(
                """
                <button aria-controls="missing">Open</button>
                <a href="#absent">Jump</a>
                <section id="same"><h2>One</h2></section>
                <section id="same"><h2>Two</h2></section>
                """
            )
        )
        self.assertTrue(any("Duplicate IDs" in item for item in errors))
        self.assertTrue(any("Broken internal anchors" in item for item in errors))
        self.assertTrue(any("Broken ARIA references" in item for item in errors))

    def test_accessible_controls_pass(self) -> None:
        errors, warnings = VALIDATOR.validate_source(
            document(
                """
                <label for="query">Search</label>
                <input id="query" type="search">
                <button type="button" aria-label="Clear search"></button>
                """
            )
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_unlabeled_control_warns(self) -> None:
        _, warnings = VALIDATOR.validate_source(document('<input type="text">'))
        self.assertTrue(any("lack an associated label" in item for item in warnings))

    def test_external_resource_and_local_path_are_reported(self) -> None:
        errors, warnings = VALIDATOR.validate_source(
            document(
                """
                <script src="https://cdn.example.com/app.js"></script>
                <p>/Users/example/private/source.md</p>
                """
            )
        )
        self.assertTrue(any("local filesystem path" in item for item in errors))
        self.assertTrue(any("External resources" in item for item in warnings))

    def test_undefined_css_variable_warns_but_fallback_does_not(self) -> None:
        _, warnings = VALIDATOR.validate_source(
            document(
                "<p>Content</p>",
                ".a { color: var(--missing); } .b { color: var(--optional, red); }",
            )
        )
        css_warning = next(
            item for item in warnings if "CSS variables used" in item
        )
        self.assertIn("--missing", css_warning)
        self.assertNotIn("--optional", css_warning)

    def test_heading_skip_warns(self) -> None:
        _, warnings = VALIDATOR.validate_source(
            document("<section><h3>Skipped level</h3></section>")
        )
        self.assertTrue(any("Heading levels skip" in item for item in warnings))

    def test_named_or_decorative_svg_passes(self) -> None:
        errors, warnings = VALIDATOR.validate_source(
            document(
                """
                <svg viewBox="0 0 10 10"><title>Trend line</title></svg>
                <svg viewBox="0 0 10 10" aria-hidden="true"></svg>
                """
            )
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
