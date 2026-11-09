We are to create a website for reading T. S. Eliot's Waste Land.

Waste Land is to be read as a pile of fragments, the corrupted fragments
of readers' shared consciousness.  Each fragment has a corresponding
markdown file with a short name, which we'll use in the text it self to
create links.

annotation.txt contains the poem from plain.txt with annotations added.
An annotation is a reference to a fragment, e.g.

...
<ref topic="pervigilium">Quando fiam ceu chelidon</ref> —
  <ref topic="tennyson">O swallow swallow</ref>
...

It's not a proper full HTML, but only with the <ref> tag to annotate
spans.

## File relations

| File | Role and relation to other files |
| --- | --- |
| `raw.txt` | Source edition: includes the title, contents, poem, Eliot's notes, and Project Gutenberg material. Preserve it as the source reference. |
| `plain.txt` | Clean poem text extracted from `raw.txt`: the epigraph, dedication, and five sections, without the contents, printed line numbers, source formatting markers, notes, or Gutenberg material. This is the text baseline for `annotation.txt`. |
| `annotation.txt` | Annotated version of `plain.txt`. Add only `<ref topic="name">…</ref>` tags; removing those tags must reproduce `plain.txt` exactly, including punctuation, indentation, blank lines, and the final newline. |
| `fragments/<topic>.md` | Markdown fragment addressed by a reference's `topic` attribute. For example, `topic="pervigilium"` resolves to `fragments/pervigilium.md`. The filename stem is the stable topic identifier; do not include the directory or `.md` in the attribute. |
| `AGENTS.md` | Project intent, annotation conventions, and documentation of these file relations. |

The text flows from `raw.txt` to `plain.txt` to `annotation.txt`.
References in `annotation.txt` link spans of the poem to files in `fragments/`.
Eliot's notes in `raw.txt` can inform fragments, but are not part of the
reading text in `plain.txt` or `annotation.txt`.

## Editing conventions

- Preserve `raw.txt` when editing annotations or fragments. If a correction
  to the reading text is intentional, update `plain.txt` and the corresponding
  text in `annotation.txt` together.
- Reuse an existing fragment topic wherever the same allusion returns,
  including across sections. For example, the Phoenician Sailor and Phlebas
  both reference `phoenician`; Philomela references share `philomela`.
- Create `fragments/<topic>.md` when a needed topic is missing. Use a short,
  descriptive lowercase filename with hyphens between words. Every reference
  must resolve to an existing fragment file.
- References may span multiple lines and may nest when a passage relates to
  several fragments. Keep tags balanced and properly nested; spans must not
  cross. Use only the `topic` attribute and do not add HTML wrappers to the file.
- Preserve the wording of the poem when selecting spans. A fragment may
  discuss a textual variant without changing the reading text to that variant.
- Validate edits by stripping reference tags and comparing the result with
  `plain.txt`, checking balanced nesting, and checking that every topic resolves
  to a Markdown file in `fragments/`.


