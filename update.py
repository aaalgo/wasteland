#!/usr/bin/env python3
"""Validate the annotated poem and build the static reader. Run: python update.py."""

import bisect
import difflib
import html
import json
from pathlib import Path
import re
import sys
import tempfile

try:
    from markdown_it import MarkdownIt
except ImportError:
    sys.exit("Install the builder dependency: python -m pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent
TOPIC = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TAG = re.compile(r'<ref topic="([a-z0-9]+(?:-[a-z0-9]+)*)">|</ref>')


def parse_annotations(annotated, plain, topics):
    """Produce escaped span HTML and source locations from a single token walk."""
    output, text, references, stack = [], [], [], []
    offset = 0
    position = 0
    for match in TAG.finditer(annotated):
        chunk = annotated[position:match.start()]
        if '<' in chunk or '>' in chunk:
            raise ValueError("Unexpected or malformed markup in annotation.txt")
        output.append(html.escape(chunk))
        text.append(chunk)
        offset += len(chunk)
        if match.group(1):
            topic = match.group(1)
            if topic not in topics:
                raise ValueError(f"Missing fragment: fragments/{topic}.md")
            ref = dict(id=f"ref-{len(references) + 1:04d}", topic=topic, start=offset)
            references.append(ref)
            stack.append(ref)
            output.append(f'<span id="{ref["id"]}" class="reference" '
                          f'data-topic="{topic}" role="link" tabindex="0">')
        else:
            if not stack:
                raise ValueError("Closing reference without an opening tag")
            ref = stack.pop()
            ref['end'] = offset
            if ref['start'] == offset:
                raise ValueError(f"Empty reference: {ref['id']}")
            output.append('</span>')
        position = match.end()
    chunk = annotated[position:]
    if '<' in chunk or '>' in chunk:
        raise ValueError("Unexpected or malformed markup in annotation.txt")
    output.append(html.escape(chunk))
    text.append(chunk)
    if stack:
        raise ValueError("Unclosed reference tags")
    stripped = ''.join(text)
    if stripped != plain:
        difference = ''.join(difflib.unified_diff(
            plain.splitlines(keepends=True), stripped.splitlines(keepends=True),
            fromfile='plain.txt', tofile='annotation.txt (reference tags removed)'))
        raise ValueError(
            "Removing reference tags does not reproduce plain.txt exactly.\n"
            "For intentional wording or whitespace changes, update plain.txt too.\n"
            "The generated page was not changed.\n" + difference)
    line_starts = [0] + [m.end() for m in re.finditer('\n', plain)]
    for ref in references:
        start, end = ref.pop('start'), ref.pop('end')
        ref['quote'] = plain[start:end]
        last = max(start, start + len(ref['quote'].rstrip('\n')) - 1)
        ref['start_line'] = bisect.bisect_right(line_starts, start)
        ref['end_line'] = bisect.bisect_right(line_starts, last)
    return ''.join(output), references


def render_fragment(path, markdown):
    source = path.read_bytes().decode('utf-8')
    tokens = markdown.parse(source)
    title = path.stem
    for index, token in enumerate(tokens):
        if token.type == 'heading_open' and token.tag == 'h1' and token.level == 0:
            inline = tokens[index + 1]
            title = ''.join(child.content for child in inline.children or []
                            if child.type not in ('html_inline', 'softbreak', 'hardbreak'))
            lines = source.splitlines(keepends=True)
            first, last = token.map
            source = ''.join(lines[:first] + lines[last:])
            break
    return dict(title=title, body_html=markdown.render(source), references=[])


def build(root=ROOT):
    paths = sorted((root / 'fragments').glob('*.md'))
    if not paths:
        raise ValueError("No Markdown fragments found")
    for path in paths:
        if not TOPIC.fullmatch(path.stem):
            raise ValueError(f"Invalid topic filename: {path.name}")
    plain = (root / 'plain.txt').read_bytes().decode('utf-8')
    annotated = (root / 'annotation.txt').read_bytes().decode('utf-8')
    poem, references = parse_annotations(annotated, plain, {p.stem for p in paths})
    markdown = MarkdownIt('commonmark', {'html': False})
    fragments = {p.stem: render_fragment(p, markdown) for p in paths}
    for ref in references:
        record = dict(ref)
        topic = record.pop('topic')
        fragments[topic]['references'].append(record)
    data = json.dumps(dict(schema_version=1, fragments=fragments),
                      ensure_ascii=False, indent=2) + '\n'
    page = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The Waste Land — T. S. Eliot</title>
  <link rel="stylesheet" href="style.css">
  <script src="fragments.js" defer></script>
  <script src="reader.js" defer></script>
</head>
<body>
  <main class="reader">
    <section class="poem-column" aria-label="The poem">
      <div id="poem">''' + poem + '''</div>
    </section>
    <aside id="fragment-panel" aria-label="Fragment">
      <div id="fragment-content"><p class="eyebrow">Fragments</p>
      <h2>A gathering of echoes</h2><p>Select a highlighted passage in the poem
      to follow an allusion. Each fragment offers a way back to every passage
      that refers to it.</p></div>
    </aside>
  </main>
  <p id="status" class="sr-only" role="status" aria-live="polite"></p>
  <noscript><p class="notice">Enable JavaScript to explore the fragments.</p></noscript>
</body>
</html>
'''
    # A script bundle supports file://, where browsers block fetching local JSON.
    bundle = 'window.WASTELAND_DATA = ' + data.rstrip() + ';\n'
    outputs = {'index.html': page, 'fragments.json': data, 'fragments.js': bundle}
    destination = root / 'doc'
    destination.mkdir(exist_ok=True)
    # Finish every validation and render before staging any replacement.
    with tempfile.TemporaryDirectory(dir=destination, prefix='.build-') as staging:
        for name, content in outputs.items():
            (Path(staging) / name).write_bytes(content.encode('utf-8'))
        for name in outputs:
            (Path(staging) / name).replace(destination / name)
    print(f"Built html/index.html: {len(fragments)} fragments, {len(references)} references.")


if __name__ == '__main__':
    try:
        build()
    except (ValueError, OSError, UnicodeError) as error:
        sys.exit(f"Build failed: {error}")
