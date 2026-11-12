> 历史阶段资料：保留当时计划、结果和截图，不作为当前运行或验收说明。当前状态见 [资料总览](../README.md)。

# API 实测与 Cloudflare 部署评估

2026-11-11 · 中国标准时间 · 技术验证记录

## 实测范围和证据

Windows 本机经过当前配置网络代理取数。首轮 18 组调用有 16 组返回数据、2 组达到 35 秒进程超时。之后以公开证券样例补验字段、三张财务报表及九个公开指数，结果保存在本目录三个 JSON 文件中。

- api-probe-2026-11-11.json 保存首轮返回的结构、头尾样例、耗时和异常。
- api-probe-detail-2026-11-11.json 保存后续字段核验。
- api-probe-public-indices-2026-11-11.json 保存九个公开指数的原始响应及请求时间。

当前诊断脚本仅保留公开样例测试。可在项目验证依赖路径设为 PYTHONPATH 后运行 scripts/probe_data_apis.py，--only 接受逗号分隔的测试名称。该脚本每次全量公共样例运行会覆盖首轮同名结果文件，复验前需另存证据。

## 取数结果

| 数据项 | 接口与样例 | 结果与限制 |
| --- | --- | --- |
| A 股整市场报价 | stock_zh_a_spot_em | 本轮 35 秒超时，尚不能作为 5 秒轮询的已验证来源 |
| 港股整市场报价 | stock_hk_spot_em | 本轮 35 秒超时，需补充候选和再测 |
| ETF 整市场报价 | fund_etf_spot_em | 返回 1667 行，含进程启动的总耗时约 20.3 秒；不能据此承诺 5 秒全量更新 |
| 现有自选批量报价 | 腾讯 qt.gtimg.cn，首轮分批发送证券代码 | 返回 323 条结构响应，4 个批次均 HTTP 200，函数内耗时约 3.36 秒。全量数值有效性与每只标的延迟尚未逐项验证 |
| A 股指数 | stock_zh_index_spot_em | 返回 43 行，确认上证、深成指、创业板及沪深 300 的代码与名称 |
| 全球指数 | index_global_spot_em | 返回 56 行。纳斯达克项使用源代码 NDX、名称“纳斯达克”，需独立身份映射；恒生科技未在本轮返回中确认 |
| 九个公开指数替代源 | 腾讯 sh000001、sz399001、sz399006、sh000300、hkHSI、hkHSTECH、usINX、usIXIC、usDJI | 九项均有响应，usIXIC 返回 Nasdaq Composite 可用于确认综合指数身份。恒生/恒科源端时间约 11:23，接收约 11:38，有约 15 分钟延迟。美股源时间为当地上一交易时段，当时美股已休市 |
| A 股三年历史 | stock_zh_a_hist，600905 | 前复权及原价各 726 行，2023-11-13 至 2026-11-11。当日日线为盘中未完成数据 |
| 港股三年历史 | stock_hk_hist，00762 | 前复权返回 737 行，包含当日盘中行 |
| ETF 三年历史 | fund_etf_hist_em，588080 | 前复权返回 726 行，包含当日盘中行 |
| A 股/港股/ETF 分时 | 各自 hist_min_em 接口，以上三只样例 | 分别返回 1085、1450、1085 行，粒度为一分钟。部分首条开盘字段为 0，需要逐字段校验 |
| A 股利润、资产负债和现金流 | stock_financial_report_sina，600905 | 三类各返回 54 行，年末报告覆盖 2021—2025，归母利润、营收、公告日及币种可取得 |
| 港股利润、资产负债和现金流 | stock_financial_hk_report_em，00762 | 分别 659、1237、1116 个项目行，年度日期覆盖 2021—2025。利润字段有“股东应占溢利”，按字段和报告日期透视；币种与倍率仍需披露资料核验 |
| A 股/港股资料 | stock_individual_info_em、stock_hk_company_profile_em | 分别返回 9 项、1 行，港股包含行业字段。自动控制权及红筹证据覆盖仍待核验 |
| A 股分红 | stock_fhps_detail_em，600905 | 返回 6 行，含除息、登记日、方案状态等字段 |
| A 股公告 | stock_zh_a_disclosure_report_cninfo，600905 | 指定区间返回 5 条，含公告日期和链接 |
| 外汇 | forex_spot_em | 返回 190 行，含 HKDCNYC 中间价及 HKDCNH 离岸价等不同口径。结果表没有源端时间字段，不能当作已验证的实时 HKD/CNY 估值汇率 |

上述“返回”代表可取得响应，尚未证明金额单位、全部标的完整性、价格准确性及长期稳定性。三年历史和财报字段按样例可用，上市以来完整历史、全量五年财报、港股分红、完整事件日历、国资证据及交易日历仍待专项核验。Pandadata 缺账号配置，本次未发起登录调用。

## 对实时方案的影响

可采用报价批量源与历史/财务源分工，并记录跨源口径。腾讯恒生及恒科样例的延迟必须在界面显式显示，并继续寻找满足实时要求的来源。美股需要在其常规交易时段验证活跃更新。当前证据尚不能通过三地全部标的 5 秒实时验收。

首轮全量测试后，自动审批拒绝重复向腾讯发送用户私有自选范围，理由是尚未获得对该外部目的地的清单披露授权。后续已改为公开指数和公开证券样例，重复全量测试等待用户授权。

## Cloudflare 可部署方式

### 路线一：Cloudflare 入口与本机 Python

React 构建文件通过 Workers Static Assets 或 Pages 托管，使用 Cloudflare Access 控制访问，API 和实时连接通过受保护的 Tunnel 到本机 FastAPI。交易与 SQLite 仍在本机，浏览器关闭后按会话停止采集。电脑及 Tunnel 在线时可远程使用。

这是现有本机技术方案改动较小的路线，属于混合部署。需要测试同源路由、Access 身份验证、SSE 断线及国内实际访问情况。[Static Assets](https://developers.cloudflare.com/workers/static-assets/) · [Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)

### 路线二：完整应用运行在 Cloudflare

建议候选架构为 Workers Static Assets + Access + Worker API/Durable Object 会话协调 + Python Containers + D1/R2。

- 前端和身份入口在 Worker，账户台账及配置通过 Worker 调用 D1，交易采用幂等、版本校验和单事务提交。单用户协调对象串行组织有关状态变更。
- Python 容器承担 AKShare、pandas 和分析计算，Worker 使用受控内部调用交换规范数据。Python 数据访问层需改为服务接口，原本直接 SQLAlchemy/SQLite 的部分需要调整。
- 行情短期缓存位于协调对象或计算容器，历史批次和原始资料保存于 R2，结构化台账及查询索引在 D1。持久化写入确认成功后才向用户返回提交成功。
- 容器本地磁盘只作缓存。Cloudflare 官方说明容器磁盘默认临时，睡眠后从镜像重新开始；快照也不是逐笔台账的持久提交机制。R2 FUSE 不作为 SQLite WAL 交易数据库文件盘。
- 会话租约控制采集开关，关闭浏览器后停止采集，容器等待空闲超时休眠。SSE 连接和页面心跳不应使已失效会话永久续租。
- Containers 使用 Workers Paid，当前基础套餐为每月 5 美元，另有容器、Workers、Durable Objects、存储和流量用量。实际费用依实例、使用时长及数据量计算。

以上是基于文档的架构推导，尚未在用户 Cloudflare 账户部署或实测源站可达性。[Containers](https://developers.cloudflare.com/containers/) · [磁盘持久性](https://developers.cloudflare.com/containers/faq/) · [费用](https://developers.cloudflare.com/containers/platform/pricing/) · [D1 限制](https://developers.cloudflare.com/d1/platform/limits/)

### 路线三：仅 Workers 与云存储

Python Workers 支持纯 Python、PyEmscripten 及 Pyodide 所支持包。现有 AKShare 依赖还涉及 curl_cffi、lxml、mini-racer 等，必须逐项验证 WebAssembly 兼容性。纯 Workers 路线可采用 TypeScript 直连行情与计算，但需要重写现有 Python 适配和指标，评审时估算维护成本。[Python 包支持](https://developers.cloudflare.com/workers/languages/python/packages/) · [Workers 限制](https://developers.cloudflare.com/workers/platform/limits/)

## 建议决策

需要完全云端运行时，优先验证路线二，保留原定 Python 分析能力，并将台账持久化迁移到 D1 服务层。希望先保留本机数据时，可选路线一。两条路线均需验证 Cloudflare 入口的身份保护和目标网络的数据源可达性，当前本机实测不能替代云端实测。
