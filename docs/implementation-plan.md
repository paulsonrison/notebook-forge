# Notebook Forge Implementation Plan

> Execute directly using Superpowers executing-plans, writing-skills,
> test-driven-development and verification-before-completion.

**Goal:** Publish the approved notebook skill and plugin as a new GitHub repository.
**Architecture:** One self-contained Agent Skill with a validated JSON-to-PDF
renderer, wrapped by portable/Codex/Claude plugin metadata.
**Tech stack:** Python 3.10+, ReportLab, pypdf, Pillow for previews; unittest;
JSON manifests; Markdown instructions; GitHub Actions.
**Spec:** [design.md](design.md).

## Global constraints

- Always request theme confirmation for a new notebook.
- Ask for missing source/topic and provide multiple-choice layout options.
- Every requested topic is represented; dedicated-page mode covers all levels.
- No private interview content, reference screenshot or Windows fonts in public.
- No unrelated portfolio changes, automatic global installs or paid services.

## Review focus

Unconfirmed options; nested topic omissions; long text/code clipping; unsupported
glyphs; path/manifest portability. Add checks for each below.

## Tasks

### 1. Establish behaviour and package contract
- [x] Run baseline requests without the new skill.
- [ ] Record observed missing confirmation/layout behaviour.
- [ ] Write skill with concise intake and source-handling rules.
- [ ] Run fresh agents against realistic requests and inspect their next actions.

### 2. Test and implement the local renderer
- [ ] Write failing tests for missing renderer, confirmations, absent sources,
  hierarchy coverage, grouped layouts, long content, Unicode and safe links.
- [ ] Implement schema validation, typography, layout, page continuation,
  bookmarks, contents and CLI.
- [ ] Run the full suite on Windows; CI covers Linux and Windows.
- [ ] Render a generic sample and inspect all pages.

### 3. Package and document
- [ ] Add portable, Codex and Claude manifests and local marketplace catalogs.
- [ ] Add install instructions, job example, font attribution and license.
- [ ] Validate frontmatter and all metadata; create a portable ZIP.
- [ ] Run an independent final review and fix substantive findings.

### 4. Publish and verify
- [ ] Copy the reviewed package into its own local repository directory.
- [ ] Create an initial commit containing only package files.
- [ ] Create public repository paulsonrison/notebook-forge and push.
- [ ] Publish v0.1.0 release with ZIP and sample PDF.
- [ ] Verify repository visibility, commit, release assets and CI outcome.
