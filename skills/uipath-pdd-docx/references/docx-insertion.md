# DOCX Insertion

## Goal

Use this guide when turning drafted markdown into a clean Word section.

## Section replacement strategy

Prefer replacing content between two heading anchors instead of editing random paragraphs in place.

Typical pattern:

1. locate the start heading
2. locate the next stable heading after the target section
3. remove everything in between
4. rebuild the section in order

This is safer than partial paragraph edits when the template contains tables, bookmarks, or numbering.

## Heading rules

- Reuse the template's `Heading 1`, `Heading 2`, and `Heading 3` styles.
- Do not prepend `3.1`, `3.2`, and similar values if the template already auto-numbers headings.
- If the template does not auto-number, then add explicit numbering in the text.

## Shared dispatcher and performer documents

For shared PDDs:

- keep the section heading generic
- insert a short italic scope note before the component content
- phrase body text so it can coexist with later performer content
- avoid global out-of-scope statements unless confirmed for both components

Recommended note examples:

- `Note: The rows below document dispatcher-owned scope only within the shared PDD.`
- `Note: Add performer-specific exceptions below this point in a later pass.`

## Table formatting rules

Use Word-native tables with these defaults:

- `Table Grid` style unless the template uses a stricter house style
- fixed widths sized to the document's usable width
- repeated header row
- header shading
- top-aligned cells
- cell padding
- slightly looser row spacing

Avoid:

- relying on autofit alone for wide tables
- heavy monospace text inside dense tables
- very small font sizes unless absolutely required

If headers still wrap badly, change the column distribution rather than shrinking the font first.

## Diagram rules

- Mermaid should be converted before insertion
- prefer an image if layout matters
- verify the image visually at the actual inserted width
- split dense process maps into multiple images when one page width is not enough
- move long explanatory text out of the diagram and back into Word notes or paragraphs

## Validation checklist

After rebuilding the section, verify:

- headings render once, not twice
- inserted images are present and readable
- table headers are not stacked awkwardly
- dense cell text has enough padding and width
- row order still matches the markdown content
- the next section heading remains intact
