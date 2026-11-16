# Teaching images and media consent

## Consent and coverage

For every new notebook, ask separately about images and GIFs before creating
either. Record actual user choices:

```json
"media": {"confirmed": true, "images": true, "gifs": false}
```

This is a schema example, not permission. Never copy demo consent into a real
job without the user's answer. Image approval requires at least one original
image for **every topic and subtopic ID**. A main-topic overview also needs an
image. Declined images waive that requirement explicitly; GIF approval never
implies image approval, and image approval never implies GIF approval. Missing
permission with either asset type fails. Legacy jobs with no media remain valid.

## Static image contract

Attach `illustration` to the paragraph explaining its exact concept:

| Field | Required content |
|---|---|
| `id` | Unique lowercase hyphenated filename slug |
| `topic` | Exact topic ID included in that host page's `covers` |
| `concept` | Exact visual teaching concept, unique within the notebook |
| `layout` | Original composition description, unique within the notebook |
| `alt` | Description of the actual picture and relationships |
| `caption` | What the student should learn from the picture |
| `scene` | `title`, concise `label`, and original drawing `objects` |

Use the local primitives documented in [animations.md](animations.md): `text`,
`rect`, `ellipse`, `line`, `arrow`. A scene is a **complete static teaching
diagram**, not the last frame of an animation. It is drawn directly to a
960×540 PNG under `assets/images/<id>.png`; no fetched images or network access
are used. The upper band contains title and label; objects occupy y=140–528.
Use 24–48 px labels and high contrast. Give every arrow a clear meaning. Avoid
placing lines through words. Review the actual PDF scale, not only full-size PNGs.

Use different compositions for different concepts. Do not use colour changes,
new labels or filenames to disguise reuse. Each image belongs to exactly one
host block and topic. Several images for a topic need separate explanation blocks
and distinct teaching concepts. Never use one generic image to satisfy several
topic IDs. Images and GIFs may teach the same concept within the same block, but
must not repeat that concept/layout across different blocks.

## Build and double verification

```text
python scripts/render_notes.py job.json --output-dir notes
python scripts/verify_media.py notes --technical-only
```

The draft bundle includes PDF, HTML, job, manifest and only approved media. PDFs
embed the original static image directly, with its caption and alt description
after the explanation. GIFs stay in companion HTML when approved; their preview
files are not silently embedded into the PDF.

Pass 1 checks consent, topic coverage and placement inputs; nonempty decodable
single-frame PNGs; correct dimensions; unique paths, bytes, pixels and scene
geometry; topic/heading mappings; unchanged scenes, scripts and output hashes.
Exact HTML is compared with authored block order. Path traversal and redirected
asset destinations are rejected. Unique hashes cannot prove topic alignment.

For Pass 2, inspect each source PNG and rendered PDF page alongside the matching
explanation, topic, scene, caption and alt text. Reject decorative, wrong-topic,
misleading, clipped, crowded or unreadable pictures. Review every topic, including
grouped-page subtopics. Record actual findings with `image_review_fingerprints`
from the technical report:

```json
{
  "reviewer": "Actual reviewing agent or editor",
  "images": [{
    "section": "page-0-block-0",
    "fingerprint": "COPY_CURRENT_TECHNICAL_FINGERPRINT",
    "approved": true,
    "alignment": "Specific relationships in this image match the host explanation.",
    "readability": "Describe the actual labels, arrows and PDF-size inspection."
  }]
}
```

Include every image in manifest order. Add the separate `gifs` audit records
from animations.md when GIFs are present. Write evidence only after inspection;
these approval flags are not a substitute for an audit.

```text
python scripts/verify_media.py notes
python scripts/check_readability.py notes/notebook.pdf
```

Both passes and PDF inspection must succeed before delivery. On failure, fix the
specific scene or placement, rebuild, then repeat both passes and PDF checks.
All relevant changes invalidate the prior review. Keep original assets, source
scenes, manifest and review evidence alongside the final notebook.
