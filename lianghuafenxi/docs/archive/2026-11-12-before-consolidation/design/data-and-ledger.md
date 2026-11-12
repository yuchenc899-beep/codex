# 数据模型与持仓台账

版本 v0.1，设计评审稿。主文：[详细设计](../plans/2026-11-11-quant-system-detailed-design.md)。本节模型默认存于会话快照；只有选择 D1 时才建表。

## 1. 通用类型与版本

- ID：UUID；证券 ID 使用 `XSHG:600905`、`XSHE:000001`、`XHKG:00762`，代码始终字符串。指数分配规范 ID，并通过来源映射表连接，不能用名称猜测指数。
- 金额/数量/价格/汇率：规范十进制字符串，如 `"100.00"`。禁止将浮点运算结果写回台账。数量精度由证券属性约束，成交价允许来源支持的精度，结算金额按币种精度舍入。默认候选 `HALF_UP`，保留未舍入中间值及规则版本。
- 时间：发生时间为带时区 ISO 8601，内部 UTC；`trade_date` 为交易所本地日期。另存录入时间、披露时间和源端时间，不混用。
- 通用私有对象：`id, owner_id, revision, created_at, updated_at`。默认模式 owner 为当前会话空间；D1 owner 由服务端身份生成。
- 指标值：`{value: string|null, status, reason_codes:[], input_versions:{}, as_of}`。status 为 `valid/partial/missing/invalid/not_applicable`。
- 快照：`schema_version, dataset_id, revision, exported_at, checksum, payload`。校验和用于检测文件损坏，不作为可信签名或权限凭据。

## 2. 实体字段与关系

下表列出领域所需字段；私有对象均具备上一节通用字段。D1 物理表还须将 owner 纳入唯一键和关联校验，防止跨空间引用。

| 实体 | 核心字段 | 唯一性/索引 |
| --- | --- | --- |
| issuers | name, domicile, listing_structure, source_ref | id；发行人关联需证据 |
| instruments | exchange, code, market, type, name, currency, issuer_id, listed_on, lot_size, quantity_scale | exchange+code；name 搜索辅助 |
| source_symbols | instrument_id, provider, provider_symbol, effective_from/to | provider+symbol+有效期 |
| classifications | instrument_id, taxonomy, level, industry_code, source, as_of, override, evidence_ref | 每体系各级一个生效主分类 |
| ownership_evidence | issuer_id, central_control, local_control, red_chip, controller_name, effective_on, source_url, checked_at | issuer+来源+时点；各布尔允许 unknown |
| watchlists | name, archived_at | owner+id |
| watchlist_members | watchlist_id, instrument_id, added_at, removed_at, rank | owner+list+instrument 当前成员唯一 |
| saved_views | name, filters_json, columns_json, sort_json, group_by, config_version | owner+id |
| notes | instrument_id, thesis, observation_conditions, body, revision | owner+instrument+id |
| accounts | name, base_currency, cost_method, ledger_revision, active_generation | owner+id |
| ledger_events | account_id, instrument_id, type, occurred_at, sequence, qty, price, currency, fees_json, cash_json, payload_json, supersedes_id, voids_id, batch_id | owner+id；account+occurred_at+sequence |
| position_projections | account_id, instrument_id, generation, qty, book_cost, realized_pnl, cost_status, through_event_id | owner+account+instrument+generation |
| import_batches | file_hash, schema, state, manifest_hash, total_rows, valid_rows, issues_json, expected_revision | owner+file_hash+导入策略 |
| alerts | scope_type/id, metric, operator, threshold, confirmation, cooldown_s, once, enabled, rule_revision | owner+id |
| alert_occurrences | alert_id, instrument_id, trigger_key, source_time, observed_at, evidence_json, read_at | owner+trigger_key |
| events | instrument_id, type, event_date, date_status, announcement_at, source_ref | provider+source_event_id |
| research_reports | report_date, generated_at, input_versions, coverage_json, content | owner+id |
| mutation_receipts | idempotency_key, request_hash, state, result_json, committed_revision | owner+幂等键 |

公开取数模型不要求全部持久化：

| 对象 | 字段 |
| --- | --- |
| Quote | instrument_id, last, prev_close, open, high, low, change_pct, volume, volume_unit, amount, amount_currency, source_time, received_at, session, quality, provider |
| Bar | instrument_id, date/time, interval, OHLCV, adjustment, factor_version, is_final, provider, coverage |
| FinancialYear | fiscal_end, disclosed_at, report_kind, parent_profit, revenue, currency, multiplier, source_ref, revision |
| FX | pair, rate, rate_type, source_time, received_at, provider；缺少源时间不能冒充即时汇率 |
| Calendar | exchange, date, sessions[], timezone, status, source_ref, verified_at |
| Analysis | instrument_id, indicators, research_label, portfolio_constraints, evidence[], missing[], rule_version, input_versions |

账户之间内部转移使用成对事件和共同 `transfer_id`；现金流水、分红、公司行为采用 ledger_events 的有类型 payload，避免同一经济事件在多张表重复记账。财报原始字段留来源映射，不将不同利润口径合并成一个值。

行业：来源分类与手动覆盖分别保存；有效分类优先手动覆盖，取消后恢复来源值。汇总只使用一套指定体系的一个一级主行业。概念标签多值但不参与行业金额相加。ETF 独立归基金类别，缺行业归“待分类”。A/H 按证券显示，按发行人汇总时金额仍只加每条实际持仓一次。

## 3. 事件类型与录入校验

| 类型 | 必填参数 | 处理 |
| --- | --- | --- |
| OPENING | 时间、证券、数量、确认总成本或均价、币种、基准来源 | 建立期初；未知历史已实现收益留空 |
| BUY / SELL | 账户、时间、证券、数量、成交价、币种、费用状态 | 增减数量与成本；SELL 不得超过该时点可用账面持仓 |
| CLOSE | 同 SELL，数量从当前版本计算 | 提交时再核对版本，不能用过期数量清仓 |
| CASH_IN / CASH_OUT | 时间、金额、币种、外部/内部性质 | 组合收益现金流基础；不能伪装利润 |
| DIVIDEND | 权益所属证券、到账时间、税前额、税费、净额、币种 | 检查税前−税费=净额；除息日不代替到账日 |
| TRANSFER_IN/OUT | 转移数量、转移成本、对应账户或外部来源 | 内部合并抵消；外部视为资产流入/出 |
| SPLIT / BONUS | 生效日、比例、前后数量、成本处理依据 | 保留总成本或按明确依据调整 |
| CORRECT / VOID | 原记录、替代内容或撤销原因 | 不改写原事件；重新回放受影响序列 |

费用用 `status=known/unknown` 和分项佣金、税费、其他费用；明确 0 才视为零费用。未知费用允许保存研究台账，但相关净收益为 partial，不显示精确已对账。成交币种必须符合证券或明确兑换事件；费用异币种需汇率依据。

同一发生时间使用 account 内稳定 sequence 决定先后，允许用户核对同日顺序。原事件引用必须同 owner/account，无循环更正、不能重复撤销。更正链仅末端有效，撤销更正不能靠覆盖字段处理。现金是否允许负数由账户设置；持仓账本默认不支持卖空。实际下单、交易所撮合及券商自动交易不在范围内。

## 4. 核算与更正

令数量 Q、总账面成本 C；含费用买入 q、p、f：`Q'=Q+q；C'=C+q*p+f`。卖出前平均成本 `a=C/Q`，卖出释放 `r=q*a`，`realized=q*p-sell_fees-r`，`Q'=Q-q；C'=C-r`。完全清仓最后一笔释放全部剩余成本，避免累计舍入尾差。每笔展示本金、费用、释放成本和净收入。

例（纯设计样例）：100 股、总成本 1,000；再买 100 股，成交 12，费用 5 → 200 股、总成本 2,205、均价 11.025。卖出 50 股、成交 13、费用 5 → 收入净额 645、释放成本 551.25、已实现 93.75；余 150 股、成本 1,653.75。报价 12 时浮盈 146.25。费用已纳入上述收益，收益拆解中不得再扣一次。

期初只有券商成本价时，将其记录为“确认基准成本”，不倒推过去成交、分红或已实现利润。券商可能使用摊薄成本等不同口径，保留来源原值并列差异；默认候选平均成本未经核对不得声称完全一致。

更正/补录先在临时投影回放，显示真实记录的更正差异；若中途负持仓则拒绝提交并返回首个冲突事件。回放成功才替换有效投影。期间用户看到旧完整版本或新完整版本，不显示半更新账户。

默认会话：Web Worker 生成新状态 → 序列化到临时 sessionStorage 键并校验 → 切换当前快照指针 → 发布新 revision。容量不足保留原快照和当前工作结果，清楚报告未持久到会话存储。该机制只保证应用提交步骤完整，不承诺浏览器故障后的持久性。

## 5. 可选 D1 的一致性

使用参数化 SQL 和 `DB.batch()` 提交固定批次，不设计跨网络请求保持的 SQL 事务。按账户 revision 做乐观并发，先读取当前状态、计算校验，再提交带版本条件的批次。D1 批次语义需按当前 SDK 在实施时做原子性及回滚实验。[D1 API](https://developers.cloudflare.com/d1/worker-api/d1-database/)

并发保护的具体要求：

1. 为提交生成 mutation_id；相同幂等键相同规范化请求摘要返回原结果，不同摘要返回 409。
2. 批次首条 CAS 更新账户：revision 必须等于 expected_revision，同时设置 last_mutation_id。
3. 后续事件、投影、审计和回执写入均以“新 revision 且 last_mutation_id 等于本次 ID”为条件；CAS 未成功时全部为无操作。
4. 检查首条变更行数；0 返回 VERSION_CONFLICT，不报告成功。任一 SQL 错误须整批回滚。
5. 大回放分块写入不可见 generation，最终复核基础 revision 后原子切换 active_generation；基础版本已变则重算。未完成 generation 可清理，不作为有效持仓读取。

幂等回执、投影与事件必须同批提交，不能先发成功再异步补记。限定每次调用不超过 40 条 SQL、每 SQL 不超过 90 个绑定参数，为平台限制留空间；具体分页大小由字段数确定。长历史回放走分块作业，不让一个 Free Worker 请求承担无限事件数。

## 6. 导入、导出与数据寿命

流程：浏览器选文件 → 本地解析 → 证券规范化 → 差异预览（新增、重复、冲突、无法识别、历史日期）→ 用户选择处理 → 一次发布新数据集版本。文件原件默认不传云端。证券取数只发送所需代码，不发送数量、成本或备注。

历史清单的整理日、报价日和持仓基准日分开；不能将 2026-11-11 文件名当作当天资产。原已确认持仓基准保持优先，冲突逐项展示，不自动覆盖。

导入批次以文件摘要+导入类型+策略识别，重复预览不产生新事件。D1 大批量先 staging、分块校验行数及 manifest，最后切换数据集指针；中途中断不产生部分有效替换。删除自选不删除交易；删除有账本的账户改为归档。

JSON 为完整可恢复格式，含版本、字段和事件引用；CSV 为可读明细，导出时防范表格公式注入并附币种/单位/时间。仅靠 CSV 列表不承诺恢复审计链。导入限制候选：单文件 5 MB、10,000 事件；超限给出分批说明，后续实测调整，不静默截断。
