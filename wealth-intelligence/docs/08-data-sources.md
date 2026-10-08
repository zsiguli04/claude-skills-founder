# Data sources and licensing

No source is ingested until its row below is filled in from the source's own terms and, where needed, a written agreement. Nothing here has been verified yet: the official hosts are blocked from the build environment (see `00-environment.md`), and licence terms must be read, not assumed.

| Source | Data | Access method | Licence and commercial use | Redistribution | Rate limits | Status |
|:-------|:-----|:--------------|:---------------------------|:---------------|:------------|:-------|
| e-beszamolo.im.gov.hu (Céginformációs Szolgálat) | Published annual financial statements of Hungarian companies | to verify (web; bulk or API availability unknown) | to verify | to verify | to verify | candidate |
| e-cegjegyzek.hu | Company registry: identifiers, legal form, owners, officers | to verify | to verify | to verify | to verify | candidate |
| Commercial providers (for example Opten, Dun & Bradstreet, Creditreform) | Normalized financials, ownership, risk data | API under contract | contract | contract | contract | candidate; compare cost and coverage |
| MNB (Magyar Nemzeti Bank) | FX rates, house price index, base rate, statistics | to verify (statistical downloads; FX web service) | to verify | to verify | to verify | candidate |
| ÁKK (Államadósság Kezelő Központ) | Government bond yields for the risk-free rate | to verify | to verify | to verify | to verify | candidate |
| BÉT (Budapest Stock Exchange) | Listed prices, peer multiples | to verify; market data is usually licensed | to verify | to verify | to verify | candidate |
| Nemzeti Jogszabálytár, Magyar Közlöny, NAV, kormany.hu | Law texts, drafts, guidance | web | public; reuse terms to verify | to verify | to verify | needed for phase 8 |

For each source, before ingestion:

1. Read and save the terms of use (link and retrieval date).
2. Confirm commercial use and whether derived data (valuations) may be shown to customers.
3. Confirm redistribution limits (can a report include the raw figures?).
4. Record rate limits and implement them in the client.
5. Record the data's update frequency and set the `STALE_DATA` threshold from it.
