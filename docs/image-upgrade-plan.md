# Approved image-first upgrade

Goal: require at least one original teaching image for every topic/subtopic when
images are approved, and require separate explicit consent for images and GIFs.

- [x] Add regression tests for permission denial/missing permission, complete topic
  coverage, unique image assets, placement, PDF embedding and stale audits.
- [x] Add a static illustration contract and reuse local drawing primitives;
  retain GIFs for approved companion HTML only. Preserve text-only legacy jobs.
- [x] Extend technical and editorial gates to images, bind exact topic mappings,
  source scenes, decoded pixels, assets and rendered outputs to reviews.
- [x] Generate and visually audit three distinct topic examples; inspect PDFs
  and rerun the ruled-line, legacy renderer and package tests.
- [x] Update instructions, schema, examples and release metadata to 1.1.0.
- [ ] Publish the verified update and use the supported installed-plugin updater
  if available; report any actual host limitation without modifying caches.

Approved by the user in this conversation. Active governance: Skill Governor;
Skill Creator for packaging and Karpathy Guidelines for focused implementation.
Media consent for future notebook creation is separate from this implementation
approval. Every future job records the user's actual choices, never demo flags.

Evidence: 37 automated tests pass; package checks pass; illustrated and GIF-only
compatibility demos pass both media gates. All six illustrated PDF pages pass
the ruled-line raster audit. An independent reviewer checked all three source
images and actual PDF-size topic pages. A continuation regression exposed and
fixed caption separation; figures now keep image, caption and alt together.

Installed refresh: the supported Codex marketplace updater was attempted and
failed on GitHub DNS resolution. Installed version remains 0.3.0 until the host
can refresh it. Do not claim the installed cache has been updated or modify it
directly. The versioned source/release can still be published through GitHub.
