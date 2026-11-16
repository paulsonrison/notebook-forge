"""Raster-based ruled-line audit. Install pdfplumber and pypdfium2 for this check."""
import argparse
import json
import re


def check_pdf(path, rule=None):
    """Reject rule-colour pixels inside text glyph bands, across every page."""
    import pdfplumber
    import pypdfium2 as pdfium
    checked = 0
    with pdfplumber.open(path) as text, pdfium.PdfDocument(str(path)) as raster:
        if rule is None:
            match = re.search(r'NotebookForgeRule=(none|#[0-9A-Fa-f]{6})', str(text.metadata.get('Keywords', '')))
            if not match:
                raise ValueError('PDF has no rule-colour metadata; supply --rule explicitly')
            rule = match.group(1)
        if rule == 'none':
            return {'pass': True, 'pages_checked': len(text.pages), 'words_checked': 0, 'reason': 'plain theme: no rules'}
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', rule):
            raise ValueError('Rule must be #RRGGBB')
        target = tuple(bytes.fromhex(rule[1:]))
        match = re.search(r'NotebookForgePaper=(#[0-9A-Fa-f]{6})', str(text.metadata.get('Keywords', '')))
        paper = tuple(bytes.fromhex(match.group(1)[1:])) if match else (255, 254, 246)
        delta = [paper[i]-target[i] for i in range(3)]
        length = sum(v*v for v in delta)
        if length < 100:
            raise ValueError('Rule colour is too close to paper for a reliable raster audit')

        def is_rule(pixel):
            # Hairline rules are antialiased: compare the full paper-to-rule
            # colour segment, not just the nominal solid stroke colour.
            amount = sum((paper[i]-pixel[i])*delta[i] for i in range(3))/length
            return .3 <= amount <= 1.05 and max(abs(pixel[i]-(paper[i]-amount*delta[i])) for i in range(3)) <= 2
        page_count = len(text.pages)
        for number, page in enumerate(text.pages):
            rendered = raster[number].render(scale=2)
            image = rendered.to_pil().convert("RGB")
            for word in page.extract_words():
                x0, y0, x1, y1 = (word[k] for k in ("x0", "top", "x1", "bottom"))
                if y0 < 65 or y1 > page.height - 54:
                    continue
                crop = image.crop((int(x0*2), int((y0+1)*2), int(x1*2), int((y1-1)*2)))
                # A real rule forms a horizontal stroke; isolated glyph-edge
                # antialias pixels can coincidentally share a pale cyan shade.
                hits = max((sum(is_rule(crop.getpixel((x, y))) for x in range(crop.width))
                            for y in range(crop.height)), default=0)
                if hits >= max(4, crop.width*.25):
                    raise ValueError(f"Rule crosses text on page {number+1}: {word['text']!r} ({hits} pixels)")
                checked += 1
            rendered.close()
    return {"pass": True, "pages_checked": page_count, "words_checked": checked}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--rule", help="Override rule colour; normally inferred from PDF metadata")
    args = parser.parse_args()
    try:
        print(json.dumps(check_pdf(args.pdf, args.rule)))
    except (ValueError, OSError, ImportError) as error:
        parser.exit(2, f"Readability check: {error}\n")


if __name__ == "__main__":
    main()
