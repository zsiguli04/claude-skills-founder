---
name: security
description: Secure a financial application, covering PII and financial data handling, secrets, authentication, authorization, encryption, audit logging, and common web vulnerabilities. Use when writing or reviewing code that touches user data, credentials, payments, or access control.
---

# Security

## Data classification

| Class | Examples | Handling |
|:------|:---------|:---------|
| Restricted | Tax ids, account and card numbers, credentials, bank tokens | Encrypted at rest at field level, masked in UI and logs, access audited |
| Confidential | Balances, transactions, holdings, income | Encrypted at rest, tenant-isolated, never in analytics without consent |
| Internal | Aggregated, de-identified metrics | Standard controls |

## Rules

- **Secrets:** from a secret manager or environment, never in code, config files, or logs. Scan commits for secrets.
- **AuthN:** MFA for users with access to money movement or tax filing. Short-lived sessions, rotation on privilege change.
- **AuthZ:** check ownership on every object access server side (no IDOR). Deny by default.
- **Input:** parameterized queries only. Validate amounts (sign, scale, range) and currency codes at the boundary.
- **Logging:** no restricted data in logs. Log security events (login, failed login, permission change, export, money movement) to an append-only store.
- **Third parties:** least-privilege tokens for bank and broker aggregators. Store their tokens as restricted data.
- **Dependencies:** pin versions, scan for known vulnerabilities in CI.
- **Money movement:** idempotency keys, rate limits, and a second factor or confirmation step.

## Review focus

When reviewing a change, check in this order:

1. Can a user read or change another user's data?
2. Does restricted data leak into logs, errors, URLs, analytics, or LLM prompts?
3. Is any secret committed or printed?
4. Is untrusted input reaching a query, shell, template, or file path?
5. Can a request be replayed to move money or change state twice?

## Compliance context

Requirements depend on jurisdiction and business type (for example GDPR, GLBA, PCI DSS, SOC 2). Use the `regulatory-research` skill to confirm which apply before claiming compliance.
