# ADR 0002: authentication

Status: proposed; needs a product decision before phase 16.

## Context

The brief suggests Supabase Auth or an equivalent. The data is personal wealth information about Hungarian residents, so EU data residency, MFA, and auditability matter more than speed of setup.

## Options

| Option | For | Against |
|:-------|:----|:--------|
| Supabase Auth (EU region) | fast, MFA, social and magic links, JWTs the API can verify | vendor dependency; check its data processing terms and region guarantees |
| Self-hosted Keycloak or Zitadel | full control, EU hosting by construction, SSO for enterprise | operations burden |
| Auth implemented in the API | no dependency | most security risk; not recommended |

## Proposal

Use a managed provider with an EU region (Supabase Auth is the default candidate) and keep the API provider-agnostic: it verifies a standard OIDC JWT, maps `sub` to `users.auth_subject`, and does all authorization (roles, organizations, RLS) itself. Switching providers then touches configuration only.

Before deciding: read the provider's data processing agreement, sub-processor list, and region guarantees.
