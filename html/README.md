# Reader file formats (version 1)

This document defines the build output and browser behavior before implementation.
The Python builder will read `../annotation.txt`, `../plain.txt`, and
`../fragments/*.md` and write the generated files below. Source files remain
unchanged. No backend or browser-side Markdown parser is required.

## Files

```text
html/
  README.md          This format specification; maintained by hand
  index.html         Generated page, including the complete annotated poem
  fragments.json     Generated fragment content and reverse-link records
  fragments.js       Generated copy of the same data for direct local opening
  reader.js          Reader interaction code; maintained by hand
  style.css          Reader styles; maintained by hand
```

Run `python -m pip install -r requirements.txt` once, then `python update.py`
from the project root to rebuild the generated files. Open `html/index.html`
directly, or serve it with `python -m http.server --directory html`.
All asset URLs are relative, so the site can live under a subdirectory.
The page loads `fragments.js` before `reader.js`; it assigns the same JSON data
to `window.WASTELAND_DATA`, avoiding local-file fetch restrictions. JSON remains
available to other consumers. Both copies are generated from the same object.

## `index.html`

Use a UTF-8 HTML5 document with `lang="en"`, a viewport declaration, the title
“The Waste Land — T. S. Eliot”, and relative links to `style.css` and
`reader.js`. The script is deferred.

The main layout has two independently scrolling columns: the poem on the left
and a fragment panel on the right. On narrow screens these stack. Before a
selection, the fragment panel contains a short prompt to select highlighted
text. The poem remains readable if JavaScript or fragment loading fails.

Render the poem in a container with `id="poem"` and CSS
`white-space: pre-wrap`. Escape source text as HTML and preserve its exact
whitespace, punctuation, and final newline; do not introduce formatting
whitespace inside this container. Its `textContent` must equal `plain.txt`.
The page has no top title panel; the reading columns use the full window height.

Convert each `<ref>` to a span:

```html
<span id="ref-0001" class="reference" data-topic="sibyl" role="link" tabindex="0">…</span>
```

Assign IDs in opening-tag order, starting at `ref-0001` (minimum four digits).
IDs uniquely identify occurrences, even when a topic occurs repeatedly or is
nested inside another reference. They are deterministic for a given source;
adding an earlier annotation can renumber subsequent IDs. Topic identifiers,
in contrast, are stable filename stems.

Preserve nesting as nested spans; do not use nested anchor elements. Clicking
or pressing Enter on a reference selects that occurrence and loads its topic.
Handle the nearest reference to the event target only. Every enclosing
reference remains separately focusable, allowing access to outer annotations
even when an inner annotation covers the same words. Highlight references and
provide visible keyboard focus and selected-occurrence styling.

The right panel has `id="fragment-panel"`. After a selection, render the
fragment title, its body, and a “Referring passages” list at the end. Give the
panel a heading and announce changes through a short live status message.
Show errors there without removing the poem; offer reload if data failed to load.

## `fragments.json`

UTF-8 JSON with this shape (example values are illustrative):

```json
{
  "schema_version": 1,
  "fragments": {
    "chaucer": {
      "title": "Chaucer and the Canterbury Tales",
      "body_html": "",
      "references": [
        {
          "id": "ref-0003",
          "start_line": 14,
          "end_line": 17,
          "quote": "April is the cruellest month, breeding\n  Lilacs out of the dead land, mixing\n  Memory and desire, stirring\n  Dull roots with spring rain."
        }
      ]
    }
  }
}
```

- `schema_version`: integer `1`; reject unsupported versions visibly.
- `fragments`: object keyed by the exact Markdown filename stem, without a
  directory or extension. Include all fragment files, including unreferenced
  ones; their `references` lists are empty.
- `title`: plain text from the first top-level Markdown heading, or the topic
  identifier when no such heading exists. Render it as text, not HTML.
- `body_html`: Markdown rendered to an HTML fragment, with the title heading
  removed to avoid displaying it twice. A heading-only source produces an
  empty string. Disable raw HTML in Markdown and disallow unsafe link/image
  schemes; allow ordinary paragraphs, headings, lists, quotations, emphasis,
  code, and safe links. Do not embed reverse links in this field.
- `references`: one record per matching `<ref>`, in poem order. Include nested
  occurrences independently; never collapse repeated passages.
- `id`: the corresponding span ID in `index.html`.
- `start_line`, `end_line`: inclusive, one-based physical lines in `plain.txt`,
  including blank lines and the epigraph/dedication. These are source locations,
  not Eliot's printed verse numbers. The end line contains the last character
  of the span, excluding any trailing newline characters.
- `quote`: the full exact referenced text after removing all reference tags,
  including nested tags, while retaining original whitespace. The interface
  may shorten its display, but stores the full quote here.

The browser builds reverse links from `references`. Each list entry shows a
quote preview and source line range; its destination is the occurrence's ID.
Render quote text with `textContent`. An empty reference list displays
“No referring passages.” The JSON is the single source for fragment content
and reverse links; no separate per-topic HTML files or duplicate index is needed.

## Navigation state

Use URL fragments with query-string syntax:

```text
#topic=chaucer&ref=ref-0003
#topic=philomela
```

Parse and serialize with `URLSearchParams`. A poem click sets both values.
A reverse-link click sets both values, scrolls the matching poem span into
view, focuses it, and highlights it while keeping its fragment visible.
A topic-only URL opens that fragment without selecting an occurrence.
Support initial deep links and browser Back/Forward through `hashchange`.
Validate that a supplied occurrence belongs to the supplied topic; an invalid
occurrence is ignored, and an unknown topic produces a readable panel error.
Opening a new topic scrolls the fragment panel to its beginning.

## Builder contract

The Python builder validates inputs before replacing build output:

1. Strip only reference tags and compare the result exactly with `plain.txt`.
2. Reject malformed, unbalanced, or crossing tags, extra attributes, and empty
   references. Only `<ref topic="…">` and `</ref>` are annotation markup.
3. Require lowercase topic identifiers with hyphen-separated words
   (`[a-z0-9]+(?:-[a-z0-9]+)*`) and a matching `fragments/<topic>.md` file.
4. Derive span markup and backlink records from the same parse tree, ensuring
   every backlink has exactly one matching span with the same topic.
5. Produce deterministic HTML and JSON (no build timestamps, sorted fragment
   keys, references in source order), then replace generated files only after
   validation and rendering succeed. Never clear the output directory or
   overwrite the maintained files.

Verification should cover the existing nested annotations, repeated topics,
multiline spans, Unicode text, heading-only fragments, exact poem text
preservation, and backlink navigation. Run `python -m unittest discover -s tests`
for builder checks.
