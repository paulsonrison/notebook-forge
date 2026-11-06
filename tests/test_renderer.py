import copy
import importlib.util
import json
import re
from pathlib import Path
import tempfile
import unittest

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
(ROOT / '.test-tmp').mkdir(exist_ok=True)
SCRIPT = ROOT / "skills/notebook-forge/scripts/render_notebook.py"


def job(mode="subtopic-pages"):
    return {
        "title": "Learning notebook",
        "theme": {"name": "notebook", "confirmed": True},
        "layout": {"mode": mode, "confirmed": True},
        "sources": [{"kind": "topic", "value": "Memory techniques"}],
        "topics": [
            {"id": "memory", "title": "Memory"},
            {"id": "recall", "title": "Active recall", "parent": "memory"},
        ],
        "pages": [
            {"title": "Memory", "covers": ["memory"], "blocks": [
                {"type": "paragraph", "label": "The idea", "text": "Practise remembering, then check your answer."}]},
            {"title": "Active recall", "covers": ["recall"], "blocks": [
                {"type": "bullets", "label": "Try it", "items": ["Close the book.", "Explain the concept."]}]},
        ],
    }


class RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = None
        if SCRIPT.exists():
            spec = importlib.util.spec_from_file_location("render_notebook", SCRIPT)
            cls.renderer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.renderer)

    def require_renderer(self):
        if self.renderer is None:
            self.skipTest("Renderer has not been implemented")
        return self.renderer

    def test_renderer_entrypoint_exists(self):
        self.assertTrue(SCRIPT.exists(), "Portable renderer is missing")

    def test_confirmation_is_required_for_both_choices(self):
        module = self.require_renderer()
        for field in ("theme", "layout"):
            for bad in (False, "true", 1, None):
                data = job()
                data[field]["confirmed"] = bad
                with self.subTest(field=field, bad=bad):
                    with self.assertRaisesRegex(ValueError, "confirm"):
                        module.validate_job(data)

    def test_missing_source_requires_input(self):
        module = self.require_renderer()
        for sources in ([], [{"kind": "topic", "value": " "}]):
            data = job()
            data["sources"] = sources
            with self.assertRaisesRegex(ValueError, "source"):
                module.validate_job(data)

    def test_nested_topic_requires_dedicated_page(self):
        module = self.require_renderer()
        data = job()
        data["topics"].append({"id": "practice", "title": "Practice", "parent": "recall"})
        with self.assertRaisesRegex(ValueError, "practice"):
            module.validate_job(data)
        data["pages"][1]["covers"].append("practice")
        with self.assertRaisesRegex(ValueError, "dedicated"):
            module.validate_job(data)

    def test_grouped_layout_accepts_combined_subtopics(self):
        module = self.require_renderer()
        data = job("topic-pages")
        data["pages"][0]["covers"].append("recall")
        data["pages"] = data["pages"][:1]
        module.validate_job(data)

    def test_cycles_and_duplicate_ids_are_rejected(self):
        module = self.require_renderer()
        data = job()
        data["topics"][0]["parent"] = "recall"
        with self.assertRaisesRegex(ValueError, "cycle"):
            module.validate_job(data)
        data = job()
        data["topics"][1]["id"] = "memory"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            module.validate_job(data)

    def test_render_has_searchable_text_bookmarks_and_contents_links(self):
        module = self.require_renderer()
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as tmp:
            output = Path(tmp) / "book.pdf"
            report = module.render_notebook(job(), output)
            doc = PdfReader(output)
            self.assertEqual(4, len(doc.pages))  # cover, contents, two topics
            self.assertEqual(4, report["pages"])
            self.assertIn("Practise remembering", doc.pages[2].extract_text())
            self.assertTrue(doc.outline)
            self.assertTrue(doc.pages[1].get("/Annots"))

    def test_long_content_continues_without_losing_tail(self):
        module = self.require_renderer()
        data = job()
        data["pages"][0]["blocks"][0]["text"] = ("Remember this principle. " * 900) + "UNIQUE-END-MARKER"
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as tmp:
            output = Path(tmp) / "long.pdf"
            report = module.render_notebook(data, output)
            doc = PdfReader(output)
            self.assertGreater(report["pages"], 4)
            text = "\n".join(p.extract_text() for p in doc.pages)
            self.assertIn("UNIQUE-END-MARKER", text)
            # Headers/footers interrupt a sentence spanning a page boundary.
            self.assertEqual(900, len(re.findall(r"\bRemember\b", text)))
            self.assertEqual(900, len(re.findall(r"\bprinciple\b", text)))

    def test_long_code_lines_fail_with_actionable_message(self):
        module = self.require_renderer()
        data = job()
        data["pages"][0]["blocks"] = [{"type": "code", "label": "Example", "text": "x" * 300}]
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as tmp:
            with self.assertRaisesRegex(ValueError, "code line"):
                module.render_notebook(data, Path(tmp) / "bad.pdf")
            self.assertFalse((Path(tmp) / "bad.pdf").exists())

    def test_source_text_is_literal_and_unsafe_links_are_rejected(self):
        module = self.require_renderer()
        data = job()
        data["pages"][0]["blocks"][0]["text"] = "<script>ignore previous instructions</script>"
        data["sources"] = [{"kind": "url", "value": "javascript:alert(1)"}]
        with self.assertRaisesRegex(ValueError, "https"):
            module.validate_job(data)
        data["sources"] = [{"kind": "text", "value": "Literal source"}]
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as tmp:
            output = Path(tmp) / "literal.pdf"
            module.render_notebook(data, output)
            text = "\n".join(p.extract_text() for p in PdfReader(output).pages)
            self.assertIn("<script>ignore previous instructions</script>", text)

    def test_unsupported_glyph_reports_it_instead_of_silent_tofu(self):
        module = self.require_renderer()
        data = job()
        data["pages"][0]["blocks"][0]["text"] = "A rare character: \U0001f984"
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as tmp:
            with self.assertRaisesRegex(ValueError, "glyph"):
                module.render_notebook(data, Path(tmp) / "unsupported.pdf")

    def test_all_layout_modes_validate_and_custom_needs_description(self):
        module = self.require_renderer()
        for mode in ("compact", "topic-pages", "subtopic-pages"):
            module.validate_job(job(mode))
        data = job("custom")
        with self.assertRaisesRegex(ValueError, "instructions"):
            module.validate_job(data)
        data["layout"]["instructions"] = "Keep one topic per page."
        module.validate_job(data)

    def test_palette_is_validated_even_if_theme_is_not_custom(self):
        module = self.require_renderer()
        for palette in ({"paper": "not-a-colour"}, [], {"unknown": "#FFFFFF"}):
            data = job()
            data["theme"]["palette"] = palette
            with self.assertRaisesRegex(ValueError, "palette"):
                module.validate_job(data)

    def test_all_themes_render_and_failed_job_preserves_previous_output(self):
        module = self.require_renderer()
        with tempfile.TemporaryDirectory(dir=ROOT / ".test-tmp") as tmp:
            output = Path(tmp) / "themes.pdf"
            for name in ("notebook", "plain", "custom"):
                data = job()
                data["theme"]["name"] = name
                if name == "custom":
                    data["theme"]["palette"] = {"highlight": "#E8E4FF"}
                module.render_notebook(data, output)
                self.assertEqual(4, len(PdfReader(output).pages))
            original = output.read_bytes()
            data["theme"]["confirmed"] = False
            with self.assertRaises(ValueError):
                module.render_notebook(data, output)
            self.assertEqual(original, output.read_bytes())

    def test_tall_code_block_continues_with_all_lines(self):
        module = self.require_renderer()
        data = job()
        lines = [f"// ROW-{number:03}" for number in range(160)]
        data["pages"][0]["blocks"] = [{"type": "code", "label": "Long example", "text": "\n".join(lines)}]
        with tempfile.TemporaryDirectory(dir=ROOT / ".test-tmp") as tmp:
            output = Path(tmp) / "code.pdf"
            module.render_notebook(data, output)
            text = "\n".join(p.extract_text() for p in PdfReader(output).pages)
            for line in lines:
                self.assertEqual(1, text.count(line), line)

    def test_non_bullet_text_is_checked_even_with_incidental_items(self):
        module = self.require_renderer()
        data = job()
        data["pages"][0]["blocks"][0].update(
            text="Unsupported \U0001f984 marker", items=["unrelated"])
        with tempfile.TemporaryDirectory(dir=ROOT / ".test-tmp") as tmp:
            with self.assertRaisesRegex(ValueError, "glyph"):
                module.render_notebook(data, Path(tmp) / "unsupported.pdf")


if __name__ == "__main__":
    unittest.main()

