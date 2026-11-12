# 宇辰看板 · 个人量化分析项目

当前资料基线：2026-11-12。主应用位于 `prototype/`，已部署到 [宇辰看板](https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/)。

以 [资料总览](docs/README.md) 为统一入口，业务范围、实现状态及限制以当前文档为准。历史截图、原始清单和旧稿不能当作当前行情或功能验收结果。

## 快速使用

1. 进入线上看板，在“资料与设置”导入会话 JSON。
2. 导入预览确认后，在自选和持仓列表点击证券名称打开研究弹窗。
3. 修改持仓通过台账录入；离开前导出会话，关闭浏览器后不保证恢复。
4. 历史和财报优先复用本账号 D1 缓存；报价、成交、估值及时查询。

完整步骤见 [用户指南](docs/user-guide.md)。

## 本地运行

在 `prototype` 目录执行 `npm ci`。两个终端分别运行 `npm run gateway` 与 `npm run dev -- --strictPort`，打开 http://127.0.0.1:5173/ 。开发网关监听 127.0.0.1:8787。

检查：`npm test`、`npm run build`。本机网关不自动连接云端 D1，D1 缓存由 Worker 入口实现；仅启动 Vite preview 不会启动 API。

## 目录

| 目录 | 用途 |
| --- | --- |
| prototype/src | 当前网页、研究和账本逻辑 |
| prototype/server | Node 开发网关、Worker、公开数据缓存 |
| prototype/migrations | 本人账号 D1 缓存表迁移 |
| docs | 当前方案、使用说明、部署与验收 |
| docs/archive | 重构前方案原稿 |
| private | 真实导入文件及私人验证材料，禁止公开部署 |
| quant_app | 早期 Python 实现，不是当前云端入口 |
| .agents/skills、skills | 项目技能和研究工具，见技能说明 |

私人导入文件、持仓原始清单、凭据不能进入静态资源、截图公开报告或发布包。项目 AGENTS.md 为贡献约束，不应当被当作量化系统业务设计。

