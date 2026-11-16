"""Animation integration and rejection tests; all assets are drawn locally."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
(ROOT / '.test-tmp').mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / 'skills/notebook-forge/scripts'))


def sample():
    data = json.loads((ROOT / 'examples/learning-notebook.json').read_text())
    data['pages'] = data['pages'][:1]
    data['topics'] = [{'id': 'test', 'title': 'Packet exchange'}]
    data['pages'][0].update(title='Packet exchange', covers=['test'])
    data['pages'][0]['blocks'] = [{
        'type': 'paragraph', 'label': 'Connection',
        'text': 'A request moves from the sender to the receiver.',
        'animation': {
            'id': 'packet', 'concept': 'Request delivery', 'layout': 'two endpoints',
            'pattern': 'packet moves right', 'motion_reason': 'Movement shows the request destination.',
            'alt': 'A request moves from left sender to right receiver.',
            'caption': 'The receiver gets the request sent by the sender.',
            'storyboard': {'title': 'Request delivery', 'frames': [
                {'label': 'Step 1: Send request', 'duration_ms': 800, 'objects': [
                    {'type': 'rect', 'box': [80, 220, 160, 300], 'fill': '#193963'}]},
                {'label': 'Step 2: Request arrives', 'duration_ms': 1800, 'objects': [
                    {'type': 'rect', 'box': [760, 220, 840, 300], 'fill': '#193963'}]}
            ]}
        }
    }]
    return data


class AnimationTests(unittest.TestCase):
    def setUp(self):
        import animations
        self.api = animations
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.job = sample()

    def build(self):
        return self.api.build_notes(self.job, self.root)

    def approve(self):
        manifest = json.loads((self.root / 'manifest.json').read_text())
        fingerprints = self.api.verify_bundle(self.job, self.root, require_review=False)['review_fingerprints']
        reviews = [{'section': e['section'], 'fingerprint': fingerprints[e['section']], 'approved': True,
                    'alignment': 'The request moves to the receiver described in this explanation.',
                    'readability': 'Large labels and two clear states show sending then arrival.',
                    'playback': 'Observed the request change position and loop with a final pause.'}
                   for e in manifest['gifs']]
        (self.root / 'review.json').write_text(json.dumps({'reviewer': 'Test fixture', 'gifs': reviews}))

    def test_generated_gif_and_review_gate(self):
        from PIL import Image
        self.build()
        with Image.open(self.root / 'assets/gifs/packet.gif') as gif:
            self.assertGreater(gif.n_frames, 1)
            self.assertEqual((960, 540), gif.size)
        self.api.verify_bundle(self.job, self.root, require_review=False)
        with self.assertRaisesRegex(ValueError, 'review'):
            self.api.verify_bundle(self.job, self.root)
        self.approve()
        self.assertTrue(self.api.verify_bundle(self.job, self.root)['pass2'])

    def test_missing_and_modified_files_fail(self):
        self.build()
        gif = self.root / 'assets/gifs/packet.gif'
        gif.write_bytes(b'not a gif')
        with self.assertRaises(ValueError):
            self.api.verify_bundle(self.job, self.root, require_review=False)
        gif.unlink()
        with self.assertRaises(ValueError):
            self.api.verify_bundle(self.job, self.root, require_review=False)

    def test_changed_explanation_invalidates_review(self):
        self.build()
        self.approve()
        self.job['pages'][0]['blocks'][0]['text'] += ' Changed.'
        with self.assertRaisesRegex(ValueError, 'changed|stale'):
            self.api.verify_bundle(self.job, self.root)

    def test_duplicate_layout_pattern_concept_and_pixels_fail(self):
        for field in ('id', 'layout', 'pattern', 'concept', 'pixels'):
            with self.subTest(field=field):
                data = sample()
                extra = copy.deepcopy(data['pages'][0]['blocks'][0])
                for key in ('id', 'layout', 'pattern', 'concept'):
                    extra['animation'][key] += ' different'
                extra['animation']['id'] = 'other'
                if field != 'pixels':
                    extra['animation'][field] = data['pages'][0]['blocks'][0]['animation'][field]
                data['pages'][0]['blocks'].append(extra)
                with self.assertRaisesRegex(ValueError, 'duplicate|repeated'):
                    self.api.build_notes(data, self.root)

    def test_unsafe_id_and_timing_and_clipped_text_fail(self):
        for value in ('../escape', 'https://example.org/a.gif', 'a/b', 'a\\b'):
            self.job['pages'][0]['blocks'][0]['animation']['id'] = value
            with self.assertRaises(ValueError):
                self.build()
        self.job = sample()
        animation = self.job['pages'][0]['blocks'][0]['animation']
        animation['storyboard']['frames'][0]['duration_ms'] = 20
        with self.assertRaisesRegex(ValueError, 'duration|timing'):
            self.build()
        animation['storyboard']['frames'][0]['duration_ms'] = 800
        animation['storyboard']['frames'][0]['objects'] = [
            {'type': 'text', 'xy': [940, 200], 'text': 'Cannot fit', 'size': 26}]
        with self.assertRaisesRegex(ValueError, 'clip|bounds'):
            self.build()

    def test_html_order_and_escaping(self):
        self.job['pages'][0]['blocks'][0]['text'] += ' <script>alert(1)</script>'
        self.build()
        html = (self.root / 'notebook.html').read_text()
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertLess(html.index('</p>'), html.index('<figure'))
        self.assertIn('alt="A request', html)
        self.assertIn('<figcaption>', html)
        (self.root / 'notebook.html').write_text(html.replace('assets/gifs/packet.gif', 'wrong.gif'))
        with self.assertRaises(ValueError):
            self.api.verify_bundle(self.job, self.root, require_review=False)

    def test_legacy_job_and_pdf_still(self):
        from pypdf import PdfReader
        self.build()
        text = '\n'.join(p.extract_text() for p in PdfReader(self.root / 'notebook.pdf').pages)
        self.assertIn('The receiver gets', text)
        self.job['pages'][0]['blocks'][0].pop('animation')
        self.build()
        self.assertEqual([], json.loads((self.root / 'manifest.json').read_text())['gifs'])

    def test_changed_still_and_contact_sheet_are_rejected(self):
        from PIL import Image
        for suffix in ('.png', '-frames.png'):
            with self.subTest(suffix=suffix):
                self.build()
                path = self.root / ('assets/gifs/packet' + suffix)
                Image.new('RGB', (960, 540), 'black').save(path)
                with self.assertRaisesRegex(ValueError, 'still|contact|changed'):
                    self.api.verify_bundle(self.job, self.root, require_review=False)

    def test_renderer_change_invalidates_review(self):
        from unittest.mock import patch
        self.build()
        self.approve()
        original = self.api.Path.read_text
        def changed(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            return result + '\n# renderer changed' if path.name == 'render_notebook.py' else result
        with patch.object(self.api.Path, 'read_text', changed):
            with self.assertRaisesRegex(ValueError, 'changed|stale'):
                self.api.verify_bundle(self.job, self.root)

    def test_output_path_resolution_rejects_redirected_files(self):
        from unittest.mock import patch
        self.build()
        original = self.api.Path.resolve
        escaped = self.root.parent / 'outside.gif'
        def redirected(path, *args, **kwargs):
            if path == self.root / 'assets/gifs/packet.gif':
                return escaped
            return original(path, *args, **kwargs)
        with patch.object(self.api.Path, 'resolve', redirected):
            with self.assertRaisesRegex(ValueError, 'escapes'):
                self.build()
        self.assertFalse(escaped.exists())


if __name__ == '__main__':
    unittest.main()
