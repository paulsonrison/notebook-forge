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
