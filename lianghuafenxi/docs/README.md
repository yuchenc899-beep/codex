# 资料总览

版本：2026-11-12 当前实现基线。当前项目名称统一为“宇辰看板”。

## 阅读顺序

| 资料 | 用途 |
| --- | --- |
| [用户指南](user-guide.md) | 导入、使用、保存、常见故障 |
| [业务方案](plans/quant-system-business.md) | 业务边界与需求落实情况 |
| [技术方案](plans/quant-system-technical.md) | 当前技术架构和代码入口 |
| [详细设计总览](plans/2026-11-11-quant-system-detailed-design.md) | 页面、数据、计算、接口与云部署设计索引 |
| [实施与待办](plans/quant-system-implementation.md) | 已交付、缺项及后续优先级 |
| [发布运维](deployment.md) | 账号、D1、构建、发布和排障 |
| [最新部署验证](validation/cloudflare-deployment-2026-11-12.md) | 真实部署版本、接口与缓存命中证据 |
| [变更与资料治理](changelog.md) | 决策演变、原稿保留和更新规则 |
| [技能与应用关系](skills-and-runtime.md) | 技能在项目中的定位 |

## 当前事实

主应用为 React + TypeScript + ECharts，部署为 Cloudflare Worker + Static Assets。同一账号下的 D1 `yuchen-market-cache` 只缓存公开历史日线和财报；自选、持仓、成本、笔记仍采用浏览器临时会话。未配置持续后台监控和付费订阅。

五个菜单：市场总览、我的自选、持仓管理、事件与提醒、资料与设置。个股研究在证券弹窗内，无独立菜单。正式入口不预填演示持仓；`?mode=demo` 是独立演示模式。

截至本轮，66 项自动化测试及生产构建通过；报价、估值备用源、公开样例历史和财报 D1 命中已实测。不能把样例接口验证外推为全部证券、全部周期、移动端和持续运行均通过验收。

## 资料优先级

当前方案说明“现在是什么”，实施待办说明“下一步做什么”，validation 保留“当时实际看到什么”。archive 原稿及带“历史阶段”标记的专项计划仅供追溯，不作为当前部署指令。

[原稿归档](archive/README.md) 保留本轮重构前的 18 份设计和计划；原始截图、JSON 和检查输出保持原样。真实资料继续留在 private，当前通用文档不复制持仓明细。

