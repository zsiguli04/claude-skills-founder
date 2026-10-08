# Database design

PostgreSQL 16. Implemented in phase 4 as SQLAlchemy 2 models plus Alembic migrations, tested against a real PostgreSQL instance.

## Conventions

| Convention | Rule |
|:-----------|:-----|
| Keys | `id uuid primary key default gen_random_uuid()` |
| Tenancy | every tenant table has `organization_id uuid not null`, an index on it, and a row-level security policy `organization_id = current_setting('app.organization_id')::uuid` |
| Money | `numeric(24,6)` plus `currency char(3)` with a check against ISO 4217 codes in use |
| Rates | `numeric(12,10)`; a check keeps percentages within their valid range |
| Time | `timestamptz` in UTC; business dates as `date` |
| History | append-only where noted; corrections are new rows that reference the old one |
| Soft facts | `is_estimated boolean`, `confidence_score numeric(5,2)` between 0 and 100 |
| Hashes | `calculation_hash char(64)`: SHA-256 hex of canonical JSON |
| Enums | PostgreSQL enum types for statuses and roles |

Global (not tenant) tables: `users`, `companies`, `company_identifiers`, `financial_periods`, `financial_statements`, `financial_metrics`, `tax_rules`, `tax_rule_versions`, `regulatory_sources`, `regulatory_changes`. Public company data is shared; what an organization does with it (its valuations, people, wealth profiles) is private.

## Entities

### Identity and access

| Table | Key columns | Notes |
|:------|:------------|:------|
| `users` | `id`, `auth_subject` (identity provider id), `email`, `display_name`, `status`, `created_at` | no passwords stored here when using an external identity provider |
| `organizations` | `id`, `name`, `kind` (`personal`, `advisory_firm`, `family_office`, `enterprise`), `plan`, `created_at` | tenant root |
| `organization_members` | `organization_id`, `user_id`, `role` (`USER`, `ANALYST`, `ADVISOR`, `ADMIN`), `invited_by`, `created_at` | unique `(organization_id, user_id)`; `SUPERADMIN` is a platform flag on `users`, never a member role |
| `report_shares` | `organization_id`, `report_version_id`, `grantee_email`, `scope jsonb` (sections allowed), `expires_at`, `revoked_at` | advisor handoff; least exposure |

### People, companies, ownership

| Table | Key columns | Notes |
|:------|:------------|:------|
| `people` | `organization_id`, `id`, `display_name`, `tax_residency`, `is_demo` | no tax id unless needed; then encrypted column |
| `companies` | `id`, `legal_name`, `legal_form`, `country`, `status`, `founded_on`, `is_demo` | global |
| `company_identifiers` | `company_id`, `scheme` (`HU_CEGJEGYZEKSZAM`, `HU_ADOSZAM`, `LEI`), `value`, `valid_from`, `valid_to` | unique `(scheme, value, valid_from)`; deduplication key |
| `ownerships` | `organization_id`, `id`, `owner_type` (`person`, `company`, `trust`), `owner_id`, `owned_type` (`company`, `asset`), `owned_id`, `share_class`, `economic_pct`, `voting_pct`, `is_beneficial`, `control`, `valid_from`, `valid_to`, provenance columns | checks: `0 < economic_pct <= 1`, `0 <= voting_pct <= 1`. A deferred trigger blocks total economic ownership of one entity above 100% per share class at any date. Cycles are detected by the wealth engine before saving and reported as `CIRCULAR_OWNERSHIP` |

### Financial data (global, provenance on every number)

| Table | Key columns | Notes |
|:------|:------------|:------|
| `financial_periods` | `company_id`, `id`, `fiscal_year`, `period_start`, `period_end`, `currency`, `unit`, `is_consolidated`, `audited` | unique `(company_id, period_end, is_consolidated)`: blocks duplicate periods |
| `financial_statements` | `period_id`, `kind` (`balance_sheet`, `income_statement`, `cash_flow`), `source_document_id`, `data_version` | one per kind per period per data version |
| `financial_metrics` | `period_id`, `metric` (`revenue`, `ebitda`, `ebit`, `ebt`, `net_income`, `d_and_a`, `capex`, `nwc`, `cash`, `debt`, `equity`, `total_assets`, ...), `normalized_value`, plus the provenance columns below | unique `(period_id, metric, data_version)` |

Provenance columns (on `financial_metrics`, `assets`, `liabilities`, `ownerships`, `valuation_inputs`):
`source`, `source_url`, `retrieved_at`, `financial_year`, `original_value text`, `normalized_value numeric`, `currency`, `unit`, `is_estimated`, `confidence_score`, `data_version`.

### Valuation

| Table | Key columns | Notes |
|:------|:------------|:------|
| `valuations` | `organization_id`, `id`, `company_id`, `valuation_date`, `status`, `parameter_set_id`, `engine_version`, `data_version`, `rule_version`, `assumption_version`, `source_version`, `calculation_hash`, `created_by`, `created_at` | append-only |
| `valuation_inputs` | `valuation_id`, `name` (`wacc`, `rf`, `beta`, `erp`, `g`, `peer_multiple_ev_ebitda`, ...), `value`, `kind` (`FACT`, `ASSUMPTION`, `ESTIMATE`), provenance | every input that influenced the result |
| `valuation_results` | `valuation_id`, `method` (`dcf`, `ev_ebitda`, `ev_revenue`, `ev_ebit`, `pe`, `asset_based`, `weighted`), `low`, `base`, `high`, `weight`, `confidence`, `data_quality_score`, `trace jsonb` | |
| `scenarios` | `organization_id`, `id`, `subject_type`, `subject_id`, `name` (`BEAR`, `BASE`, `BULL`, custom), `overrides jsonb`, `created_by` | overrides validated against a schema |
| `sensitivity_results` | `valuation_id`, `x_param`, `y_param`, `grid jsonb` (values as strings; invalid cells carry an error code) | |
| `market_parameter_sets` | `id`, `name`, `as_of`, `params jsonb`, provenance | used by batch runs; enables "companies over 1bn at WACC 12%" |

National batch valuations are stored under a reserved platform organization and exposed to tenants read-only through a view. A tenant's own valuations stay private to that tenant.

### Regulation

| Table | Key columns | Notes |
|:------|:------------|:------|
| `tax_rules` | `id` (`rule_id`, for example `hu-vagyonado-individual`), `jurisdiction`, `tax_type`, `subject_kind` | identity only |
| `tax_rule_versions` | `rule_id`, `version`, `status` (`PROPOSED`, `DRAFT`, `ENACTED`, `EFFECTIVE`, `EXPIRED`, `REPEALED`), `effective_from`, `effective_to`, `brackets jsonb`, `thresholds jsonb`, `exceptions jsonb`, `valuation_methods jsonb`, `parameters jsonb`, `source_id`, `source_type` (`CURRENT_LAW`, `PROPOSED_LEGISLATION`, `GOVERNMENT_COMMUNICATION`, `NEWS`, `EXPERT_INTERPRETATION`, `ASSUMPTION`), `confidence`, `supersedes`, `notes jsonb`, `approved_by`, `created_at`, `updated_at` | immutable after approval; unique `(rule_id, version)` |
| `regulatory_sources` | `id`, `title`, `issuer`, `url`, `source_type`, `published_on`, `retrieved_at`, `content_hash`, `storage_key` | one row per fetched document version |
| `regulatory_changes` | `id`, `source_id`, `previous_source_id`, `diff_summary`, `affected_rule_ids`, `detected_at`, `review_status`, `reviewed_by` | |

### Wealth and exposure

| Table | Key columns | Notes |
|:------|:------------|:------|
| `assets` | `organization_id`, `id`, `person_id`, `category` (`cash`, `bank_deposit`, `securities`, `private_company_shares`, `real_estate`, `vehicle`, `art`, `collectible`, `crypto`, `private_investment`, `receivable`, `other`), `location`, `is_liquid`, `value`, `currency`, `valuation_method`, provenance | liquidity is explicit per asset; private shares and real estate default to illiquid |
| `liabilities` | `organization_id`, `id`, `person_id`, `category` (`mortgage`, `business_loan`, `personal_loan`, `other`), `amount`, `secured_on_asset_id`, provenance | |
| `exposure_calculations` | `organization_id`, `id`, `person_id`, `rule_id`, `rule_version`, `rule_status`, `gross_wealth`, `modelled_eligible_liabilities`, `modelled_net_wealth`, `legal_tax_base`, `potential_exposure`, `liquid_assets`, `liquidity_gap`, all version columns, `calculation_hash`, `trace jsonb` | modelled net wealth and legal tax base are separate columns |

### Documents, reports, AI, audit, billing

| Table | Key columns | Notes |
|:------|:------------|:------|
| `documents` | `organization_id`, `id`, `kind`, `storage_key`, `sha256`, `mime_type`, `size`, `uploaded_by`, `encryption_key_id` | file bytes in object storage, encrypted |
| `document_extractions` | `document_id`, `field`, `value`, `page`, `bbox`, `confidence`, `status` (`EXTRACTED`, `CONFIRMED`, `REJECTED`), `confirmed_by` | nothing reaches financial tables before `CONFIRMED` |
| `reports` | `organization_id`, `id`, `subject_type`, `subject_id`, `title` | |
| `report_versions` | `report_id`, `version`, `inputs_hash`, `content jsonb`, `pdf_storage_key`, `created_by`, `created_at` | immutable snapshots |
| `audit_logs` | `id bigserial`, `organization_id`, `user_id`, `action`, `entity`, `entity_id`, `ip_hash`, `detail jsonb`, `at` | append-only: `UPDATE` and `DELETE` revoked from the application role and blocked by trigger |
| `ai_requests` | `organization_id`, `id`, `purpose`, `model`, `input_hash`, `input_tokens`, `cache_read_tokens`, `created_at` | no raw personal data |
| `ai_responses` | `request_id`, `output jsonb`, `validated boolean`, `validation_errors`, `output_tokens`, `cost_usd numeric(12,6)`, `latency_ms` | |
| `subscriptions` | `organization_id`, `plan`, `status`, `period_start`, `period_end` | |
| `usage` | `organization_id`, `metric`, `quantity`, `period` | |

## Integrity enforced in the database

- Duplicate financial periods: unique constraint.
- Ownership above 100%: deferred constraint trigger.
- Percentages and confidence ranges: check constraints.
- Currency codes: check constraint.
- Audit log immutability: privileges plus trigger.
- Approved rule versions immutable: trigger blocks updates once `approved_by` is set.
- Tenant isolation: RLS on every tenant table, with the application connecting as a role that cannot bypass RLS.

## Scale notes (measured in phase 18, not assumed)

- `financial_metrics` is the largest table (100,000 companies x 5 years x about 30 metrics is about 15 million rows). Index `(period_id, metric)`; consider partitioning by `fiscal_year` if the benchmark shows a need.
- National statistics read from `valuation_results` joined to `valuations` filtered by `market_parameter_sets.id`; index `(parameter_set_id, method, base)`.
