# Hungary: research record

Retrieved 2026-10-08. This is research, not tax or legal advice.

## Vagyonadó (wealth tax)

**Status: draft bill, not law.** The Ministry of Finance (Pénzügyminisztérium) published the bill for public consultation on 2026-10-06. Comments are due by 2026-10-14. Business groups (VOSZ, MKIK) have asked for business assets to be excluded and for lower rates, so the text may change.

**Confidence: medium-low.** The container's network policy blocked kormany.hu and every Hungarian news site, so the bill text was not read. Everything below comes from search-result summaries of tax advisers' and newspapers' write-ups. Read the bill before relying on any of it.

| Item | Draft rule (as summarized) | Source |
|:-----|:---------------------------|:-------|
| Taxpayers | Resident individuals (worldwide wealth), non-resident individuals (listed Hungarian assets only), trusts and private foundations (vagyonkezelési adóalany) | [RSM](https://www.rsm.hu/blog/csaladi-vallalat/vagyonado-2026-2027-magyarorszagon), [Infostart](https://infostart.hu/belfold/2026/10/06/elindult-az-egyeztetes-a-kata-adozasrol) |
| Tax base | Net taxable wealth above HUF 1,000,000,000 | [kormany.hu](https://kormany.hu/dokumentumtar/tarsadalmi-egyeztetes-a-vagyonadorol-szolo-torvenyjavaslatrol), [Andersen](https://hu.andersen.com/hu/hirek/vagyonado-torvenytervezet/) |
| Rates | 1% on the first HUF 100bn of the base, 1.5% above | [Bloomberg](https://www.bloomberg.com/news/articles/2026-10-06/hungary-unveils-wealth-tax-plan-raising-burden-on-ultra-rich), [Infostart](https://infostart.hu/belfold/2026/10/06/elindult-az-egyeztetes-a-kata-adozasrol) |
| Spouses | Assessed separately, each with their own HUF 1bn threshold | [VG](https://www.vg.hu/vilaggazdasag-magyar-gazdasag/2026/10/vagyonado-torvenyjavaslat-tarsadalmi-egyeztetes) |
| Debts | Deductible. The return lists deducted debts per asset | [hvg](https://hvg.hu/gazdasag/20261006_vagyonado-kiszamolas-gazdagok-osszvagyon-szabaly), [mfor](https://mfor.hu/cikkek/szemelyes_penzugyek/on-beleesik-igy-kell-kiszamolni-az-ingatlan-es-a-cegerteket-a-vagyonado-szabalyai-szerint.html) |
| Main home | No exemption | [mfor](https://mfor.hu/cikkek/szemelyes_penzugyek/on-beleesik-igy-kell-kiszamolni-az-ingatlan-es-a-cegerteket-a-vagyonado-szabalyai-szerint.html) |
| Valuation date | 31 December each year; first one 2026-12-31 | [BDO](https://www.bdo.hu/hu-hu/aktualitasok-blog/blog/vagyonado-2027), [RSM](https://www.rsm.hu/blog/csaladi-vallalat/vagyonado-2026-2027-magyarorszagon) |
| Filing and payment | Self-assessed, due 31 August of the following year; first due 2027-08-31 | [BDO](https://www.bdo.hu/hu-hu/aktualitasok-blog/blog/vagyonado-2027) |
| Entry into force | 2026-12-15 (BDO); the government's announcement says 2027-01-01 | [BDO](https://www.bdo.hu/hu-hu/aktualitasok-blog/blog/vagyonado-2027), [Bloomberg](https://www.bloomberg.com/news/articles/2026-10-06/hungary-unveils-wealth-tax-plan-raising-burden-on-ultra-rich) |
| Deferral | Available when paying causes a liquidity problem (state secretary's statement) | [VG](https://www.vg.hu/vilaggazdasag-magyar-gazdasag/2026/10/vagyonado-torvenyjavaslat-tarsadalmi-egyeztetes) |
| Exit tax | Planned separately for wealth above HUF 500m when moving abroad | [VG](https://www.vg.hu/vilaggazdasag-magyar-gazdasag/2026/10/vagyonado-tisza-karman-andras-exit-tax-milliardosok) |
| Expected reach | About 15,000 individuals and 2,000 trusts or foundations | [Portfolio](https://www.portfolio.hu/gazdasag/20261007/brutalisan-korbebastyazta-a-vagyonadot-a-tisza-kormany-867848) |

### Valuation rules (as summarized)

Set values, not market values. A value computed by the statutory method can't be penalized later even if the market price differs.

| Asset | Method |
|:------|:-------|
| Hungarian real estate | Bought within the last 12 months: the purchase price. Bought 1 to 10 years ago: the purchase price indexed by the MNB house price index. Otherwise: the NAV valuation model, then an appraiser as the last resort |
| Listed shares, and shares regularly traded off-exchange | Closing price on the last trading day of the year |
| Unlisted company shares | Mandatory formula: one third equity, two thirds earning capacity from the last three years' after-tax profit. Equity above HUF 500m is increased by hidden reserves |
| Movables, foreign assets, trust and foundation assets | In scope; methods not found in summaries |

### Open questions

1. Does the 1.5% band start at HUF 100bn of base (101bn net wealth, as modeled) or 100bn net wealth?
2. Do trusts and foundations get the HUF 1bn threshold?
3. Which Hungarian assets are taxable for non-residents? (The engine assumes assets located in HU.)
4. Can non-residents deduct debts, and which ones? (The engine deducts only debts tied to included assets.)
5. The exact earning-capacity formula for unlisted shares, and how hidden reserves are measured.
6. The FX rate for foreign assets (MNB rate on the valuation date is likely, not confirmed).
7. Rounding of the tax amount.
8. Whether the final act keeps 2026-12-31 as the first valuation date.

## SZJA (personal income tax) 2026

Flat 15% (Szja tv. 8. § (1)). From 2027 the government plans a tax credit that cuts the effective rate below the median wage, down to 9% at the minimum wage ([proab](https://proab.hu/proab-news/karman-andras-bejelentette-jon-a-szja-csokkentes-de-csak-2027-tol/), [hvg360](https://hvg.hu/360/20260930_bertargyalas-vkf-minimalber-garantalt-berminimum-mennyi-lesz-2027-szja-csokkentes)). The 2027 credit is not enacted and not modeled.

## To do once the bill text is reachable

Allow `kormany.hu` in the environment's network settings, then read the bill and resolve the open questions. Update the rule as version 2 with `supersedes: hu-vagyonado-individual@1`. When the act is promulgated in Magyar Közlöny, add version 3 with `status: enacted` and the act's citation.
