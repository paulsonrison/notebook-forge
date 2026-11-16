# Original animations and verification

## Authoring contract

Attach `animation` only to a `paragraph` block containing the exact core
explanation. A block is a section: its page title and block label together locate
the target. Several explained concepts on one page use separate blocks.

Required fields:

| Field | Meaning |
|---|---|
| `id` | Unique lowercase hyphenated filename slug |
| `concept` | Exact visual concept, unique per notebook |
| `layout` | Description of the original composition, unique per notebook |
| `pattern` | Description of the changing progression, unique per notebook |
| `motion_reason` | Why motion helps this particular explanation |
| `alt`, `caption` | Descriptive alternative text and informative caption |
| `storyboard` | Original title and 2–30 keyframes |

Each frame has `label`, `duration_ms` and `objects`. Keyframes last 500–1200 ms
(multiples of 10); the final state pauses 1500–3000 ms and at least 500 ms longer
than the preceding frame. The canvas is 960×540. Keep objects within x=12–948,
y=140–528; the renderer reserves the upper band for title and step label.

Draw with these local primitives (no URLs or imported images):

| `type` | Fields |
|---|---|
| `text` | `xy: [x,y]`, `text`, optional `size` (24–48), `fill`, `background` |
| `rect`, `ellipse` | `box: [x0,y0,x1,y1]`, optional `fill` |
| `line`, `arrow` | `xy: [x0,y0,x1,y1]`, optional `fill` |

Colours use #RRGGBB. Text defaults to dark navy on ivory. Declare the actual
background when placing text on a coloured shape; text contrast must be at
least 4.5:1. The audit must catch inaccurate declarations and shape/text overlap.
Use concise labels and deliberate whitespace. Full typography uses the bundled
ReportLab Vera font. Unsupported glyphs fail rather than silently become boxes.

See the repository's `examples/animated-notebook.json` for a complete job with
three original compositions. It demonstrates TCP, binary search and the water
cycle. Author a fresh storyboard for other concepts using these primitives.

## Build and technical gate

```text
python -m pip install -r requirements.txt
python scripts/render_animated_notes.py job.json --output-dir notes
python scripts/verify_gifs.py notes --technical-only
```

Use a fresh directory per notebook. Existing outputs are preserved until all
staged files pass the technical gate. The build copies approved technical draft
files; final editorial approval is separate. A rebuilt draft removes any old
`verification.json`. Do not copy a demo's review or fabricate a pass.

The bundle contains `job.json`, `notebook.html`, `notebook.pdf`, `manifest.json`
and `assets/gifs/` containing GIFs, final-frame PNGs and decoded-frame contact
sheets. Exact HTML is checked against source block order: the figure is the next
element after the explanation. All references are relative and stay inside the
bundle. A reduced-motion preference shows the still instead of autoplay.

The manifest binds the job, generator, storyboard, actual GIF bytes, decoded
frames, geometry and preview assets. Repeated concepts, IDs, layouts and patterns
fail validation. Duplicate bytes, decoded visuals and storyboard geometry fail
Pass 1. These checks catch exact repetitions; renamed or transformed conceptual
repetition still requires the Pass 2 review.

## Editorial gate

Open each decoded contact sheet and compare it to the host explanation and
storyboard. Observe playback in an available GIF viewer. If viewer access is
blocked, state that explicitly and inspect all decoded states, timing and loop
metadata; do not claim browser playback was observed. Review every label, contrast,
state transition, caption and alt text. Confirm movement teaches the exact host
topic, without borrowing an adjacent explanation.

Read `review_fingerprints` from the technical command. Create `notes/review.json`:

```json
{
  "reviewer": "Name or agent identifier",
  "gifs": [{
    "section": "page-0-block-0",
    "fingerprint": "COPY THE CURRENT TECHNICAL FINGERPRINT",
    "approved": true,
    "alignment": "Specific evidence linking the explanation and visual states.",
    "readability": "Specific observations about labels, pacing and progression.",
    "playback": "Observed transitions and final pause, or exact viewer limitation and decoded-frame evidence."
  }]
}
```

Include every animation in manifest order, then run:

```text
python scripts/verify_gifs.py notes
python -m pip install pdfplumber pypdfium2
python scripts/check_readability.py notes/notebook.pdf
```

The final GIF command rejects missing, stale or incomplete reviews and writes
`verification.json` only on success. This records an audit; it cannot prove a
reviewer was truthful or that educational content is correct. An agent must
actually perform the audit. Rebuild and re-review after changes. PDF QA covers
all pages separately; passing the GIF gate does not replace PDF inspection.

Deliver the HTML with adjacent assets and PDF, retaining the manifest and audit
evidence. PDF stills never animate. Existing jobs without `animation` keep using
`render_notebook.py job.json --output notebook.pdf` unchanged.
