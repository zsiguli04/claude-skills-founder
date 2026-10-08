---
name: data-engineering
description: Build or debug pipelines for market data, prices, FX rates, transactions, and account data, with point-in-time correctness, idempotent loads, corporate actions, and lineage. Use for ingestion, ETL/ELT, data quality, or backfill work.
---

# Data engineering

## Principles

- **Idempotent loads.** Rerunning a job for the same window produces the same rows. Upsert on a natural key, never blind insert.
- **Point-in-time correctness.** Store when a value was true (`valid_from`, `valid_to`) and when you learned it (`recorded_at`). A backtest for date D reads only rows with `recorded_at <= D`. This prevents look-ahead bias.
- **Raw first.** Land source data unchanged in a raw zone, then transform. You can always rebuild from raw.
- **Lineage.** Every derived row can be traced to its source rows and the job version that produced it.

## Financial data specifics

| Topic | Rule |
|:------|:-----|
| Prices | Store close, adjusted close, and the adjustment factor separately |
| Corporate actions | Splits, dividends, mergers, ticker changes are events with effective dates. Apply them, don't overwrite history |
| Identifiers | Map tickers to a stable id (ISIN, FIGI, internal id). Tickers get reused |
| FX | Store rate, source, and timestamp. Say which side is base. Convert at the rate for the transaction date, not today |
| Time zones | Store UTC. Keep the exchange's local trading date as its own column |
| Holidays | Use an exchange calendar. A missing price on a holiday is not a gap |

## Data quality checks

Run on every load. Fail the load on a hard check, alert on a soft one.

- Schema: types, required fields, enums.
- Uniqueness of the natural key.
- Freshness: latest date vs. expected.
- Range: prices > 0, FX within a band of the prior day, no day-over-day move beyond a threshold without a corporate action.
- Reconciliation: row counts and totals match the source.

## Backfills

- Write the backfill as the normal job with a date range. No one-off scripts.
- Run on a copy first and diff against current data.
