---
name: reporting
description: Generate reproducible financial reports, such as valuation memos, model audits, portfolio statements, tax summaries, and investor updates, with as-of dates, assumptions, sources, and disclaimers. Use when producing any report a person will read or rely on.
---

# Reporting

## Every report contains

1. **Header:** title, as-of date, generated-at timestamp, engine version or commit.
2. **Summary:** the answer in three to five lines, with the key numbers.
3. **Assumptions:** every input that is not a fact, with its value and source.
4. **Workings:** tables that let a reader recompute the summary.
5. **Sources:** every external number with a link and retrieval date.
6. **Limitations and disclaimer:** what the report does not cover, and that it is not advice.

## Reproducibility

- A report is generated from saved inputs plus a code version. Store both next to the output.
- Rerunning with the same inputs and version produces identical numbers.
- No numbers typed by hand into the narrative. Narrative text pulls values from the computed results.

## Formatting

- Units in every column header. Totals visibly separated.
- Same rounding throughout. Totals computed from unrounded values, with a note if displayed rows don't sum exactly.
- Plain words, sentence case headings, no filler.

## Formats

Markdown for repo artifacts, HTML or PDF for people outside the repo, CSV or XLSX when the reader will rework the numbers.
