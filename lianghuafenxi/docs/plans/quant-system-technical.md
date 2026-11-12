# 宇辰看板技术方案

2026-11-12 当前架构。[原稿](../archive/README.md)中的Python主服务、SQLite私人云台账和Containers路线不作为当前实施要求。

## 架构

浏览器React → 同源 /api/v1 → Cloudflare Worker → 公开数据适配器。历史/财报优先读取本人D1缓存；静态资源由Static Assets提供。个人台账在浏览器中处理。

| 层 | 代码入口 |
| --- | --- |
| 正式应用 | prototype/src/live/RealApp.tsx |
| 表格/弹窗/图表 | SecurityTables.tsx、ResearchDialog.tsx、ResearchMetrics.tsx |
| 账本/计算 | prototype/src/core/engine.mjs、table-query.mjs、research.mjs |
| 研究加载 | research-packet.mjs、research-store.mjs、live/useResearchData.ts |
| 来源适配 | prototype/server/gateway.mjs |
| Worker/D1缓存 | prototype/server/worker.mjs、public-cache.mjs |
| 本机网关 | prototype/server/dev.mjs、vite.config.ts |
| 云资源/迁移 | prototype/wrangler.jsonc、migrations/0001_public_cache.sql |

React、TypeScript、ECharts、Decimal；精确依赖见package-lock.json。

## 来源与缓存

腾讯报价和搜索；东方财富估值失败切腾讯备用；东方财富日线失败接受腾讯匹配证券qfqday，不把原价冒充前复权。新浪财报采用核实的归母字段。未核实的港股估值字段不套A股索引。

报价/估值5秒内存缓存、分时15秒；历史按自然年固定分段。往年7天、含当日5分钟、近7日结束区间1小时、财报6小时复核。浏览器另有受剩余新鲜期约束的短HTTP缓存。D1保存成功非空响应文档，30天旧成功回退，明确stale和原查询时点。详见 [数据设计](../design/data-and-ledger.md)。

## 运行差异

本地gateway直接调用适配器，不自动使用D1；云端通过PUBLIC_DATA绑定接入。Vite preview不独立提供API。Workers使用redirect: manual并拒绝3xx，有限时与大小限制。

云端已认领，使用普通wrangler deploy。未配置KV/R2/容器/Cron、私人云登录及台账API。前复权按过期分段重取，尚无跨年修订即时统一重算；刷新目标不代表行情零延迟。

