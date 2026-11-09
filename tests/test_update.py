import json
from pathlib import Path
import tempfile
import unittest

import update


class BuilderTests(unittest.TestCase):
    def test_nested_multiline_and_repeated_topics(self):
        annotated = '<ref topic="a">α\n<ref topic="b">β</ref>\n</ref> <ref topic="a">γ</ref>\n'
        markup, refs = update.parse_annotations(annotated, 'α\nβ\n γ\n', {'a', 'b'})
        self.assertEqual([r['id'] for r in refs], ['ref-0001', 'ref-0002', 'ref-0003'])
        self.assertEqual(refs[0]['quote'], 'α\nβ\n')
        self.assertEqual((refs[0]['start_line'], refs[0]['end_line']), (1, 2))
        self.assertEqual(refs[2]['topic'], 'a')
        self.assertIn('data-topic="b"', markup)

    def test_invalid_inputs(self):
        cases = [
            ('<ref topic="a">x', 'x'),
            ('x</ref>', 'x'),
            ('<ref topic="a" extra="x">x</ref>', 'x'),
            ('<ref topic="missing">x</ref>', 'x'),
            ('<ref topic="a"></ref>', ''),
            ('<ref topic="a">x</ref>', 'y'),
        ]
        for annotated, plain in cases:
            with self.subTest(annotated=annotated), self.assertRaises(ValueError):
                update.parse_annotations(annotated, plain, {'a'})

    def test_build_is_deterministic_and_failure_preserves_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'fragments').mkdir()
            (root / 'fragments/a.md').write_text('# A title\n', encoding='utf-8')
            (root / 'fragments/b.md').write_text('# Unused\n\n<script>x</script>\n\n[x](javascript:alert(1))\n', encoding='utf-8')
            (root / 'plain.txt').write_text('α\n', encoding='utf-8')
            (root / 'annotation.txt').write_text('<ref topic="a">α</ref>\n', encoding='utf-8')
            update.build(root)
            before = {p.name: p.read_bytes() for p in (root / 'html').iterdir()}
            data = json.loads(before['fragments.json'])
            self.assertEqual(data['fragments']['a']['body_html'], '')
            self.assertEqual(data['fragments']['b']['references'], [])
            self.assertNotIn('<script>', data['fragments']['b']['body_html'])
            self.assertNotIn('href="javascript:', data['fragments']['b']['body_html'])
            update.build(root)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root / 'html').iterdir()})
            (root / 'plain.txt').write_text('changed\n')
            with self.assertRaises(ValueError):
                update.build(root)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root / 'html').iterdir()})


if __name__ == '__main__':
    unittest.main()
