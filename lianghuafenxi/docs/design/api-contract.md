# 当前接口契约

2026-11-12；实际入口prototype/server/gateway.mjs及worker.mjs，前缀/api/v1，同源JSON。

| 方法/路径 | 实际输入与输出 |
| --- | --- |
| GET /health | 云端ok、storage=session、mode=production、publicDataCache=d1/unbound；本地略有不同 |
| GET /config | 九项指数、存储及能力说明 |
| GET /instruments | q为1–30字符代码/名称；最多20项 |
| POST /quotes/batch | instrument_ids为1–40个ID、可选client_round_id；文本最多20000字符 |
| GET /history/{id} | interval=1d/1m；from/to有效日期，跨度最多370天；日线前复权 |
| GET /financials/{id} | A股五完整财年利润/收入/披露字段，港股暂不支持 |
| GET /valuation/{id} | 估值、当日量额，东方财富失败切腾讯；部分字段可缺失 |

ID为XSHG:六位、XSHE:六位、XHKG:五位；INDEX采用服务器白名单。美国指数报价受支持不等于历史和估值也受支持。历史默认日期由适配器处理，D1仅缓存显式有效区间。

成功包{data,meta}；失败包{error:{code,message,retryable},meta}。meta含请求标识及接收时间；来源时间可null，不能用接收时间补造。常见400输入错误、403私人接口禁用、404路由不存在、405方法不支持、413过大、422来源不支持、502来源失败。

缓存响应的data.cache及meta.cache含layer(source/d1)、stale、fetchedAt、freshUntil、warning，响应头X-Data-Cache。命中保留原获取时点。来源切换warning与过期缓存警告不同。

accounts、ledger、imports、session私人路径403 FEATURE_DISABLED。旧方案中的watchlists/events/fx/data-status、分页游标、私人云认证与服务端台账幂等API未作为当前契约实现；私人对象由浏览器操作。

