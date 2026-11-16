# v1.1.0 image-first validation

The implementation was tested on Windows with Python 3.12. Tests first exposed
missing media permission enforcement, missing image coverage, missing image
manifests, retained obsolete assets, and image captions separating across pages.
Each case was implemented or corrected and rerun.

- Final suite: **37 tests**, including all prior renderer and GIF regression
  tests plus static-image tests for permission, exact nested-topic coverage,
  unique scenes, wrong topic metadata, real PDF embedding, unchanged outputs
  after refused permission, both media types and continuation-page figure groups.
- Image-only example: three original locally drawn PNG diagrams, three topics,
  zero GIFs, six PDF pages and an HTML companion. The PDF contains one image on
  each matching topic page, rather than substituted animation frames.
- Topic audit: inspected source PNGs and PDF pages 3-5 at actual page scale.
  TCP uses directed lifelines/messages; binary search uses an annotated sorted
  array; water cycle uses a labelled cycle. All match their host explanations.
- Visual correction: condensation and precipitation labels originally crossed
  arrows in the first water-cycle draft. They were repositioned, regenerated
  and rechecked before approval.
- Pagination correction: a negative control with longer text separated an
  image from its caption. Figures now keep image/caption/alt together, and
  excessive captions fail with an instruction to shorten them.
- GIF-only compatibility example: explicit GIF approval and image refusal;
  animations remain in HTML, with no GIF stills smuggled into PDF.
- Both media verification passes and the ruled-text raster audits are required
  by the release workflow. Semantic approval is recorded only after inspection;
  hashes alone do not prove topic alignment or truthful review.

The supported installed-plugin updater was attempted during this session but
failed resolving github.com in the execution environment. The source update
and verified release are separate from refreshing the installed plugin cache.
No cache files or host security settings were edited.

To refresh from an ordinary terminal with GitHub connectivity:

```powershell
codex plugin marketplace upgrade notebook-forge
codex plugin add notebook-forge@notebook-forge
```

If Codex is not on PATH, use its installed executable or the app's supported
plugin updater. Verify that the installed version is 1.1.0 afterward.

| Assigned skill | Result | Evidence |
|---|---|---|
| Skill Governor | PASS | Requested selection retained, plan approved before edits, evidence audit |
| Skill Creator | PASS for source update | Self-contained skill, schema/package checks, real examples and independent visual audit; installed refresh separately blocked |
| Karpathy Guidelines | PASS | Existing drawing/verification reused; focused changes; failing regression cases corrected |
