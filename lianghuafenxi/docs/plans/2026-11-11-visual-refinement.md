> 历史阶段资料：保留当时计划、结果和截图，不作为当前运行或验收说明。当前状态见 [资料总览](../README.md)。

# 宇辰看板视觉优化 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 保留纯黑底，优化六页面文字、配色与交互层级，并交付原创矢量Logo。

**Architecture:** 保留现有原型交互和会话数据，通过独立视觉系统覆盖样式、统一图表主题和品牌资产完成调整。使用系统字体，无外部字体请求。

**Tech Stack:** CSS变量、React、原创SVG、ECharts。

## 1. 品牌

创建`prototype/public/brand/yuchen-symbol.svg`及横版标识。图形以Y形坐标、轨道和四芒辰星构成；接入侧栏、页脚和favicon。使用矢量以适应小尺寸和高分屏，不需要位图生成。

## 2. 字体与配色

创建`prototype/src/visual-system.css`：纯黑画布、三档中性面板、正文/辅助/弱化三级灰阶、单一蓝色操作色。正文13–14px、辅助11–12px，数字等宽排列；警告琥珀、涨跌红绿。调整表格、筛选器、卡片、弹窗和移动端，统一焦点及悬停状态。

## 3. 验证

运行现有6项行为测试和构建；浏览器逐页检查字体、品牌与交互，核对纯黑画布、桌面和390px窄屏、指数切换及图例颜色。保存总览/指数/窄屏截图供用户审阅。当前为可逆视觉修改，不增加仅镜像CSS实现的单元测试。
