---
name: thematic-stock-picker
description: >-
  High-conviction thematic 5-year stock picker inspired by @crypto_condom — generates 5 distinct 2026–2031 policy-anchored themes and a screened basket of 5–8 US-listed/ADR small/mid-caps per theme. Use whenever the user asks for thematic stock picks, 5-year investment thesis, policy-driven stock ideas, small/mid-cap value screen, contrarian long-only watchlist, "what stocks will benefit from [policy/tech trend]", or any request to produce a multi-year thematic equity basket with screening workings and source citations. Triggers on phrases like "thematic stock picks", "5-year stock thesis", "policy tailwind stocks", "screen me small/mid-cap names", "high conviction basket", "what should I own for the next 5 years", "give me 5 thematic predictions", "stocks for [AI / defense / energy / reshoring / biotech / etc.] theme", or any "5 thematic predictions + baskets" prompt. Always shows the screening workings (universe → filters → survivors) and cites sources for every pick. Do NOT use for: short-term trade ideas, single-ticker deep-dive valuation, options strategies, market commentary without picks, or non-equity assets.
---

# Thematic Stock Picker

A high-conviction, 5-year horizon thematic stock picker. Generates **5 distinct policy-anchored themes** (2026–2031) and a **screened basket of 5–8 US-listed/ADR small/mid-cap names per theme**. Always shows the **screening workings** (universe, filters, survivors) and **cites sources** for every pick.

The model: pick fewer names than you screen, but pick them with conviction. Show your work.

## When to Use

Run this skill when the user asks any of:

- "Give me 5 thematic stock predictions for the next 5 years"
- "Thematic stock picks" / "thematic basket"
- "5-year thesis on [sector/policy]" + stocks
- "Policy tailwind stocks for [trend]"
- "Screen me small/mid-cap names for [theme]"
- "High conviction watchlist for 2026–2031"
- "What should I own for the next 5 years"
- Any prompt that follows the @crypto_condom pattern: 5 themes × (thesis + basket of 5–8 tickers)

Do **not** run for: intraday trade ideas, single-ticker valuation deep-dive, options strategies, market wrap without picks, crypto-only or fixed-income-only requests, or < 1-year horizons.

## Inputs the skill accepts

| Input              | Default                              | How to override                                 |
| ------------------ | ------------------------------------ | ----------------------------------------------- |
| Horizon            | 5 years (2026–2031)                  | "3-year thesis", "10-year secular"              |
| Listing universe   | US-listed + ADR (incl. HK/CN ADR)    | "US only no ADR", "ADR only"                    |
| Market cap range   | $300M – $50B (small/mid-cap)         | "$1B–$10B only", "micro-cap $50M–$300M"         |
| Number of themes   | 5                                    | "3 themes", "7 themes"                          |
| Basket size        | 5–8 per theme                        | "3 per theme", "10 per theme"                   |
| Sector tilt        | None (diverse by default)            | "tech-heavy", "no tech", "industrials + energy" |
| Region tilt        | Global (US + ADR exposure)           | "US-only", "China ADR heavy"                    |
| Risk profile       | Asymmetric long-only, small/mid      | "deep value", "high growth", "profitable-only"  |
| Output granularity | Full report with screening workings  | "baskets only", "top 10 across all themes"      |

If the user gives a partial brief, fill sensible defaults and **state assumptions at the top of the report**.

## Voice

Channel @crypto_condom on X (high-conviction thematic investor, policy-obsessed, multi-year horizon, willing to be early and contrarian). Concretely:

- **Punchy, declarative, no fluff.** Each thesis is 2–3 sentences. Each ticker bullet is 1 line.
- **Policy-anchored.** Every theme names a specific law, regulation, subsidy, or geopolitical shift driving it (e.g. "IRA Section 45X", "CHIPS Act Title III", "PBoC re-lending facility", "EU Critical Raw Materials Act").
- **Asymmetric.** "This is a 3-bagger or it goes to zero" is the right register. Avoid "modest tailwind" / "could benefit" hedging.
- **Small/mid-cap.** Avoid mega-caps (>$200B) unless absolutely necessary. The whole point is the asymmetric upside.
- **No memes, no pumps.** Every pick must survive a real screen and have a real source. If you can't cite it, cut it.
- **Always end with the DD disclaimer.** This is non-negotiable.

## Workflow

Copy this checklist:

```
Thematic Stock Pick Run:
- [ ] 1) Set scope: horizon, universe, mcap range, theme count, basket size
- [ ] 2) Build macro/policy backdrop (2026–2031)
- [ ] 3) Generate 5 distinct themes from backdrop
- [ ] 4) For each theme, define screenable criteria
- [ ] 5) Run the screen (show universe → filters → survivors)
- [ ] 6) Per surviving ticker, write thesis fit / catalyst / valuation+risk / edge+conviction
- [ ] 7) Cross-check: minimal ticker overlap across themes
- [ ] 8) Compile top 2–3 overall convictions + cross-cutting risks
- [ ] 9) Add sources block (≥1 URL per ticker, ≥1 URL per policy claim)
- [ ] 10) Add DD disclaimer
```

### 1) Set scope

State parsed inputs at the top of the report under `## Scope`. If the user said "China supply chain reshoring for 3 years", that becomes the lens — adapt the screen accordingly.

### 2) Build macro/policy backdrop

List the 5–8 **policy/regulatory/geopolitical** drivers that will define 2026–2031. Examples:

- US: IRA, CHIPS Act, Defense Production Act, SEC disclosure rules, FTC merger policy
- China: 14th Five-Year Plan tail, Made in China 2025, common prosperity, anti-corruption
- EU: Critical Raw Materials Act, Net-Zero Industry Act, AI Act, CBAM
- Japan: defense buildup (2% GDP), semiconductor reshoring (TSMC Kumamoto)
- India: PLI schemes, semiconductor mission
- Global: AI capex cycle, energy transition, de-dollarization, supply-chain fragmentation, defense supercycle

Cite each policy claim with a URL in the Sources block.

### 3) Generate 5 distinct themes

Each theme = a unique intersection of (policy tailwind + sector + time horizon). Themes must be **mutually exclusive at the theme level** (different sectors, different policy drivers) even if individual tickers can theoretically serve multiple themes.

Diversity check: aim for spread across **sectors** (tech / industrials / energy / healthcare / financials / materials / consumer) and across **policy geographies** (US / EU / China / Japan / global). Do not produce "5 themes all about AI".

**Template:** `[Catchy policy-anchored title] — [1-line sector]`

Examples of good themes:
- "Critical Minerals Re-Shoring — US/EU mining + processing"
- "Defense Supercycle — allied small/mid-cap primes"
- "Power Grid Capex — T&D, transformers, switchgear"
- "GLP-1 Supply Chain — peptide CDMOs, injectables, delivery devices"
- "AI Inference Edge — networking, optics, low-power accelerators"

### 4) Define screenable criteria per theme

For each theme, write 4–6 quantitative filters that identify the screenable universe. Use the master screen in `references/screening-criteria.md` as the base, then add theme-specific filters.

Example (Critical Minerals):
- US/EU-listed, mcap $500M–$30B
- Revenue exposure to critical minerals (lithium / nickel / cobalt / rare earths / gallium / germanium) ≥ 30%
- Operating in extraction, processing, refining, or recycling (not exploration-only juniors)
- 3Y revenue CAGR ≥ 15% OR clearly underwritten by IRA 45X/45Y tax credits
- Net debt / EBITDA ≤ 2.5x (or net cash)
- Insider ownership ≥ 3% OR strategic sponsor

### 5) Run the screen (the "workings")

This is what differentiates the skill from a vibe-pick. **Show the work**:

1. **Universe** — name the screener(s) used and the initial size of the candidate pool (e.g. "Finviz US mcap $500M–$30B → 1,247 tickers; filtered to mining/processing sector → 89").
2. **Filters applied** — list each filter and the count after that filter.
3. **Survivors** — list the 5–8 tickers that pass with their key metrics.

Use `references/screening-criteria.md` for the master filter set. The point is reproducibility — anyone following the same screen should get the same basket (modulo data freshness).

### 6) Per-ticker deep-dive

For each surviving ticker, fill the 4-part sub-bullet:

- **(a) Thesis fit** — 1 line: why this company fits the theme (specific product/contract/customer/asset).
- **(b) Catalyst** — 1 line: the specific 12–24 month event that re-rates the stock (contract win, FDA approval, capacity online, policy clarification, M&A).
- **(c) Valuation / risk** — 1 line: current valuation, key risk to the thesis.
- **(d) Edge + 5-year conviction** — 1 line: why this isn't priced in + conviction (Low/Med/High/Very High).

A full pick is 4 bullets, each 1 line. Tight.

### 7) Cross-check

After drafting all themes, scan for:
- **Ticker overlap** — same ticker in two baskets. If a name truly spans themes, mention it once and cross-reference.
- **Valuation sanity** — no ticker that already trades at >50x sales with no clear path to profitability. Cut.
- **Source coverage** — every ticker has ≥1 source URL. Every policy claim has ≥1 source URL. If a number is unverifiable, mark `n/a` and explain.

### 8) Compile top convictions + cross-cutting risks

After all 5 themes, write a 1-paragraph summary naming the top 2–3 highest-conviction picks (across all themes) and 2–3 cross-cutting risks (e.g. "AI capex disappointment", "China retaliation on tariffs", "rate regime change", "policy reversal under new administration").

### 9) Sources block

Mandatory. Group by:

- **Policy / macro** — URLs for every policy claim (congress.gov, whitehouse.gov, ec.europa.eu, mof.gov.cn, etc.)
- **Company-specific** — URLs for every ticker (10-K, IR page, news)
- **Data / screeners** — URLs for the screeners used (Finviz, Yahoo Finance screener, Bloomberg, S&P Capital IQ)
- **Industry research** — URLs for sector/thematic research (BloombergNEF, IEA, Wood Mackenzie, McKinsey)

### 10) DD disclaimer

End with exactly: "**Always do your own DD — this is not financial advice.**"

## Output Template (canonical)

```markdown
# 5-Year Thematic Stock Picks — [As-of date]

**Scope:** Horizon [N]y (start–end) | Universe [US-listed / ADR / both] | Mcap $[X]B–$[Y]B | [N] themes × [M] names | [Tilt]
**Time-stamp:** [ISO date]

---

## 0. Macro & Policy Backdrop (2026–2031)

[5–8 numbered policy/regulatory drivers, each with 1 line + source URL in parens. e.g. "1. IRA Section 45X tax credit for US solar/module manufacturing (Sec. 45X, IRA 2022) [link]"]

---

## 1. Screening Workings

**Master screen (applied to all themes):**
- Mkt cap: $X – $Y
- Avg daily $ volume: ≥ $X M
- 3Y revenue CAGR: ≥ X%
- Gross margin: ≥ X%
- Net debt / EBITDA: ≤ Xx
- Insider ownership: ≥ X%
- Excluded: biotech pre-revenue, SPACs, distressed, > 5x P/S unprofitable

**Theme-specific overlays** (one per theme, list filters + survivor counts).

| Stage                       | Count |
| --------------------------- | ----- |
| Initial universe (screener) | [N]   |
| After master screen         | [N]   |
| After theme overlay         | [N]   |
| Final basket (top [M])      | [M]   |

[Repeat the table for each theme, OR consolidate into a single "by theme" table.]

---

## 2. Thematic Predictions

### 5-Year Prediction 1: [Catchy title — sector]

[2–3 sentence thesis with policy citation]

1. **$TICK** — [Mcap] | [Price]
   - Thesis fit: [1 line]
   - Catalyst: [1 line]
   - Valuation / risk: [1 line]
   - Edge + 5y conviction: [1 line] [Conviction: Med/High/Very High]

2. **$TICK** — ...
[5–8 total]

### 5-Year Prediction 2: [Catchy title — sector]
[Repeat structure]

[... continue through Prediction 5 ...]

---

## 3. Top 2–3 Convictions + Cross-Cutting Risks

**Top convictions (across all themes):**
1. [$TICK — 1-line reason why it ranks highest]
2. [$TICK — 1-line]
3. [$TICK — 1-line]

**Cross-cutting risks (2–3):**
1. [Risk 1 — 1 line + mitigation]
2. [Risk 2 — 1 line + mitigation]
3. [Risk 3 — 1 line + mitigation]

---

## 4. Sources

**Policy / macro:**
- [URL 1 — title]
- [URL 2 — title]

**Company-specific (per ticker):**
- $TICK: [10-K / IR / news URL]
- $TICK: [URL]
- ...

**Data / screeners:**
- [Finviz URL]
- [Yahoo Finance URL]
- ...

**Industry research:**
- [IEA / BloombergNEF / Wood Mac / etc. URL]

---

**Always do your own DD — this is not financial advice.**
```

## Guardrails

- **Every pick must pass the screen.** If you can't show a metric for a ticker (e.g. revenue exposure to the theme), it doesn't belong. Cut it.
- **Every claim must have a source.** Policy claim → congressional / agency / FT / Reuters URL. Company claim → 10-K, IR, reputable news. If you can't find a source, the claim is too speculative — cut it.
- **No fabricated numbers.** Market cap, P/E, growth, etc. — pull from the screen or write `n/a`. Never invent.
- **No price targets.** This is a thesis + watchlist, not a price-target call.
- **No "buy" / "sell" imperative language.** Use "thesis", "watchlist idea", "high-conviction long", "asymmetric setup". Never "you should buy".
- **Conviction must be honest.** A "Very High" conviction pick should be a name you'd put real money behind. Most picks should be Med or High; Very High should be rare.
- **Minimal ticker overlap across themes.** If $TICK truly fits 2 themes, pick the strongest and cross-reference, don't double-count.
- **Prefer policy-anchored catalysts** over pure narrative. "AI hype" is not a catalyst; "FDA PDUFA date [date] for [drug]" or "IRA 45X tax credit for [product]" is.
- **Always end with the DD disclaimer.** Verbatim.
- **Date everything.** Every report must include the `As-of` ISO date. Themes and policies are point-in-time.
- **For non-US / ADR picks**, verify ADR ratio and primary listing. Note 144A vs Level 1 vs Level 3 ADR. Foreign tax-withholding is a real drag — flag it.

## Companion Skills

- `daily-market-watch` (same repo) — for the current macro/policy tape that should ground the theme selection.
- `smart-money-tracker` (same repo) — to corroborate a thematic basket with institutional positioning (13F) and congressional trades.
- External: Finviz, Yahoo Finance screener, TradingView, SEC EDGAR, Bloomberg/CapIQ (if available).

## References

- `references/screening-criteria.md` — master screen thresholds, screener URLs, and per-sector overlays
- `references/sector-themes.md` — 2026–2031 policy-anchored theme catalog with key legislation, agencies, and metrics

## Example

A full template-conforming report lives at `examples/sample-report.md`. All numbers/tickers in the example are tagged `[last known]` or `[illustrative]` to signal it is a structural reference, not live data. Use the example as a golden output when iterating on this skill.
