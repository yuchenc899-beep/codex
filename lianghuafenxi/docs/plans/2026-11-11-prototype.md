> 历史阶段资料：保留当时计划、结果和截图，不作为当前运行或验收说明。当前状态见 [资料总览](../README.md)。

# 量化工作台原型 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在当前项目制作供用户评审的六页面可点击网页原型。

**Architecture:** 本地预览、静态可构建的React应用，全部使用明确标注的示例数据。会话存储保存交互结果，不调用真实行情商，不云部署；原型预览服务不改变正式产品完整云端架构。

**Tech Stack:** React、Vite、TypeScript、ECharts、Lucide，依赖仅安装prototype目录。

## Task 1：交互规则与工程

Files：`prototype/package.json`、`prototype/src/domain.mjs`、`prototype/tests/domain.test.mjs`。
先写19.99/20筛选、费用买卖核算、超额卖出、重复自选测试；运行`node --test tests/domain.test.mjs`确认失败，再实现通过。配置Vite及类型检查。

## Task 2：六页面

Files：`prototype/src/App.tsx`、`prototype/src/styles.css`、`prototype/src/data.ts`、`prototype/src/main.tsx`。
实现总览、自选、持仓、个股、事件提醒与设置；共用侧栏、数据状态、搜索、表格、图表和弹窗。实现筛选/分组/自选增删/真实记录示例录入/图表周期/提醒规则/导出/会话恢复。保持所有行情为示例，不模拟真实联网成功。

## Task 3：构建及浏览器核验

`npm test`、`npm run build`。启动127.0.0.1预览；在浏览器逐页检查，并测试筛选、增删自选、持仓买卖、图表切换、提醒、导出与窄屏。记录实际结果于`docs/validation/prototype-review.md`，向用户打开预览。当前不是Git仓库，不创建虚构提交或PR。
