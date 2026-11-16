import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/notebook-forge/scripts'))
from test_animations import sample


def image_job():
    data = sample()
    data['media'] = {'confirmed': True, 'images': True, 'gifs': False}
    block = data['pages'][0]['blocks'][0]
    animation = block.pop('animation')
    block['illustration'] = {k: animation[k] for k in ('id', 'concept', 'layout', 'alt', 'caption')}
    block['illustration'].update(topic='test', scene={
        'title': 'Request delivery', 'label': 'Sender sends; receiver receives',
        'objects': [
            {'type': 'text', 'xy': [50, 180], 'text': 'SENDER'},
            {'type': 'text', 'xy': [700, 180], 'text': 'RECEIVER'},
            {'type': 'arrow', 'xy': [200, 280, 760, 280]},
            {'type': 'text', 'xy': [340, 320], 'text': 'Request packet'}]})
    return data


class IllustrationTests(unittest.TestCase):
    def setUp(self):
        import animations
        self.api = animations
        (ROOT / '.test-tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_each_media_kind_requires_explicit_permission(self):
        for kind in ('image', 'gif'):
            for consent in (None, {'confirmed': False, 'images': True, 'gifs': True},
                            {'confirmed': True, 'images': False, 'gifs': False}):
                data = image_job() if kind == 'image' else sample()
                if consent is None:
                    data.pop('media', None)
                else:
                    data['media'] = consent
                with self.subTest(kind=kind, consent=consent):
                    with self.assertRaisesRegex(ValueError, 'permission|consent|approve'):
                        self.api.build_notes(data, self.root)

    def test_approved_images_require_every_nested_topic(self):
        data = image_job()
        data['topics'].append({'id': 'child', 'title': 'Response', 'parent': 'test'})
        data['pages'].append({'title': 'Response', 'covers': ['child'], 'blocks': [
            {'type': 'paragraph', 'label': 'Explain', 'text': 'The receiver sends a response.'}]})
        with self.assertRaisesRegex(ValueError, 'child|coverage'):
            self.api.build_notes(data, self.root)

    def test_image_embedded_in_pdf_and_html_and_requires_review(self):
        from pypdf import PdfReader
        data = image_job()
        self.api.build_notes(data, self.root)
        manifest = json.loads((self.root / 'manifest.json').read_text())
        self.assertEqual(1, len(manifest['images']))
        self.assertTrue((self.root / 'assets/images/packet.png').is_file())
        pdf = PdfReader(self.root / 'notebook.pdf')
        self.assertGreater(sum(len(list(p.images)) for p in pdf.pages), 0)
        html = (self.root / 'notebook.html').read_text()
        self.assertIn('</p>\n<figure data-topic="test"', html)
        self.assertIn('assets/images/packet.png', html)
        self.assertNotIn('.gif"', html)
        with self.assertRaisesRegex(ValueError, 'review'):
            self.api.verify_bundle(data, self.root)
        fingerprints = self.api.verify_bundle(data, self.root, require_review=False)['image_review_fingerprints']
        review = {'reviewer': 'Explicit unit-test fixture', 'images': [
            {'section': 'page-0-block-0', 'fingerprint': fingerprints['page-0-block-0'], 'approved': True,
             'alignment': 'Sender and receiver match the request explanation.',
             'readability': 'Large labels and the arrow are readable and distinct.'}]}
        (self.root / 'review.json').write_text(json.dumps(review))
        self.assertTrue(self.api.verify_bundle(data, self.root)['pass2'])
        from PIL import Image
        Image.new('RGB', (960, 540), 'white').save(self.root / manifest['images'][0]['path'])
        with self.assertRaises(ValueError):
            self.api.verify_bundle(data, self.root)

    def test_wrong_topic_and_duplicate_scene_rejected(self):
        data = image_job()
        data['pages'][0]['blocks'][0]['illustration']['topic'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'topic'):
            self.api.build_notes(data, self.root)
        data = image_job()
        extra = copy.deepcopy(data['pages'][0]['blocks'][0])
        for key in ('id', 'concept', 'layout'):
            extra['illustration'][key] += '-other'
        data['pages'][0]['blocks'].append(extra)
        with self.assertRaisesRegex(ValueError, 'duplicate|repeated'):
            self.api.build_notes(data, self.root)

    def test_permission_denied_text_only_still_renders(self):
        data = image_job()
        self.api.build_notes(data, self.root)
        data['media']['images'] = False
        data['pages'][0]['blocks'][0].pop('illustration')
        self.api.build_notes(data, self.root)
        self.assertEqual([], json.loads((self.root / 'manifest.json').read_text())['images'])
        self.assertFalse((self.root / 'assets/images/packet.png').exists())

    def test_both_types_approved_gif_stays_in_html(self):
        from pypdf import PdfReader
        data = image_job()
        data['media']['gifs'] = True
        data['pages'][0]['blocks'][0]['animation'] = sample()['pages'][0]['blocks'][0]['animation']
        self.api.build_notes(data, self.root)
        manifest = json.loads((self.root / 'manifest.json').read_text())
        self.assertEqual((1, 1), (len(manifest['images']), len(manifest['gifs'])))
        pdf = PdfReader(self.root / 'notebook.pdf')
        self.assertEqual(1, sum(len(list(p.images)) for p in pdf.pages))
        self.assertIn('assets/gifs/packet.gif', (self.root / 'notebook.html').read_text())

    def test_manifest_wrong_topic_rejected_and_refusal_preserves_outputs(self):
        data = image_job()
        self.api.build_notes(data, self.root)
        original = (self.root / 'notebook.pdf').read_bytes()
        denied = copy.deepcopy(data)
        denied['media']['images'] = False
        with self.assertRaisesRegex(ValueError, 'permission'):
            self.api.build_notes(denied, self.root)
        self.assertEqual(original, (self.root / 'notebook.pdf').read_bytes())
        manifest = json.loads((self.root / 'manifest.json').read_text())
        manifest['images'][0]['topic'] = 'unrelated'
        (self.root / 'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'topic|placement'):
            self.api.verify_bundle(data, self.root, require_review=False)

    def test_caption_and_alt_stay_with_image_across_continuation_pages(self):
        from pypdf import PdfReader
        for count in (40, 44, 48, 52):
            with self.subTest(count=count):
                data = image_job()
                data['pages'][0]['blocks'][0]['text'] = 'The diagram belongs to this explanation. ' * count
                self.api.build_notes(data, self.root)
                pdf = PdfReader(self.root / 'notebook.pdf')
                for page in pdf.pages:
                    if list(page.images):
                        text = page.extract_text()
                        self.assertIn('The receiver gets', text)
                        self.assertIn('Alt text:', text)


if __name__ == '__main__':
    unittest.main()
