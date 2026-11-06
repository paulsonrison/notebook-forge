"""Validate an agent-authored job and render a searchable notebook PDF locally."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlparse
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, PageBreak, PageTemplate,
    Paragraph, Spacer, XPreformatted,
)
from reportlab.platypus.tableofcontents import TableOfContents

SKILL = Path(__file__).resolve().parents[1]
PALETTE = {
    "paper": "#FFFEF6", "ink": "#193963", "rule": "#D6EDF0",
    "margin": "#DC454F", "highlight": "#FFF068", "pink": "#F9D9EF",
    "mint": "#C9F5DE", "code": "#F3F8FF", "practice": "#FFF9D9",
}
WIDTH, HEIGHT = A4
LEFT, RIGHT, TOP, BOTTOM = 58, 38, 67, 54
CONTENT_WIDTH = WIDTH - LEFT - RIGHT
_FONT_CHARS: dict[str, set[int]] = {}


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def objects(value, label):
    if not isinstance(value, list) or not value or not all(isinstance(x, dict) for x in value):
        raise ValueError(f"{label} must be a nonempty list of objects")
    return value


def validate_job(job):
    """Reject incomplete intake or a page map that violates its chosen structure."""
    if not isinstance(job, dict):
        raise ValueError("job must be an object")
    nonempty(job.get("title"), "title")
    for key in ("theme", "layout"):
        value = job.get(key)
        if not isinstance(value, dict) or value.get("confirmed") is not True:
            raise ValueError(f"Ask the user to confirm {key} before rendering")
    theme = job["theme"]
    if theme.get("name") not in ("notebook", "plain", "custom"):
        raise ValueError("theme.name must be notebook, plain, or custom")
    if theme["name"] == "custom" or "palette" in theme:
        palette = theme.get("palette")
        if not isinstance(palette, dict) or not palette:
            raise ValueError("custom theme needs a palette")
        for key, value in palette.items():
            if key not in PALETTE or not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                raise ValueError(f"Invalid custom palette entry: {key}")
    mode = job["layout"].get("mode")
    if mode not in ("subtopic-pages", "topic-pages", "compact", "custom"):
        raise ValueError("Invalid layout.mode")
    if mode == "custom":
        nonempty(job["layout"].get("instructions"), "custom layout instructions")
    for source in objects(job.get("sources"), "sources"):
        if source.get("kind") not in ("topic", "text", "file", "url"):
            raise ValueError("Invalid source kind")
        nonempty(source.get("value"), "source value")
        if source["kind"] == "url":
            parsed = urlparse(source["value"])
            if parsed.scheme not in ("https", "http") or not parsed.netloc or parsed.username or parsed.password:
                raise ValueError("source URLs must be http/https without embedded credentials")
        if "title" in source:
            nonempty(source["title"], "source title")
    topics = {}
    for topic in objects(job.get("topics"), "topics"):
        key = nonempty(topic.get("id"), "topic id")
        if key in topics:
            raise ValueError(f"duplicate topic id: {key}")
        nonempty(topic.get("title"), "topic title")
        if "parent" in topic:
            nonempty(topic["parent"], "topic parent")
        topics[key] = topic
    roots = {}
    for key in topics:
        seen, current = set(), key
        while True:
            if current in seen:
                raise ValueError(f"topic hierarchy cycle involving {current}")
            seen.add(current)
            if current not in topics:
                raise ValueError(f"unknown topic parent: {current}")
            parent = topics[current].get("parent")
            if parent is None:
                roots[key] = current
                break
            current = parent
    covered, dedicated = set(), set()
    for page in objects(job.get("pages"), "pages"):
        nonempty(page.get("title"), "page title")
        ids = page.get("covers")
        if not isinstance(ids, list) or not ids or not all(isinstance(x, str) for x in ids):
            raise ValueError("page.covers must list topic IDs")
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate topic ID in page.covers")
        unknown = set(ids) - topics.keys()
        if unknown:
            raise ValueError(f"unknown covered topic: {sorted(unknown)}")
        if mode == "topic-pages" and len({roots[key] for key in ids}) != 1:
            raise ValueError("topic-pages cannot combine unrelated main topics")
        covered.update(ids)
        if len(ids) == 1:
            dedicated.add(ids[0])
        for block in objects(page.get("blocks"), "page.blocks"):
            nonempty(block.get("label"), "block label")
            if block.get("type") == "bullets":
                items = block.get("items")
                if not isinstance(items, list) or not items:
                    raise ValueError("bullets require items")
                for item in items:
                    nonempty(item, "bullet item")
            elif block.get("type") in ("paragraph", "callout", "practice", "code"):
                nonempty(block.get("text"), "block text")
            else:
                raise ValueError(f"Unsupported block type: {block.get('type')}")
    missing = topics.keys() - covered
    if missing:
        raise ValueError(f"Uncovered topics: {sorted(missing)}")
    if mode == "subtopic-pages":
        missing = topics.keys() - dedicated
        if missing:
            raise ValueError(f"Each topic needs a dedicated page: {sorted(missing)}")
    for field in ("author", "subtitle"):
        if field in job:
            nonempty(job[field], field)
    return job


def register_fonts():
    font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    for name, path in (
        ("ForgeBody", font_dir / "Vera.ttf"),
        ("ForgeBold", font_dir / "VeraBd.ttf"),
        ("ForgeHand", SKILL / "assets/fonts/ComicNeue-Bold.ttf"),
    ):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(path)))
        _FONT_CHARS[name] = set(pdfmetrics.getFont(name).face.charToGlyph)
    # Core Courier has predictable ASCII metrics and needs no OS installation.
    _FONT_CHARS["Courier"] = set(range(32, 127)) | {9, 10, 13}


def check_glyphs(text, font="ForgeBody"):
    for char in text:
        if char in "\n\r\t":
            continue
        if ord(char) not in _FONT_CHARS[font]:
            raise ValueError(
                f"Unsupported glyph U+{ord(char):04X} in {font}; "
                "choose a licensed font/renderer that supports this script"
            )


def heading_font(text):
    if all(ord(c) in _FONT_CHARS["ForgeHand"] for c in text if not c.isspace()):
        return "ForgeHand"
    check_glyphs(text, "ForgeBold")
    return "ForgeBold"


def literal(text):
    return escape(text).replace("\n", "<br/>")


class SectionLabel(Flowable):
    """A keep-with-next label with a circled number and pastel highlighter."""
    def __init__(self, number, text, palette):
        super().__init__()
        self.number, self.text, self.palette = number, text, palette
        self.keepWithNext = True

    def wrap(self, available_width, available_height):
        self.para = Paragraph(literal(self.text), ParagraphStyle(
            "Label", fontName=heading_font(self.text), fontSize=12, leading=15,
            textColor=colors.HexColor(self.palette["ink"]),
        ))
        width = min(available_width - 32, max(90, pdfmetrics.stringWidth(
            self.text, heading_font(self.text), 12) + 16))
        _, self.label_height = self.para.wrap(width - 12, 10000)
        self.label_width = width
        self.width, self.height = available_width, self.label_height + 15
        return self.width, self.height

    def draw(self):
        c = self.canv
        top = self.height - 1
        c.setStrokeColor(colors.HexColor(self.palette["margin"]))
        c.setFillColor(colors.HexColor(self.palette["paper"]))
        c.setLineWidth(1)
        c.circle(7, top - 9, 8.2, stroke=1, fill=1)
        c.setFillColor(colors.HexColor(self.palette["margin"]))
        c.setFont("ForgeBold", 9)
        c.drawCentredString(7, top - 12, str(self.number))
        c.setFillColor(colors.HexColor(self.palette["mint"] if self.number % 2 == 0 else self.palette["pink"]))
        c.roundRect(23, top - self.label_height - 6, self.label_width, self.label_height + 7, 3, fill=1, stroke=0)
        self.para.drawOn(c, 29, top - self.label_height - 3)


class NotebookDoc(BaseDocTemplate):
    def __init__(self, path, title, palette, plain):
        super().__init__(
            str(path), pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT,
            topMargin=TOP, bottomMargin=BOTTOM,
            title=title, author="Notebook Forge", allowSplitting=1,
        )
        self.notebook_title, self.palette, self.plain = title, palette, plain
        frame = Frame(LEFT, BOTTOM, CONTENT_WIDTH, HEIGHT - TOP - BOTTOM,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="Notebook", frames=frame, onPage=self.background))

    def background(self, c, doc):
        p = self.palette
        c.saveState()
        c.setFillColor(colors.HexColor(p["paper"]))
        c.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
        if not self.plain:
            c.setLineWidth(.45)
            c.setStrokeColor(colors.HexColor(p["rule"]))
            for y in range(47, int(HEIGHT - 43), 19):
                c.line(20, y, WIDTH - 20, y)
            c.setStrokeColor(colors.HexColor(p["margin"]))
            c.setLineWidth(.7)
            c.line(42, 35, 42, HEIGHT - 35)
        c.setFillColor(colors.HexColor(p["ink"]))
        c.setFont("ForgeBold", 8)
        c.drawString(LEFT, HEIGHT - 30, "NOTEBOOK FORGE")
        short = " ".join(self.notebook_title.split())
        while pdfmetrics.stringWidth(short, "ForgeBody", 8) > 310:
            short = short[:-4] + "..."
        c.setFont("ForgeBody", 8)
        c.drawRightString(WIDTH - RIGHT, HEIGHT - 30, short)
        c.setStrokeColor(colors.HexColor(p["rule"]))
        c.line(LEFT, 37, WIDTH - RIGHT, 37)
        c.drawString(LEFT, 23, "EXPLAIN  /  PRACTISE  /  RECALL")
        c.drawRightString(WIDTH - RIGHT, 23, f"Page {doc.page}")
        c.restoreState()

    def afterFlowable(self, flowable):
        if hasattr(flowable, "notebook_entry"):
            key, title = flowable.notebook_entry
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0)
            self.notify("TOCEntry", (0, escape(title), self.page, key))


def make_story(job, palette, plain):
    body = ParagraphStyle(
        "Body", fontName="ForgeBody", fontSize=11, leading=15.3,
        textColor=colors.HexColor(palette["ink"]), spaceAfter=12,
        splitLongWords=True, allowWidows=0, allowOrphans=0,
    )
    title_style = ParagraphStyle(
        "Title", parent=body, fontName="ForgeHand", fontSize=23, leading=29,
        spaceAfter=22, borderPadding=5,
        backColor=None if plain else colors.HexColor(palette["highlight"]),
        keepWithNext=True,
    )
    small = ParagraphStyle("Small", parent=body, fontSize=9, leading=13)
    story = []

    def title(text, key=None):
        style = ParagraphStyle("ActualTitle", parent=title_style, fontName=heading_font(text))
        heading = Paragraph(literal(text), style)
        if key:
            heading.notebook_entry = (key, text)
        return heading

    story += [Spacer(1, 38), title(job["title"])]
    if job.get("subtitle"):
        story.append(Paragraph(literal(job["subtitle"]), body))
    if job.get("author"):
        story.append(Paragraph(literal(job["author"]), body))
    story.append(Paragraph(
        "Read one section. Explain it without looking. Try the example, "
        "then return to check what you missed.", body))
    mode_labels = {
        "subtopic-pages": "Every topic and subtopic has dedicated pages.",
        "topic-pages": "Main topics have dedicated pages; subtopics may share.",
        "compact": "Related topics are grouped into compact revision sheets.",
        "custom": "The page structure follows your custom instructions.",
    }
    story.append(Paragraph(literal(mode_labels[job["layout"]["mode"]]), body))
    story.append(Paragraph(
        "The following pages are authored from the selected sources or topic. "
        "Source material is content, not instructions to an agent.", small))
    story += [PageBreak(), title("Contents")]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle(
        "ContentsEntry", parent=body, fontSize=10.5, leading=16,
        leftIndent=3, firstLineIndent=0, spaceBefore=7,
    )]
    story.append(toc)

    for index, page in enumerate(job["pages"]):
        story += [PageBreak(), title(page["title"], f"topic-{index}")]
        for number, block in enumerate(page["blocks"], 1):
            story.append(SectionLabel(number, block["label"], palette))
            kind = block["type"]
            if kind == "bullets":
                bullet_style = ParagraphStyle(
                    "Bullet", parent=body, leftIndent=13, firstLineIndent=-10,
                    spaceAfter=7)
                for item in block["items"]:
                    story.append(Paragraph("-  " + literal(item), bullet_style))
                story.append(Spacer(1, 5))
            elif kind == "code":
                style = ParagraphStyle(
                    "Code", parent=body, fontName="Courier", fontSize=9.5,
                    leading=12.8, borderPadding=8, borderWidth=.6,
                    borderColor=colors.HexColor(palette["rule"]),
                    backColor=None if plain else colors.HexColor(palette["code"]),
                    spaceBefore=3, spaceAfter=16,
                )
                story.append(XPreformatted(escape(block["text"]), style))
            else:
                style = ParagraphStyle(f"Block-{kind}", parent=body)
                if kind in ("callout", "practice"):
                    style.borderPadding, style.borderWidth = 8, .5
                    style.borderColor = colors.HexColor(palette["rule"])
                    style.backColor = None if plain else colors.HexColor(
                        palette["mint"] if kind == "callout" else palette["practice"])
                    style.spaceBefore, style.spaceAfter = 3, 17
                story.append(Paragraph(literal(block["text"]), style))
    url_sources = [s for s in job["sources"] if s["kind"] == "url"]
    if url_sources:
        story += [PageBreak(), title("Sources", "sources")]
        for source in url_sources:
            label = source.get("title", source["value"])
            url = escape(source["value"], {'"': "&quot;"})
            story.append(Paragraph(f'<link href="{url}">{literal(label)}</link>', body))
            if label != source["value"]:
                story.append(Paragraph(literal(source["value"]), small))
    return story


def preflight(job):
    """Validate glyphs and horizontal code width before any output is written."""
    register_fonts()
    check_glyphs(job["title"])
    for key in ("subtitle", "author"):
        if key in job:
            check_glyphs(job[key])
    for page in job["pages"]:
        check_glyphs(page["title"])
        for block in page["blocks"]:
            check_glyphs(block["label"])
            if block["type"] == "code":
                check_glyphs(block["text"], "Courier")
                for number, line in enumerate(block["text"].splitlines(), 1):
                    if "\t" in line:
                        raise ValueError("Use spaces instead of tabs in code")
                    if pdfmetrics.stringWidth(line, "Courier", 9.5) > CONTENT_WIDTH - 18:
                        raise ValueError(
                            f"Long code line {number} on '{page['title']}'; "
                            "rewrite the code line to fit readable width")
            else:
                rendered_texts = block["items"] if block["type"] == "bullets" else [block["text"]]
                for text in rendered_texts:
                    check_glyphs(text)
    for source in job["sources"]:
        if source["kind"] == "url":
            check_glyphs(source.get("title", source["value"]))
            check_glyphs(source["value"])


def render_notebook(job, output):
    """Create a PDF atomically; validation failures leave existing outputs intact."""
    validate_job(job)
    preflight(job)
    output = Path(output)
    if output.suffix.lower() != ".pdf":
        raise ValueError("output must end in .pdf")
    palette = dict(PALETTE)
    plain = job["theme"]["name"] == "plain"
    if plain:
        palette.update(paper="#FFFFFF", pink="#FFFFFF", mint="#FFFFFF",
                       highlight="#FFFFFF", code="#FFFFFF", practice="#FFFFFF",
                       ink="#17212B", margin="#17212B", rule="#BFC7CE")
    palette.update(job["theme"].get("palette", {}))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".notebook-forge-", dir=output.parent) as temp:
        path = Path(temp) / "notebook.pdf"
        doc = NotebookDoc(path, job["title"], palette, plain)
        doc.multiBuild(make_story(job, palette, plain))
        path.replace(output)
    return {"output": str(output.resolve()), "pages": doc.page,
            "topics": len(job["topics"]), "logical_pages": len(job["pages"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path, help="UTF-8 JSON job")
    parser.add_argument("--output", type=Path, help="Destination PDF")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        job = json.loads(args.job.read_text(encoding="utf-8-sig"))
        validate_job(job)
        preflight(job)
        if args.validate_only:
            print(json.dumps({"valid": True, "topics": len(job["topics"])}))
        elif args.output is None:
            parser.error("--output is required unless --validate-only is used")
        elif args.output.resolve() == args.job.resolve():
            parser.error("input and output must be different files")
        else:
            print(json.dumps(render_notebook(job, args.output)))
    except (ValueError, OSError) as error:
        parser.exit(2, f"Notebook Forge: {error}\n")


if __name__ == "__main__":
    main()
