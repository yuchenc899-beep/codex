# Screening Criteria — Master & Per-Sector Overlays

The screen is the "workings" of the skill. Every pick in the output must survive the master screen + the theme overlay. Show each stage's survivor count in the report.

---

## Master screen (applied to all themes)

Use these as the **default** thresholds. The user can override via the `Inputs` table in SKILL.md.

| Filter                      | Default (small/mid-cap) | Tight (high-conviction) | Loose (broad discovery) |
| --------------------------- | ----------------------- | ----------------------- | ----------------------- |
| Listing                     | US-listed + ADR         | US-listed only          | US + ADR + OTC          |
| Market cap                  | $300M – $50B            | $1B – $20B              | $100M – $100B           |
| Avg daily $ volume (3M)     | ≥ $5M                   | ≥ $20M                  | ≥ $1M                   |
| Revenue (LTM)               | ≥ $100M                 | ≥ $500M                 | ≥ $30M                  |
| 3Y revenue CAGR             | ≥ 8%                    | ≥ 15%                   | ≥ 0% (any)              |
| Gross margin                | ≥ 30%                   | ≥ 50%                   | ≥ 20%                   |
| Net debt / EBITDA           | ≤ 2.5x (or net cash)    | ≤ 1.5x (or net cash)    | ≤ 4.0x                  |
| Insider ownership           | ≥ 3%                    | ≥ 8%                    | ≥ 1%                    |
| Cash runway / coverage      | 24+ months              | 36+ months              | 12+ months              |
| Operating cash flow         | Positive LTM            | Positive 3Y avg         | Positive TTM            |
| Float short interest        | < 20%                   | < 10%                   | < 30%                   |
| Exclude                     | SPACs, distressed, pre-revenue biotech, recent IPOs < 12mo, financials with 3Y losses | | |

**Adjustments for ADR:**
- Verify primary listing on a recognized exchange (HKEX, LSE, TSE, etc.).
- Check ADR ratio (1:1, 1:2, 1:5, etc.) — affects price math.
- Note 144A vs Level 1 vs Level 3 — Level 1 is most liquid for retail.
- Flag foreign tax withholding (some countries levy 25-30% on dividends, only 15% reclaimable via treaty).
- For HK ADRs, watch for HFCAA (Holding Foreign Companies Accountable Act) delisting risk.

**Adjustments for sector:**
- **Biotech / pharma** — replace revenue/EBITDA filters with: pipeline depth, cash runway, PDUFA calendar, partnership economics.
- **Mining / commodities** — replace P/E with EV/Resource (NPV per share, AISC for gold, IRR for development assets). Profitability is OK to be absent for pre-revenue producers.
- **Defense / aerospace** — accept low single-digit operating margins if backlog visibility is multi-year.
- **REITs** — replace gross margin with FFO/affordability, occupancy, lease length.
- **Banks / insurers** — use NIM, NPL ratio, CET1, combined ratio instead of gross margin.
- **Crypto-adjacent** — must have real revenue model and audited financials. No pure-token treasury plays.

---

## Per-sector overlays

For each sector, add **theme-specific** filters that identify the screenable universe for that theme.

### Critical Minerals & Mining

- Revenue exposure to critical minerals (Li / Ni / Co / REE / Ga / Ge / Mn / W / graphite) ≥ 30%
- Operating stage: **producing** or **near-production** (within 24 months) — exclude pure exploration
- Jurisdiction: US, EU, Canada, Australia, Japan, Korea (friendly jurisdictions; cap on Chinese exposure ≤ 25%)
- Project NPV at consensus prices ≥ current EV
- IRA 45X/45Y eligibility for US-domiciled producers
- Permits in hand or in advanced review (≥ 50% of capex committed)
- **Watch for:** single-asset risk, jurisdictional risk, capex overruns, commodity price beta

**Source screeners:** TradingView, Finviz (sector: Basic Materials → Mining), company 10-Ks, S&P Capital IQ (project-level data).

### Defense & Aerospace

- Backlog ≥ 3x LTM revenue
- US/allied government as primary customer
- NDO/IDIQ contract vehicle exposure
- Active programs in production (not R&D-only)
- Margins: gross ≥ 15%, operating ≥ 8% (defense runs thin)
- Insider ownership: 5%+
- **Watch for:** continuing resolution risk, FY26 budget, Pentagon color of money, ITAR/export control

**Source screeners:** Bloomberg DODEF, GovWin, USAspending.gov, DoD contract announcements.

### Power Grid & Electrification

- Revenue exposure to T&D, transformers, switchgear, HVDC, grid software, smart meters, BESS ≥ 50%
- Backlog ≥ 1.5x LTM
- Customer mix: utility, IPP, hyperscaler
- Capex commitments from utility customers (EEI data)
- IRA 45X/48E/45Y exposure
- **Watch for:** permitting delays, transformer lead times, transformer copper/aluminum costs, utility ROE compression

**Source screeners:** EEI, S&P Global Market Intelligence, company 10-Ks, IRA project tracker (DoE).

### Semiconductors

- Revenue exposure to advanced node, packaging, HBM, SiC, GaN, equipment, EDA, IP ≥ 50%
- CHIPS Act Title III funding application status (awarded / in review)
- Customer concentration: top 3 < 70% (unless Tier-1 anchor)
- Capex visibility ≥ 18 months
- **Watch for:** export controls (Entity List, EAR), China revenue exposure, equipment lead times, customer concentration

**Source screeners:** SEMI, SIA, Bloomberg supply-chain data, CHIPS.gov program office.

### Pharma / Biotech / CDMO

- Pipeline depth: ≥ 3 IND-stage or 1 Phase 3
- Cash runway: ≥ 24 months
- PDUFA calendar with 12-24 month catalyst
- Big Pharma partnership economics (royalty/milestone tier)
- For CDMOs: utilization ≥ 70%, GLP-1 / ADC / mRNA capability, FDA inspection history clean
- **Watch for:** FDA Adcom risk, trial readout, IP cliffs, IRA drug price negotiation list

**Source screeners:** Biomedtracker, Evaluate Pharma, FDA calendar, clinicaltrials.gov, BioCentury.

### Cybersecurity

- ARR growth ≥ 20%
- Net retention ≥ 115%
- Rule of 40 ≥ 40 (or clear path to FCF positive)
- Differentiated platform (not pure MSSP)
- Federal / regulated vertical exposure (FedRAMP, CMMC)
- **Watch for:** valuation reset risk, AI displacement, MSSP consolidation, government budget

**Source screeners:** IDC, Gartner, company filings, FedRAMP marketplace.

### AI Infrastructure (energy, cooling, optics, networking)

- Revenue exposure to data center build-out (power, cooling, optical, networking, racks) ≥ 50%
- Hyperscaler / neocloud customer (top 3 disclosed where possible)
- Backlog / design-wins ≥ 1.5x LTM
- AI capex cycle sensitivity (must survive if hyperscaler capex normalizes)
- **Watch for:** AI capex digestion, optical transition (800G → 1.6T), power availability, supply chain

**Source screeners:** Dell'Oro, Crehan Research, Synergy Research, hyperscaler capex disclosures (MSFT / GOOG / META / AMZN 10-Q).

### Energy Transition / Renewables

- Project pipeline ≥ 3 GW (for developers) or component market share ≥ 10% (for manufacturers)
- LCOE / cost curve position
- Offtake / PPA coverage
- IRA transferability eligibility (45X/45Y/48E)
- **Watch for:** interconnection queues, IRA repeal risk, battery price decline, panel price collapse

**Source screeners:** BNEF, Wood Mackenzie, SEIA, EIA, IRA tracker.

### Industrials / Reshoring

- US-domiciled manufacturing with announced or commissioned capex
- Customer mix includes US industrial / defense / critical infrastructure
- Backlog ≥ 1.2x LTM
- Pricing power (gross margin trend)
- **Watch for:** labor cost, build-out delays, automation capex, capex efficiency vs peers

**Source screeners:** Reshoring Initiative, FRED industrial production, NAM, company filings.

---

## Screeners and where to run them

| Screener | URL | Strengths | Limits |
| --- | --- | --- | --- |
| Finviz | https://finviz.com/screener.ashx | Free, fast, custom filters, US-listed only | Daily data only, no fundamental deep-dive |
| Yahoo Finance Screener | https://finance.yahoo.com/screener/ | Free, global, equity + ETF + crypto | Slower, fewer metrics, no custom formulas |
| TradingView | https://www.tradingview.com/screener/ | Free, charts inline, global, technicals | Custom filters limited in free tier |
| Stock Rover | https://www.stockrover.com/ | US, deep fundamental screen, 10Y history | Paid, US only |
| Screener.in | https://www.screener.in/ | India deep dive | India only |
| S&P Capital IQ | https://www.capitaliq.spglobal.com/ | Institutional-grade, deal-level, project-level | Paywalled |
| Bloomberg | https://www.bloomberg.com/markets/screener | Institutional, global | Paywalled |
| Koyfin | https://www.koyfin.com/ | Free tier, US + global, good fundamentals | Limited in free tier |
| TIKR | https://www.tikr.com/ | Free screening + valuation comps | US-listed focus |
| Macroaxis | https://www.macroaxis.com/ | Global, alternative data | Free tier limited |

For the screening workings section, **name the screener(s) used** and the size of the initial universe. Cite the screener URL in the Sources block.

## Adjacent data sources for the screen

| Data | URL | When to use |
| --- | --- | --- |
| SEC EDGAR (10-K, 10-Q, 8-K, DEF 14A) | https://www.sec.gov/edgar/search/ | Always — primary source for any US-listed pick |
| FRED (macro data) | https://fred.stlouisfed.org/ | Macro context (rates, inflation, sector-level) |
| US Treasury yield curve | https://home.treasury.gov/resource-center/data-chart-center/interest-rates/ | Risk-free rate baseline |
| BEA industry data | https://www.bea.gov/ | Sector-level demand proxies |
| BLS PPI by industry | https://www.bls.gov/ppi/ | Pricing power check |
| EIA energy data | https://www.eia.gov/ | Energy / utilities context |
| FDA calendar (PDUFA) | https://www.fda.gov/advisory-committees/advisory-committee-calendar | Biotech catalyst dates |
| USAspending.gov | https://www.usaspending.gov/ | Defense / government contract verification |
| CHIPS.gov program office | https://www.nist.gov/chips | Semis — funding status |
| IRA project tracker (DoE) | https://www.energy.gov/lpo/ira-funded-projects | Energy / industrials — IRA funding status |
| DoD contract announcements | https://www.defense.gov/News/Contracts/ | Defense contract awards |
| Patent data (USPTO) | https://www.uspto.gov/patents | Moat verification |
| OpenInsider | https://openinsider.com/ | Insider buying/selling |
| WhaleWisdom (13F aggregator) | https://whalewisdom.com/ | Institutional positioning |
| Glassnode (crypto) | https://glassnode.com/ | Crypto-adjacent on-chain |
| DefiLlama | https://defillama.com/ | DeFi / protocol TVL |

## Reproducibility guardrails

When writing the screening workings section:

- **Name the screener** (Finviz, Yahoo, etc.) and the exact filters used.
- **Quote the exact filter values** (e.g. "Mkt cap: $500M–$30B" not "small/mid-cap").
- **Show the count after each filter step** so the user can follow the funnel.
- **Date the data** — "as of [ISO date]" because screens drift daily.
- **Acknowledge manual overrides** — if a pick was added off-screen (e.g. from a 13F cluster buy, congressional trade, or qualitative judgment), say so explicitly. The screen is the floor, not the ceiling — but off-screen picks must justify themselves in the per-ticker bullets.

If the user later runs the same screen on a different day, the survivor set will shift. That's expected — flag it.
