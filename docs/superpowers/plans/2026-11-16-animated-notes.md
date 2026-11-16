# Animated notes and ruled-page readability implementation plan

> Execute the approved design in this session using Superpowers execution, debugging, TDD and verification guidance.

**Goal:** Release Notebook Forge 1.0.0 with original, section-specific GIFs, two verification gates and readable ruled pages.

**Architecture:** Preserve the existing JSON-to-PDF interface. Add optional animation metadata to explanation blocks and a local animation pipeline producing GIF assets, a manifest, companion HTML and PDF stills. Keep semantic review explicit and bound to content hashes; automated checks do not prove educational accuracy.

**Tech stack:** Python 3.10+, ReportLab, Pillow, existing unittest and JSON schema tooling.

**Spec:** User-approved design in this conversation, including the supplied ruled-line overlap screenshot.

## Global constraints

- Preserve existing jobs, all themes, layout choices, source handling, bookmarks and pagination.
- Generate animations locally; never download or hotlink GIFs.
- One concept, target section, layout and progression per animation per notebook.
- Place animation immediately after its host explanation, with caption and alt text.
- Use 500–1200 ms keyframes and a longer final pause; inspect actual decoded frames.
- PDF is static; playable GIFs live in companion HTML and adjacent assets.
- Publish only after tests and documented visual review; publication already authorized.

## Review focus

- Long paragraphs and code split across pages must retain their text and rule clearance.
- Missing, changed, duplicate and path-escaping assets must fail closed.
- Identical visuals encoded differently must not evade uniqueness checks.
- Review approvals must become stale after source, script, metadata or GIF changes.
- Existing jobs with no animation metadata must still render through the same CLI.

## Task 1: Ruled-page regression

- [ ] Add a PDF geometry regression covering multi-line paragraphs, bullets, labels and continuation pages; observe existing failure.
- [ ] Mask rules behind text-bearing flowables without changing text layout or pagination; verify drawn geometry and rendered pixels.
- [ ] Run existing renderer tests, add a reproducible network-device fixture and record visual evidence.

## Task 2: Animation pipeline

Files: `scripts/animations.py`, `scripts/render_animated_notes.py`, `scripts/verify_gifs.py`, `references/animations.md`, `tests/test_animations.py` under the skill or repository as appropriate.

Interfaces: optional `animation` on an explanation block describes concept, unique layout/pattern, caption, alt and a local storyboard. `build_notes(job, output_dir)` generates the bundle; `verify_bundle(job, root, require_review=True)` enforces both gates. Review binds to the complete job, storyboard, decoded visual digest and GIF bytes.

- [ ] Write failing tests for generated frames, uniqueness, placement, timing, unsafe paths, missing assets, stale review and backwards compatibility.
- [ ] Implement locally drawn storyboard primitives and GIF generation with a manifest.
- [ ] Implement technical gate plus evidence-backed editorial gate and contact-sheet review.
- [ ] Render companion HTML from the same block order and PDF stills after explanations; verify three distinct topics and retry any failed generation.

## Task 3: Skill, icon and release

- [ ] Update SKILL.md, contracts, schema, README, changelog, manifests and release checks to 1.0.0; keep the runtime self-contained.
- [ ] Add an aligned notebook/play icon to plugin and skill metadata.
- [ ] Run the full suite, package checks and release build; independently review skill usage and branch changes.
- [ ] Commit, tag and publish using available authorized capabilities; report any actual permission/connectivity limitation with exact ready-to-run commands.

## Evidence ledger

- Initial tree clean; version 0.3.0 in plugin manifests and skill. No local tags returned.
- Root cause: page rules repeat every 19 pt; body leading is 15.3 pt and block spacing varies. Fixed rules therefore intersect glyphs.
- Environment: normal `python` is an inaccessible Windows alias; bundled Python located under the Codex runtime cache.
- Git mutation is denied in this checkout; native worktree creation also failed. Continue authorized source edits here and attempt supported publication after verification. No history rewriting.
- Shell network DNS cannot resolve GitHub. Check alternate connected capability before declaring publication unavailable.
