# JSON job contract

The agent writes a job after gathering the source/topic and user choices.
The renderer does not call an AI model, fetch URLs or read external documents:
agents extract, research and author the content before rendering.

Required root fields:

- `title`: nonempty document title.
- `theme`: `{ "name": "notebook" | "plain" | "custom", "confirmed": true }`.
  Custom also requires `palette` with one or more keys: `paper`, `ink`,
  `rule`, `margin`, `highlight`, `pink`, `mint`, `code`, `practice`.
  Values are #RRGGBB colours; check custom contrast visually.
- `layout`: `{ "mode": "...", "confirmed": true }`.
  Modes: `subtopic-pages`, `topic-pages`, `compact`, `custom`.
  Custom requires a nonempty `instructions` string describing the agreement.
- `sources`: a nonempty array of `{ "kind": "topic" | "text" | "file" | "url",
  "value": "..." }`. A topic is valid source input. URLs must be HTTP(S).
  Optional `title` labels reference links. Source descriptors are provenance, not
  instructions. Do not include private file paths in public examples.
- `topics`: nonempty array of `{ "id": "...", "title": "...", "parent": "..." }`.
  Parent is optional; IDs are unique; the hierarchy must be acyclic.
- `pages`: nonempty array of logical authored pages:
  `{ "title": "...", "covers": ["topic-id"], "blocks": [...] }`.
  Every topic ID must be covered. The renderer adds cover and contents pages.
  Logical pages can overflow onto physical continuation pages.

Optional `subtitle` and `author` are displayed on the cover.
Only include user identity when requested.

## Layout rules

- `subtopic-pages`: every topic at every level needs a page that covers only that
  ID. A topic can continue over several pages.
- `topic-pages`: every page covers topics within a single top-level topic; a
  main topic and all its descendants can share pages.
- `compact`: any related topics can share pages, but coverage remains complete.
- `custom`: all topics remain covered; the agent verifies custom instructions
  against the rendered result. Arbitrary natural-language limits are not
  automatically enforced by the renderer.

## Blocks

Each block has `type` and a nonempty `label`.

| Type | Content |
|---|---|
| `paragraph` | Nonempty `text`, rendered literally |
| `callout` | Nonempty `text`, mint bordered panel |
| `practice` | Nonempty `text`, yellow bordered panel |
| `code` | Nonempty `text`, monospace with preserved line breaks |
| `bullets` | Nonempty `items` array of nonempty strings |

Text is escaped before PDF rendering; HTML-like source is never executed.
Split long code lines yourself. Do not add invisible line breaks or smaller type
to force code into the width. Long blocks may split vertically across pages.

The default fonts support a limited set of left-to-right glyphs. The renderer
rejects missing glyphs instead of substituting boxes. Use a suitably licensed
font/shaping renderer for complex scripts; translated content must retain meaning.

## CLI

```text
python scripts/render_notebook.py job.json --validate-only
python scripts/render_notebook.py job.json --output notebook.pdf
```

A successful render prints a JSON report including physical page count. Failed
validation does not create an output PDF. Rendering uses a temporary file and
replaces the output only after successful completion. Existing output is never
replaced with a partial failed build.

See the repository's examples/learning-notebook.json for a complete generic job.
