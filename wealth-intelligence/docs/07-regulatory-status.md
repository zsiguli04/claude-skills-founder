# Hungarian regulatory status

Checked 2026-10-08. Re-verify before any user-facing release; this file records what was known and how confident we are.

## Vagyonadó (wealth tax)

| Item | Value | Source type | Confidence |
|:-----|:------|:------------|:-----------|
| Status | Draft bill published for public consultation by the Ministry of Finance on 2026-10-06; comments until 2026-10-14; not passed by Parliament | `PROPOSED_LEGISLATION` (reported) | medium: the consultation page on kormany.hu could not be opened from the build environment; status taken from several consistent news and adviser reports |
| Threshold and rates | 1% of net wealth above HUF 1bn up to a base of HUF 100bn, 1.5% above | `EXPERT_INTERPRETATION` of the draft | medium-low |
| First valuation date and filing | 2026-12-31; return and payment by 2027-08-31 | `EXPERT_INTERPRETATION` | medium-low; sources disagree on whether 2026 is the first tax year |
| Valuation methods, exemptions, non-resident scope | see `../../engine/rules/hu/RESEARCH.md` | `EXPERT_INTERPRETATION` | medium-low |

The platform stores this as rule status `DRAFT`. It must not be presented as law. When the act is published in Magyar Közlöny, a new rule version with status `ENACTED` (and later `EFFECTIVE`) is created from the official text, and the draft version stays for reproducibility.

## Personal income tax (SZJA) 2026

Flat 15% (Szja tv. 8. § (1)). `CURRENT_LAW`, confidence medium (statute text not opened from the build environment; rate confirmed by multiple secondary sources). A 2027 tax credit is announced, not enacted.

## Unblocking primary sources

Add `njt.hu`, `magyarkozlony.hu`, `kormany.hu`, and `nav.gov.hu` to the environment's allowed domains. Phase 8 (regulatory engine) depends on it.
