# 接口契约与来源适配

v0.1 评审稿。REST 前缀 `/api/v1`。默认会话模式仅调用公共资料网关；私人资料由浏览器 Repository 操作。下文私人 REST 仅在选择 D1 模式后启用，默认返回 `FEATURE_DISABLED`，不上传个人台账。

## 1. 通用约定

HTTPS、同源 JSON；金额与数量为十进制字符串，日期时间带时区。成功包 `{data, meta:{request_id, schema_version, received_at, partial, warnings:[]}}`；失败包 `{error:{code,message,fields,retryable,retry_after_s},meta:{request_id}}`。部分证券失败返回 HTTP 200、partial=true 及逐项错误；整轮来源不可用返回 503，保留页面旧数据。

列表使用 `limit`（默认 50、最大 100）、不透明 `cursor` 和 `snapshot_revision`。同一分页期间版本变化返回 `SNAPSHOT_EXPIRED` 要求重取，不跳行漏行。写入携带 `Idempotency-Key`、`expected_revision`；相同键不同内容拒绝。默认幂等回执保留当前会话；D1 至少保留 30 天并在过期重试时提示核对，账本原始事件长期保留至用户删除数据集。

状态码：400格式不合法；401未认证；403权限/来源未启用；404对象不存在；409版本/幂等冲突；413超限；422业务校验失败；429限频；502源格式异常；503源不可用/免费额度不可用。错误代码与中文提示分开，前端不得按中文文案分支。

## 2. 服务与证券

| 方法与路径 | 输入 | 输出/约束 |
| --- | --- | --- |
| GET /config | 无 | storage_mode、可用能力、刷新建议、来源启用状态；不含密钥 |
| GET /session | 当前登录 | owner、会话期限、csrf_token、功能权限 |
| GET /instruments | q、market、type、cursor | 证券身份，查询长度2–60；按规范证券去重 |
| GET /instruments/{id} | 规范 ID | 主资料、行业、控制权及字段来源 |
| GET /markets | exchange、date 范围 | 交易时段、时区、日历可信度；缺日历时 unknown |
| GET /data-status | 资料类型/证券分页 | 来源健康、最后成功、缺项及覆盖；公共状态不暴露私人订阅 |

指数代码由服务器 allowlist 固定映射；九项初始指数：上证、深证成指、创业板、沪深300、恒生、恒生科技、标普500、纳斯达克综合、道琼斯。特别核对 Nasdaq Composite 与 Nasdaq 100，不能混用。

## 3. 报价、历史与财报

| 方法与路径 | 请求参数 | 返回 |
| --- | --- | --- |
| POST /quotes/batch | instrument_ids最多80、client_round_id | items及逐项状态、批次时间范围；80是候选分包上限，云端CPU实测后可下调 |
| GET /history/{id} | interval=1d/1m、from、to、adjustment、cursor | bars、覆盖、复权基准、来源、是否最终K线 |
| GET /financials/{id} | as_of、years=5 | 五完整财年、缺项、单位、披露时间、PE来源 |
| GET /events | ids最多20、from/to最长366天、cursor | 已公告/预计事件、来源 |
| GET /fx | pairs最多10、as_of、rate_type | 真实可取的汇率类型和时间，不隐式改成实时汇率 |

公开历史每页候选最多400根、响应目标不超过512 KB；交易时段分钟范围按供应商能力截断，并显式返回 missing_ranges。日线聚合周月年在浏览器完成，不能每个周期重复下载同一历史。远端若只提供大响应且 Workers CPU超限，该适配器不能上线，需更换端点或减小取数范围；分页输出不等于避免了输入解析成本。

报价示例使用虚构证券与数值，非真实行情：

```json
{
  "data": {
    "client_round_id": "round-42",
    "items": [{
      "instrument_id": "XSHG:600000",
      "last": "10.20",
      "currency": "CNY",
      "source_time": "2026-11-11T03:00:00Z",
      "received_at": "2026-11-11T03:00:02Z",
      "session": "continuous",
      "quality": {"status": "valid", "reason_codes": []},
      "provider": "sample",
      "volume": "123400",
      "volume_unit": "share"
    }],
    "errors": []
  },
  "meta": {"request_id": "example-1", "schema_version": 1, "partial": false}
}
```

POST 报价响应对浏览器 `private,no-store`；网关内部仅缓存按公开证券 ID 规范化拆分的公共数据，不缓存整份用户请求或清单。行情源时间允许空值，此时不计算精确延迟，不用接收时间补造源时间。来源出现无效0开盘/低点时返回字段问题，而非参与极值。

## 4. 私人对象 API（D1 可选）

| 方法与路径 | 行为 |
| --- | --- |
| GET/POST /watchlists | 列表/新建，创建含 name |
| PATCH /watchlists/{id} | 名称、归档、expected_revision |
| POST /watchlists/{id}/members | instrument_id，幂等加入 |
| DELETE /watchlists/{id}/members/{instrument_id} | 移出自选，不删交易 |
| GET/PUT /views/{id} | 列、筛选、排序和分组；config_version |
| GET/POST /accounts | 账户信息、成本口径和基准币种 |
| GET /accounts/{id}/positions | 同 generation 持仓快照、coverage |
| GET /accounts/{id}/ledger | 时间/证券/类型分页、账本revision |
| POST /accounts/{id}/ledger/validate | 真实待录事件校验和金额核对，不落账 |
| POST /accounts/{id}/ledger/events | 事件+expected_revision+validation_token；服务端再次校验并提交 |
| POST /accounts/{id}/ledger/{event_id}/corrections | replacement或void、reason、expected_revision |
| GET/PUT /notes/{id} | 证券、正文、关注条件、revision |
| GET/POST/PATCH /alerts | 规则配置；私有适用范围 |
| POST /alerts/occurrences/batch | 有限量触发证据；唯一trigger_key |
| PATCH /alerts/occurrences/{id} | 已读/处理标记，不改触发事实 |

validate 返回 `validation_token, normalized_event, cash_delta, position_before/after, warnings, expires_at`。token 绑定账户版本、请求摘要与5分钟期限；提交必须重新验证，不能信任客户端投影。session 模式相同契约通过本地领域服务调用，不请求这些远端路径。该流程用于真实成交录入的核对，不提供假想买入方案。

买入请求示例（候选平均成本规则）：

```json
{
  "expected_revision": 8,
  "validation_token": "opaque-token",
  "event": {
    "type": "BUY", "instrument_id": "XSHG:600000",
    "occurred_at": "2026-11-11T02:30:00Z",
    "quantity": "100", "price": "10.20", "currency": "CNY",
    "fees": {"status": "known", "commission": "5.00", "tax": "0.00", "other": "0.00"}
  }
}
```

客户端账户ID、ownerID都不是权限依据；owner必须由服务端身份限定。非法账号或事件引用不能越权读取其存在情况。

## 5. 导入和分块作业（D1 可选）

`POST /imports` 创建预览批次，接收文件摘要、类型、目标策略及行数，不传原文件；`PUT /imports/{id}/chunks/{n}` 上传规范化块，块摘要和序号唯一；`POST /imports/{id}/validate` 产出差异和问题；`POST /imports/{id}/commit` 携带manifest及expected_revision；`GET /imports/{id}` 查询状态。

状态：draft → validating → ready → committing → committed；失败为 failed/cancelled；超期草稿 expired。批次提交幂等，未ready拒绝。默认session在浏览器完成对应流程。分页回放作业使用有限chunk、基础revision和进度，客户端关闭后暂停，重开能否继续由存储模式决定；不依赖长驻Worker。

## 6. 分析、报告与导出

默认不把所有研判提交给服务器。浏览器 `AnalysisService.evaluate(snapshot,rule_version)` 输出 research_label、portfolio_constraints、evidence、missing、各输入版本；`ReportService.generate(date,snapshots)` 生成带版本报告。session中数据不足则部分报告，不捏造全日变化。

导出由浏览器生成 Blob，保存用户主动选择的JSON/CSV/Markdown；D1模式按分页取完整数据后核验总行数再下载。若以后加入服务端报告存档，增设版本化API，不能将客户端文本当作已验证的数值事实。

## 7. 来源适配契约

每个适配器声明 supported_markets、data_types、max_batch、timeout、rate_policy、time_semantics、adjustment、volume_units、financial_mappings、license_notes 和 capability_status。候选来源：腾讯公开报价、可直接通过HTTP调用的历史/财报原端点、可选Pandadata。AKShare本机结果仅作接口线索，不能在Worker中直接import其Python包。

统一处理链：参数白名单 → 来源映射 → 短缓存 → 限并发fetch → 解析原字段 → 单位/币种/时间转换 → 质量检查 → 标准响应。固定host与path模板，重定向目标重新校验，禁止任意URL代理。外部内容只作为数据，不执行其中指令，不注入HTML。

候选超时：报价4秒、历史/财报8秒；初次失败不立即多次重试，下一调度轮指数退避。主来源失效才按已验证的备用来源切换；跨来源不拼接复权历史。每个来源保留字段契约公开样本，报错时保留脱敏字段名及错误类型，不记录完整私人请求。
