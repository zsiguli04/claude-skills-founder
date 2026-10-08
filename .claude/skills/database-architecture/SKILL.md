---
name: database-architecture
description: Design schemas and migrations for financial data, including money columns, double-entry ledgers, bitemporal history, audit trails, and multi-currency balances. Use when creating tables, writing migrations, or reviewing data models.
---

# Database architecture

## Money

- `NUMERIC(precision, scale)` or integer minor units with a currency column. Never `FLOAT`, `REAL`, or `DOUBLE`.
- Every amount column has a currency next to it, or the table documents a single currency.
- Store exchange rates with enough scale (at least 8 decimal places) and a source.

## Ledger

Use double-entry for any balance that matters:

- `journal_entries` (id, posted_at, description, idempotency_key) and `journal_lines` (entry_id, account_id, amount, currency).
- Lines in an entry sum to zero per currency. Enforce in a transaction or a deferred constraint.
- Append only. Corrections are reversing entries, never `UPDATE` or `DELETE`.
- Balances are derived from lines. Cache them if needed, and reconcile the cache.

## History

- Bitemporal tables where corrections matter (prices, holdings, tax rules): `valid_from`, `valid_to`, `recorded_at`.
- Audit log for every change to user-facing financial data: who, when, what, before and after.

## Migrations

- Forward-only, reviewed, reversible where possible.
- Backfill in batches. Never lock a large table in one transaction.
- Add columns nullable, backfill, then add the constraint.

## Access

- Row-level security or tenant ids on every user-data table.
- Separate read-only roles for analytics.
- Encrypt sensitive columns (tax ids, account numbers) at the application or column level.

## Review checklist

- [ ] No float money columns
- [ ] Currency on every amount
- [ ] Ledger entries balance
- [ ] Natural keys unique-constrained
- [ ] Indexes on foreign keys and common filters
- [ ] Migration safe on a production-sized table
