# Quantitative Finance Workflow Framework

This document defines the complete end-to-end quantitative finance workflow that A-Stockit skills should support, from strategy conception through live trading verification.

## Design Philosophy

**Core Principles:**
- **Institutional Standards:** Professional-grade quantitative finance practices throughout
- **Non-Technical User Focus:** Clean results, no technical jargon or error exposure
- **Closed-Loop Recovery:** Detect → Analyze → Fix → Verify → Continue
- **Fail-Open Semantics:** Optional features don't block critical workflow
- **Graceful Degradation:** Proceed with partial results when full data unavailable
- **Transparent Logging:** All operations logged for audit trail and reproducibility

These principles guide every stage of the workflow and every skill implementation.

---

## Workflow Stages

The complete quantitative workflow consists of seven major stages:

1. **Strategy Design & Hypothesis Formation**
2. **Data Collection & Quality Assurance**
3. **Data Cleaning & Normalization**
4. **Feature Engineering & Signal Construction**
5. **Backtesting & Performance Evaluation**
6. **Risk Management & Position Sizing**
7. **Live Trading & Monitoring**

Each stage has specific technical requirements, quality gates, and failure modes that must be addressed.

---

## Stage 1: Strategy Design & Hypothesis Formation

### Objective
Develop a falsifiable investment hypothesis with clear logic, testable predictions, and defined failure conditions.

### Technical Requirements

#### 1.1 Hypothesis Specification
- **Investment thesis:** One-sentence falsifiable statement
- **Theoretical basis:** Economic rationale, behavioral driver, or structural edge
- **Time horizon:** Holding period and rebalancing frequency
- **Universe definition:** Asset class, sector, market cap, liquidity constraints
- **Expected alpha source:** Where does the edge come from?

#### 1.2 Strategy Classification
- **Directional vs. market-neutral**
- **Momentum vs. mean-reversion vs. carry**
- **Fundamental vs. technical vs. hybrid**
- **Discretionary vs. systematic**
- **Intraday vs. daily vs. weekly rebalancing**

#### 1.3 Regime Dependency
- **Bull market behavior:** Expected performance in rising markets
- **Bear market behavior:** Expected performance in falling markets
- **High volatility behavior:** Performance during VIX spikes
- **Low volatility behavior:** Performance during calm periods
- **Regime detection:** How to identify when strategy should be active

#### 1.4 Failure Conditions
- **Invalidation triggers:** Specific conditions that would falsify the hypothesis
- **Drawdown limits:** Maximum acceptable loss before strategy review
- **Correlation breakdown:** When strategy correlation with expected factors breaks
- **Capacity constraints:** When strategy size exceeds market capacity

### Quality Gates
- [ ] Hypothesis is falsifiable (can be proven wrong)
- [ ] Theoretical basis is articulated (not just data mining)
- [ ] Time horizon matches expected signal decay
- [ ] Universe is tradeable (liquidity, access, costs)
- [ ] Failure conditions are specific and monitorable

### Common Pitfalls
- **Overfitting to historical regime:** Strategy works only in one market environment
- **Survivorship bias:** Universe selection biased by knowing which stocks survived
- **Look-ahead bias:** Using information not available at decision time
- **Data mining:** Finding patterns without economic rationale

### Skill Integration
- **Primary skill:** `analysis` (for discretionary strategies) or `strategy-design` (for systematic strategies)
- **Supporting skills:** `market-analyze`, `technical-scan`, `fundamental-context`
- **Error recovery:** `fix-everything` (automatic invocation on failures)

---

## Stage 2: Data Collection & Quality Assurance

### Objective
Acquire complete, accurate, and survivorship-bias-free data with proper point-in-time alignment.

### Technical Requirements

#### 2.1 Data Sources
- **Price data:** OHLCV with adjustment factors (splits, dividends)
- **Fundamental data:** Financial statements with as-reported and restated versions
- **Corporate actions:** Splits, dividends, mergers, delistings, suspensions
- **Market microstructure:** Bid-ask spreads, depth, trade counts (if intraday)
- **Alternative data:** News, sentiment, positioning (if applicable)

#### 2.2 Point-in-Time Correctness
- **As-of dates:** Every data point must have an as-of timestamp
- **Restatement handling:** Track when fundamentals were restated
- **Announcement dates:** Earnings, guidance, corporate actions
- **Availability lag:** Model realistic data availability (e.g., fundamentals available T+1 after announcement)

#### 2.3 Survivorship Bias Prevention
- **Delisting data:** Include stocks that were delisted during backtest period
- **Bankruptcy handling:** Model realistic recovery rates and timing
- **Suspension handling:** A-share specific: handle trading halts and limit-up/down
- **Index rebalancing:** Track when stocks entered/exited indices

#### 2.4 Data Quality Checks
- **Completeness:** No missing dates in expected range
- **Consistency:** Prices align with corporate actions
- **Outlier detection:** Flag suspicious price moves (>50% single-day moves without news)
- **Cross-validation:** Verify data against alternative sources when available

#### 2.5 A-Share Specific Requirements
- **Trading calendar:** Handle Chinese holidays, extended closures
- **Price limits:** ±10% for main board, ±20% for ChiNext/STAR
- **T+1 settlement:** Cannot sell same-day purchases
- **Auction mechanics:** Opening and closing call auctions
- **Suspension handling:** Stocks can be suspended for extended periods

### Quality Gates
- [ ] Data coverage is complete for backtest period
- [ ] Point-in-time correctness verified (no look-ahead bias)
- [ ] Survivorship bias addressed (delistings included)
- [ ] Corporate actions properly adjusted
- [ ] A-share specific mechanics captured

### Common Pitfalls
- **Using adjusted prices for signals:** Adjustments create look-ahead bias
- **Ignoring delistings:** Overstates returns by excluding failures
- **Wrong announcement dates:** Using filing date instead of announcement date
- **Missing suspensions:** Assuming liquidity when stock was actually suspended
- **Ignoring price limits:** Backtests assume fills that were impossible

### Skill Integration
- **Primary skill:** `data-sync` (for data acquisition)
- **Supporting skills:** `market-data`, `stock-data`
- **Error recovery:** `fix-everything` (automatic invocation on failures)

---

## Stage 3: Data Cleaning & Normalization

### Objective
Transform raw data into analysis-ready format with consistent scaling, outlier handling, and missing data treatment.

### Technical Requirements

#### 3.1 Price Data Cleaning
- **Split adjustment:** Backward-adjust prices for splits
- **Dividend adjustment:** Decide on total return vs. price return
- **Outlier capping:** Cap extreme returns (e.g., >3 standard deviations)
- **Missing data:** Forward-fill prices for suspended stocks (with flag)
- **Zero volume days:** Flag and handle appropriately

#### 3.2 Fundamental Data Cleaning
- **Unit consistency:** Ensure all financials in same currency and scale
- **Negative equity handling:** Flag and decide on treatment
- **Missing values:** Distinguish between zero and missing
- **Restatement handling:** Use as-reported for point-in-time correctness
- **Outlier treatment:** Winsorize extreme ratios (e.g., P/E > 1000)

#### 3.3 Normalization Methods
- **Cross-sectional:** Z-score within universe at each time point
- **Time-series:** Z-score within stock's own history
- **Rank-based:** Convert to percentile ranks (robust to outliers)
- **Industry-relative:** Normalize relative to sector/industry
- **Market-cap weighted:** Weight by liquidity/size

#### 3.4 Missing Data Strategies
- **Forward fill:** Use last known value (with staleness limit)
- **Interpolation:** Linear or spline (only for smooth series)
- **Imputation:** Use cross-sectional median/mean
- **Exclusion:** Drop observations with critical missing data
- **Flagging:** Create indicator variable for missingness

#### 3.5 A-Share Specific Cleaning
- **ST/\*ST treatment:** Flag special treatment stocks
- **Limit-up/down handling:** Flag days at price limits
- **Suspension handling:** Flag suspended periods, forward-fill prices
- **Auction price handling:** Decide whether to use opening/closing auction prices
- **Dragon-tiger list:** Clean and normalize large trader data

### Quality Gates
- [ ] No look-ahead bias in cleaning process
- [ ] Outlier treatment is consistent and documented
- [ ] Missing data strategy is appropriate for data type
- [ ] Normalization preserves cross-sectional relationships
- [ ] A-share specific issues addressed

### Common Pitfalls
- **Using future data for normalization:** Z-score using full-sample statistics
- **Inconsistent outlier treatment:** Different methods for different variables
- **Over-aggressive cleaning:** Removing legitimate extreme values
- **Ignoring missingness patterns:** Missing data is informative
- **Wrong forward-fill horizon:** Stale data treated as current

### Skill Integration
- **Primary skill:** `market-data` (for price cleaning), `fundamental-context` (for fundamental cleaning)
- **Supporting skills:** `stock-data`
- **Error recovery:** `fix-everything` (automatic invocation on failures)

---

## Stage 4: Feature Engineering & Signal Construction

### Objective
Transform cleaned data into predictive features with proper lag structure, avoiding look-ahead bias.

### Technical Requirements

#### 4.1 Feature Categories

**Price-based features:**
- **Returns:** Simple, log, excess (vs. benchmark)
- **Momentum:** 1M, 3M, 6M, 12M returns with various lag structures
- **Reversal:** Short-term (1D, 1W) mean reversion signals
- **Volatility:** Realized vol, Parkinson, Garman-Klass estimators
- **Volume:** Turnover, volume ratio, Amihud illiquidity

**Technical indicators:**
- **Trend:** Moving averages (SMA, EMA), MACD, ADX
- **Momentum oscillators:** RSI, Stochastic, Williams %R
- **Volatility bands:** Bollinger Bands, Keltner Channels
- **Volume indicators:** OBV, Chaikin Money Flow, VWAP

**Fundamental features:**
- **Valuation:** P/E, P/B, P/S, EV/EBITDA, dividend yield
- **Quality:** ROE, ROA, profit margin, asset turnover
- **Growth:** Revenue growth, earnings growth, book value growth
- **Financial health:** Debt/equity, current ratio, interest coverage

**Alternative features:**
- **Sentiment:** News sentiment, social media sentiment
- **Positioning:** Institutional ownership, short interest, insider trades
- **Macro:** Interest rates, credit spreads, commodity prices
- **Cross-asset:** FX, bonds, commodities correlations

#### 4.2 Lag Structure
- **Minimum lag:** Ensure data is available at decision time
- **Announcement lag:** Fundamentals available T+1 after announcement
- **Processing lag:** Allow time for data processing and signal generation
- **Execution lag:** Account for time between signal and execution

#### 4.3 Signal Construction
- **Single-factor signals:** One feature → one signal
- **Composite signals:** Weighted combination of multiple features
- **Conditional signals:** Regime-dependent signal construction
- **Interaction terms:** Feature combinations (e.g., momentum × volatility)
- **Non-linear transformations:** Ranks, quantiles, polynomial terms

#### 4.4 Signal Validation
- **Monotonicity:** Signal should have monotonic relationship with returns
- **Stability:** Signal should be stable across time periods
- **Turnover:** Signal should not flip too frequently (transaction costs)
- **Correlation:** Check correlation with other signals (diversification)
- **Economic rationale:** Signal should have theoretical justification

#### 4.5 A-Share Specific Features
- **Dragon-tiger list signals:** Large trader activity
- **Margin trading signals:** Margin debt, short interest
- **Northbound flow:** Foreign investor flows via Stock Connect
- **Industry rotation:** Sector momentum and mean reversion
- **Policy sensitivity:** Exposure to policy announcements

### Quality Gates
- [ ] All features have proper lag structure (no look-ahead bias)
- [ ] Features are normalized consistently
- [ ] Signal construction is documented and reproducible
- [ ] Economic rationale exists for each feature
- [ ] A-share specific features properly constructed

### Common Pitfalls
- **Using close-to-close returns:** Assumes execution at close (unrealistic)
- **Insufficient lag:** Using data not available at decision time
- **Over-engineering:** Creating hundreds of features without economic rationale
- **Ignoring transaction costs:** High-turnover signals unprofitable after costs
- **Regime instability:** Features work in one regime but fail in others

### Skill Integration
- **Primary skill:** `strategy-design` (for signal construction)
- **Supporting skills:** `market-analyze`, `technical-scan`, `fundamental-context`
- **Error recovery:** `fix-everything` (automatic invocation on failures)

---

## Stage 5: Backtesting & Performance Evaluation

### Objective
Simulate strategy performance with realistic execution assumptions and comprehensive risk metrics.

### Technical Requirements

#### 5.1 Backtest Design
- **In-sample period:** Training period for parameter optimization
- **Out-of-sample period:** Validation period (never used for optimization)
- **Walk-forward analysis:** Rolling in-sample/out-of-sample windows
- **Rebalancing frequency:** Daily, weekly, monthly
- **Universe selection:** Dynamic universe with entry/exit rules

#### 5.2 Execution Modeling
- **Order types:** Market, limit, VWAP, TWAP
- **Slippage model:** Bid-ask spread + market impact
- **Market impact:** Square-root model or linear model
- **Fill probability:** Limit orders may not fill
- **Partial fills:** Large orders may fill over multiple periods

#### 5.3 Transaction Cost Modeling
- **Commission:** Brokerage fees (A-share: ~0.03% each side)
- **Stamp duty:** A-share specific: 0.1% on sells only
- **Slippage:** Bid-ask spread + market impact
- **Opportunity cost:** Cost of not executing
- **Financing cost:** Margin interest if applicable

#### 5.4 A-Share Specific Execution Constraints
- **Price limits:** Cannot execute beyond ±10% (or ±20%) limit
- **T+1 settlement:** Cannot sell same-day purchases
- **Auction mechanics:** Opening/closing auction execution
- **Suspension handling:** Cannot trade suspended stocks
- **Liquidity constraints:** ADV-based position limits

#### 5.5 Performance Metrics

**Return metrics:**
- **Total return:** Cumulative return over period
- **Annualized return:** Geometric mean return
- **Excess return:** Return vs. benchmark
- **Alpha:** Risk-adjusted excess return
- **Information ratio:** Excess return / tracking error

**Risk metrics:**
- **Volatility:** Annualized standard deviation
- **Maximum drawdown:** Peak-to-trough decline
- **Downside deviation:** Volatility of negative returns
- **VaR / CVaR:** Value at Risk, Conditional VaR
- **Beta:** Systematic risk vs. benchmark

**Risk-adjusted metrics:**
- **Sharpe ratio:** (Return - Rf) / Volatility
- **Sortino ratio:** (Return - Rf) / Downside deviation
- **Calmar ratio:** Return / Max drawdown
- **Omega ratio:** Probability-weighted gains vs. losses

**Turnover metrics:**
- **Portfolio turnover:** Sum of buys and sells / AUM
- **Holding period:** Average time in position
- **Rebalancing frequency:** How often portfolio changes

**Capacity metrics:**
- **Strategy capacity:** Maximum AUM before alpha decay
- **Liquidity utilization:** Position size / ADV
- **Market impact:** Estimated price impact of trades

#### 5.6 Robustness Checks
- **Parameter sensitivity:** Test range of parameter values
- **Subperiod analysis:** Performance across different time periods
- **Regime analysis:** Performance in bull/bear/high vol/low vol
- **Monte Carlo:** Randomize trade order, bootstrap returns
- **Stress testing:** Performance during crisis periods

### Quality Gates
- [ ] Backtest has no look-ahead bias
- [ ] Transaction costs are realistic
- [ ] Execution constraints are modeled
- [ ] Performance metrics are comprehensive
- [ ] Robustness checks are performed

### Common Pitfalls
- **Optimizing on full sample:** Using all data for parameter selection
- **Ignoring transaction costs:** Gross returns look good, net returns negative
- **Unrealistic execution:** Assuming fills at close prices
- **Ignoring capacity:** Strategy works at small scale but not at target AUM
- **Cherry-picking periods:** Showing only favorable time periods

### Skill Integration
- **Primary skill:** `backtest-evaluator` (for retrospective evaluation)
- **Supporting skills:** `analysis-history`, `reports`
- **Error recovery:** `fix-everything` (automatic invocation on failures)

---

## Stage 6: Risk Management & Position Sizing

### Objective
Determine optimal position sizes and risk limits that balance return potential with drawdown control.

### Technical Requirements

#### 6.1 Position Sizing Methods

**Fixed sizing:**
- **Equal weight:** 1/N allocation
- **Fixed dollar:** Same dollar amount per position
- **Fixed risk:** Same risk contribution per position

**Signal-based sizing:**
- **Signal strength:** Size proportional to signal magnitude
- **Confidence-weighted:** Size based on signal confidence
- **Volatility-adjusted:** Inverse volatility weighting

**Risk-based sizing:**
- **Kelly criterion:** Optimal growth rate (often too aggressive)
- **Fractional Kelly:** Conservative Kelly (e.g., 0.25x Kelly)
- **Risk parity:** Equal risk contribution across positions
- **Maximum drawdown targeting:** Size to hit drawdown target

**Portfolio optimization:**
- **Mean-variance:** Markowitz optimization
- **Risk budgeting:** Allocate risk budget across positions
- **Black-Litterman:** Combine market equilibrium with views
- **Robust optimization:** Account for estimation error

#### 6.2 Risk Limits

**Position-level limits:**
- **Maximum position size:** % of portfolio (e.g., 5% max)
- **Maximum sector exposure:** % in any sector (e.g., 30% max)
- **Liquidity constraint:** Position size / ADV (e.g., <5% ADV)
- **Concentration limit:** Top N positions / portfolio (e.g., top 10 <50%)

**Portfolio-level limits:**
- **Gross exposure:** Sum of long + short positions
- **Net exposure:** Long - short positions
- **Leverage:** Gross exposure / NAV
- **Beta limit:** Portfolio beta vs. benchmark
- **Tracking error:** Volatility of excess returns vs. benchmark

**Risk factor limits:**
- **Factor exposure:** Exposure to style factors (value, momentum, etc.)
- **Sector exposure:** Over/underweight vs. benchmark
- **Market cap exposure:** Large/mid/small cap tilt
- **Country/region exposure:** Geographic concentration

#### 6.3 Stop-Loss & Take-Profit Rules

**Stop-loss methods:**
- **Fixed percentage:** Exit if loss exceeds X%
- **Volatility-based:** Exit if loss exceeds N × volatility
- **Technical:** Exit on support break, MA cross
- **Time-based:** Exit if no profit after N days
- **Trailing stop:** Move stop up as position profits

**Take-profit methods:**
- **Fixed target:** Exit at X% profit
- **Risk-reward ratio:** Target = stop × ratio (e.g., 2:1)
- **Volatility-based:** Target = N × volatility
- **Technical:** Exit at resistance, overbought
- **Partial profit-taking:** Scale out as position profits

**A-share specific considerations:**
- **Price limit risk:** Stop may not execute if stock limit-down
- **Suspension risk:** Cannot exit suspended positions
- **Gap risk:** Overnight gaps can bypass stops
- **T+1 constraint:** Cannot exit same-day entries

#### 6.4 Portfolio Rebalancing

**Rebalancing triggers:**
- **Time-based:** Daily, weekly, monthly
- **Threshold-based:** Rebalance when drift exceeds X%
- **Signal-based:** Rebalance when signals change
- **Volatility-based:** Rebalance more in high vol

**Rebalancing optimization:**
- **Minimize turnover:** Trade only when necessary
- **Tax optimization:** Harvest losses, defer gains
- **Transaction cost optimization:** Trade when spreads are tight
- **Market impact minimization:** Split large orders over time

### Quality Gates
- [ ] Position sizing method is appropriate for strategy
- [ ] Risk limits are clearly defined and monitorable
- [ ] Stop-loss rules account for A-share constraints
- [ ] Rebalancing frequency balances alpha capture and costs
- [ ] Portfolio construction is robust to estimation error

### Common Pitfalls
- **Over-leveraging:** Using full Kelly (too aggressive)
- **Ignoring correlations:** Concentrated risk in correlated positions
- **Tight stops:** Stopped out by noise before thesis plays out
- **No stops:** Letting losers run indefinitely
- **Ignoring transaction costs:** Rebalancing too frequently

### Skill Integration
- **Primary skill:** `decision-support` (for position sizing)
- **Supporting skills:** `strategy-design`, `market-analyze`
- **Error recovery:** `fix-everything` (automatic invocation on failures)

---

## Stage 7: Live Trading & Monitoring

### Objective
Execute strategy in live markets with real-time monitoring, performance tracking, and adaptive risk management.

### Technical Requirements

#### 7.1 Pre-Trade Checks

**Signal validation:**
- **Data freshness:** Verify data is current
- **Signal integrity:** Check for calculation errors
- **Outlier detection:** Flag unusual signals
- **Regime check:** Verify strategy should be active in current regime

**Risk checks:**
- **Position limits:** Verify trade doesn't violate limits
- **Liquidity check:** Verify sufficient liquidity
- **Correlation check:** Verify not adding concentrated risk
- **Margin check:** Verify sufficient margin/cash

**Compliance checks:**
- **Restricted list:** Verify stock is tradeable
- **Regulatory limits:** Verify compliance with regulations
- **Internal policies:** Verify compliance with firm policies

#### 7.2 Order Execution

**Order routing:**
- **Venue selection:** Choose exchange/venue
- **Order type:** Market, limit, VWAP, TWAP
- **Timing:** Intraday timing optimization
- **Urgency:** Balance speed vs. market impact

**Execution algorithms:**
- **VWAP:** Volume-weighted average price
- **TWAP:** Time-weighted average price
- **Implementation shortfall:** Minimize cost vs. arrival price
- **Adaptive:** Adjust to real-time market conditions

**A-share specific execution:**
- **Auction participation:** Opening/closing call auctions
- **Price limit handling:** Monitor for limit-up/down
- **T+1 constraint:** Plan multi-day execution if needed
- **Suspension monitoring:** Watch for suspension announcements

#### 7.3 Real-Time Monitoring

**Performance monitoring:**
- **P&L tracking:** Real-time profit/loss
- **Attribution:** Decompose P&L by source
- **Benchmark tracking:** Real-time tracking error
- **Risk metrics:** Real-time VaR, beta, exposure

**Signal monitoring:**
- **Signal decay:** Monitor if signals are weakening
- **Correlation breakdown:** Monitor if factor correlations change
- **Regime shift:** Detect regime changes
- **Anomaly detection:** Flag unusual behavior

**Risk monitoring:**
- **Position limits:** Monitor for breaches
- **Drawdown monitoring:** Track current drawdown
- **Volatility monitoring:** Track realized vs. expected vol
- **Correlation monitoring:** Track portfolio correlation structure

**Execution monitoring:**
- **Fill rates:** Monitor limit order fill rates
- **Slippage:** Track actual vs. expected slippage
- **Market impact:** Measure actual market impact
- **Timing:** Monitor execution timing vs. plan

#### 7.4 Post-Trade Analysis

**Trade-level analysis:**
- **Execution quality:** Actual vs. benchmark (VWAP, arrival)
- **Slippage attribution:** Spread, impact, timing, opportunity cost
- **Fill analysis:** Fill rates, partial fills, cancellations

**Position-level analysis:**
- **Holding period:** Actual vs. expected
- **P&L attribution:** Price, carry, roll, other
- **Risk contribution:** Realized risk vs. expected

**Portfolio-level analysis:**
- **Performance attribution:** Factor, sector, stock-specific
- **Risk attribution:** Factor risk, specific risk, interaction
- **Turnover analysis:** Actual vs. expected turnover
- **Cost analysis:** Transaction costs vs. budget

#### 7.5 Adaptive Risk Management

**Dynamic position sizing:**
- **Volatility scaling:** Reduce size in high vol
- **Drawdown scaling:** Reduce size after losses
- **Regime-based scaling:** Adjust size by regime
- **Signal strength scaling:** Adjust size by conviction

**Dynamic stop-loss:**
- **Volatility-adjusted stops:** Widen stops in high vol
- **Time-decay stops:** Tighten stops over time
- **Correlation-adjusted stops:** Adjust for portfolio correlation

**Portfolio rebalancing:**
- **Drift management:** Rebalance when drift exceeds threshold
- **Risk rebalancing:** Rebalance when risk exceeds budget
- **Opportunistic rebalancing:** Rebalance when costs are low

#### 7.6 Incident Response

**Signal failures:**
- **Data errors:** Detect and correct data errors
- **Calculation errors:** Detect and correct signal errors
- **Regime shifts:** Detect regime changes and adapt

**Execution failures:**
- **Failed trades:** Handle failed executions
- **Partial fills:** Manage partial fill risk
- **Price limit hits:** Handle limit-up/down situations
- **Suspensions:** Handle unexpected suspensions

**Risk breaches:**
- **Position limit breaches:** Reduce positions
- **Drawdown breaches:** Reduce risk or halt trading
- **Margin calls:** Manage margin requirements

### Quality Gates
- [ ] Pre-trade checks are comprehensive and automated
- [ ] Execution algorithms are appropriate for strategy
- [ ] Real-time monitoring covers all critical metrics
- [ ] Post-trade analysis is systematic and actionable
- [ ] Incident response procedures are documented

### Common Pitfalls
- **Insufficient pre-trade checks:** Executing bad signals
- **Poor execution timing:** High market impact
- **Inadequate monitoring:** Missing regime shifts or signal decay
- **No incident response plan:** Panic during failures
- **Ignoring post-trade analysis:** Not learning from execution

### Skill Integration
- **Primary skill:** `paper-trading` (for simulated live trading)
- **Supporting skills:** `decision-support`, `strategy-design`, `session-status`
- **Error recovery:** `fix-everything` (automatic invocation on failures)

---

## Stage 7.6: Error Recovery & Workflow Continuity

### Objective
Ensure workflow continues seamlessly through autonomous error recovery, minimizing user intervention and maintaining professional user experience.

### Technical Requirements

#### 7.6.1 Autonomous Recovery System
- **Closed-loop recovery:** Detect → Analyze → Fix → Verify → Continue
- **Progressive recovery strategies:** 8-tier system from retry to simplified approach
- **Transparent logging:** All recovery attempts logged for audit trail
- **User escalation:** Only when all recovery strategies exhausted

#### 7.6.2 Recovery Strategy Tiers
1. **Retry with Backoff:** Transient failures (network, rate limits)
2. **Alternative Source:** Primary data source unavailable
3. **Graceful Degradation:** Proceed with partial results
4. **Data Reconstruction:** Rebuild from available components
5. **Workflow Rerouting:** Alternative skill composition path
6. **Configuration Auto-Fix:** Detect and repair config issues
7. **Dependency Auto-Install:** Missing dependencies installed automatically
8. **Simplified Approach:** Reduce complexity to essential functionality

#### 7.6.3 Fail-Open vs Fail-Closed
- **Fail-open features:** Notifications, enrichments, optional analytics
- **Fail-closed features:** Core data access, critical calculations, position tracking
- **Status indicators:** ok/partial/not_supported/stale/error
- **Degradation transparency:** Users informed what degraded, what remains trustworthy

#### 7.6.4 User Experience Principles
- **Non-technical users:** Never expose technical errors or stack traces
- **Clean results:** Users see successful outcomes when recovery succeeds
- **Clear escalation:** When escalation needed, provide actionable questions
- **Context preservation:** Recovery maintains workflow state and context

### Quality Gates
- [ ] All recoverable errors have defined recovery strategies
- [ ] Recovery attempts are logged transparently
- [ ] User escalation only when necessary
- [ ] Workflow state preserved through recovery
- [ ] Status indicators accurately reflect degradation

### Common Pitfalls
- **Exposing technical errors:** Showing stack traces to non-technical users
- **Silent failures:** Hiding errors without attempting recovery
- **Excessive retries:** Retry loops without backoff or limits
- **Lost context:** Recovery discards workflow state
- **Unclear escalation:** Users don't know what action to take

### Skill Integration
- **Primary skill:** `fix-everything` (meta-skill for autonomous recovery)
- **Supporting skills:** All skills integrate with fix-everything
- **Invocation:** Automatic on any skill failure

---

## Cross-Stage Integration

### Data Flow
```
Strategy Design → Data Collection → Data Cleaning → Feature Engineering
                                                            ↓
Live Trading ← Risk Management ← Backtesting ← Signal Construction
     ↓
Monitoring & Analysis → Performance Evaluation → Strategy Refinement
```

### Feedback Loops
- **Backtest → Strategy Design:** Refine hypothesis based on backtest results
- **Live Trading → Risk Management:** Adjust risk limits based on realized performance
- **Post-Trade Analysis → Execution:** Improve execution based on slippage analysis
- **Performance Evaluation → Feature Engineering:** Refine features based on live performance

### Quality Assurance Checkpoints
1. **After Strategy Design:** Peer review of hypothesis and economic rationale
2. **After Data Collection:** Data quality audit
3. **After Feature Engineering:** Signal validation and economic rationale check
4. **After Backtesting:** Robustness checks and out-of-sample validation
5. **Before Live Trading:** Pre-production checklist and paper trading
6. **During Live Trading:** Daily performance and risk monitoring
7. **Monthly Review:** Comprehensive performance attribution and strategy review

---

## Skill Mapping to Workflow Stages

| Workflow Stage | Primary Skills | Supporting Skills |
|---|---|---|
| Strategy Design | `analysis`, `strategy-design` | `market-analyze`, `technical-scan` |
| Data Collection | `data-sync` | `market-data`, `stock-data` |
| Data Cleaning | `market-data`, `fundamental-context` | `stock-data` |
| Feature Engineering | `strategy-design` | `market-analyze`, `technical-scan` |
| Backtesting | `backtest-evaluator` | `analysis-history`, `reports` |
| Risk Management | `decision-support` | `strategy-design`, `market-analyze` |
| Live Trading | `paper-trading` | `decision-support`, `strategy-design`, `session-status` |

---

## Next Steps

This framework should be integrated into individual skill contracts to provide:
1. **Detailed technical specifications** for each workflow stage
2. **Quality gates and checklists** to ensure rigor
3. **Common pitfalls and how to avoid them**
4. **A-share specific considerations** throughout
5. **Clear handoffs between stages** and skills
