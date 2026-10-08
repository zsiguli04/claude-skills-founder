---
description: Value a company with DCF plus comparables and save the workings.
argument-hint: "[company or ticker, as-of date, and any inputs you already have]"
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, WebSearch, WebFetch, Agent
---

Value this company: $ARGUMENTS

Use the `financial-analyst` agent and the `valuation-engine` and `reporting` skills.

1. Confirm the company, currency, and as-of date. If the input doesn't name a company, ask and stop.
2. Gather financials: from the repo if present, otherwise from filings, each cited. Mark gaps as placeholders. Never invent them.
3. Run a DCF (with WACC built up from sourced inputs) and trading comparables. Add precedent transactions if deals are findable.
4. Produce sensitivity tables (WACC vs. terminal growth, WACC vs. exit multiple) and a football field of the ranges.
5. Bridge enterprise value to equity value per share.
6. Save the report to `reports/valuation/<company>-<as-of-date>.md` with assumptions, sources, and a not-investment-advice disclaimer.

Reply with the value range, the three inputs that move it most, and the saved path.
