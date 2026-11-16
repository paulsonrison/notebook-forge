# v1.0.0 validation evidence

Validated on Windows with the available Python 3.12 runtime, 2026-11-16.

- Existing renderer baseline: 16 tests passed before implementation.
- New structural rule-background test failed before the fix and passed after it.
- A stronger raster negative control caught original 0.45-point antialiased rules
  crossing text. It also found hanging bullet marks outside the original mask;
  the final mask includes the hanging indent.
- Final suite: **29 tests passed**, including existing themes, confirmations,
  topic coverage, bookmarks, contents links, long paragraphs/code, glyph checks,
  output preservation, custom rules and continuation pages.
- Animation failure controls reject duplicates, clipped labels, bad timing,
  changed/missing GIFs, changed previews, changed explanations/scripts, wrong
  HTML references, stale reviews and redirected output paths.
- `tools/check_package.py` passed: matching version identities, self-contained
  skill references, fonts, icon paths and both JSON example schemas.
- The exact example prompt is in `examples/animated-notebook-prompt.md`.
  Its original storyboards produce **three distinct GIFs**, each with three
  decoded states. TCP and binary search use 1000/1000/2200 ms; water cycle uses
  1100/1100/2400 ms. Every GIF loops and has a longer final pause.
- Independent review compared every decoded contact sheet to the actual host
  paragraphs: endpoint messages, indexed-array elimination and a triangular
  environmental cycle have distinct compositions and progressions.
- Both GIF passes succeeded. Current hashes, fingerprints, concrete editorial
  evidence and gate results ship in `examples/animated-demo/`.
- All six animated-demo PDF pages were inspected visually; raster rule audit
  passed. The original screenshot topic was regenerated as
  `examples/ruled-readability.pdf`; all three pages passed, with a before/after
  comparison image. The seven-page legacy example was regenerated too.
- Browser policy rejected a local `file:` preview. No browser workaround was
  attempted. **Live browser playback was not observed.** All encoded GIF frames,
  progression, duration and loop metadata were decoded and inspected instead.
- Release ZIP built from the existing explicit allowlist, including changelog,
  audit evidence, examples and the self-contained updated skill.

## Implementation decisions

- Keep PDF static; use inline GIFs in companion HTML and final-state PDF stills.
  A PDF-only delivery cannot provide motion, so ship HTML and adjacent assets.
- Mask decorative rules beneath text rather than changing line spacing. This
  preserves existing pagination, typography and layout workflows.
- Bind reviews to normalized source hashes for every renderer/pipeline script
  and to actual PDF/asset hashes. Text newline normalization avoids invalidation
  merely from Windows versus Linux checkout line endings.
- Keep semantic review explicit: software records evidence but cannot prove
  teaching accuracy or truthful human/agent inspection.
- Local Git metadata is read-only and shell DNS is unavailable in this session.
  Publication uses the connected GitHub integration. The release workflow runs
  tests and gates before creating a new version tag and release on main.

## File groups changed

| Files | Purpose |
|---|---|
| Plugin manifests, marketplace metadata, `agents/openai.yaml`, icons | v1.0.0 identity and notebook/play branding |
| `SKILL.md`, contracts, schema and visual guide | Topic-specific animation policy, double gates and ruled-page rules |
| `animations.py`, bundle/verification CLIs | Local drawing, manifests, HTML/PDF assets, hash-bound audit |
| `render_notebook.py`, `check_readability.py` | Opaque text masks, hanging bullets, PDF rule metadata and raster audit |
| Tests and CI workflows | Regression/failure controls and verified release publishing |
| Examples and demo authoring tool | Three-topic example, actual GIFs, reviews and readable PDF evidence |
| README, changelog, release notes, build/check tools | Setup, compatibility, package validation and publication instructions |
