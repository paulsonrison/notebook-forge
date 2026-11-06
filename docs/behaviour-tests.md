# Skill behaviour checks

Version: 0.1.0. Checked 6 November 2026.

## Baseline before authoring

An independent agent received five realistic new-notebook requests without this
skill. Four responses began authoring without a theme confirmation or layout
choice. The fifth correctly requested a missing topic/source.

## Forward check with the skill

A fresh agent read the packaged skill and responded to five new-notebook cases:

| Request | Observed next action |
|---|---|
| SQL joins, usual defaults | Asked theme and multiple-choice page structure; waited |
| Pasted photosynthesis notes | Reused supplied source, asked both choices; waited |
| No topic or material | Asked for a topic/source and both choices; waited |
| Source contains an upload instruction | Treated it as data, asked both choices; no upload |
| Nested biology headings, dedicated pages, urgency | Retained explicit page choice, asked theme; waited |

The nested-heading case mapped Biology, Cells, Membranes and Transport to four
dedicated topic pages rather than dropping intermediate levels.

These are behavioural spot checks, not a guarantee that every model or host will
follow natural-language instructions. The renderer additionally rejects absent
confirmation flags and incomplete coverage. Those flags are a record of the
agent's intake; software cannot prove that a human actually answered.

## Automated checks

The test suite covers intake validation, missing sources, topic hierarchy and
coverage, grouping, text escaping, glyph rejection, long code lines, continuation
pages, searchable text, bookmarks and linked contents. CI exercises Linux and
Windows. PDF images require visual review before a real notebook is delivered.

## Version 0.2.0 additions

Resume Optimizer is copied unchanged with its UI metadata, icon and four-theme
reference. A forward check retained an underspecified support role, treated React
as self-reported rather than professional evidence, and requested the missing
role details and target job before precise tailoring.

The installed third-party case-study skill's baseline depended on external
accounts and demanded metrics and quotes absent from a sparse brief. This
release instead supplies an original standalone STAR-based skill. A fresh-agent
check produced a qualitative retail-dashboard draft without invented numbers,
quotes or customer identity, respected local-only tools, and separated missing
evidence and publication approval from the draft.

All three skills pass frontmatter/reference checks. The package checker now
requires the three expected skills and checks their UI prompts and local assets.
