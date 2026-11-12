> 历史阶段资料：保留当时计划、结果和截图，不作为当前运行或验收说明。当前状态见 [资料总览](../README.md)。

# 宇辰看板视觉优化与Logo重设计记录

2026-11-11；依据用户对字体、配色及Logo的反馈调整，未改变原型业务规则。

## 视觉方向

继续使用纯黑画布。中性深灰区分卡片，主操作和选中状态采用低饱和蓝，正文为冷白，辅助文字提高亮度；涨跌红绿、风险琥珀保持独立语义。局部组合卡和弹窗使用轻微蓝灰层次。

系统字体：Segoe UI / PingFang SC / Microsoft YaHei；数字优先Bahnschrift，系统无该字体时自动回退。无需联网加载字体。桌面主标题32px、导航14px、指数数字25px；表格主体13px，辅助说明以11–12px为主，品牌英文等装饰信息单独缩小。

## Logo

原创“辰星坐标”：Y形主线与轨道、四芒星组合。SVG路径可缩放，应用于侧栏、页脚及favicon。横版保留中文名与英文副标。

- [图形标识](../../prototype/public/brand/yuchen-symbol.svg)
- [横版标识](../../prototype/public/brand/yuchen-wordmark.svg)
- [资产说明](../../prototype/public/brand/README.md)

## 已完成验证

- `npm test`：6通过、0失败。
- `npm run build`：TypeScript与Vite构建通过。此前单块体积和Lucide指令提示仍为非阻断提示。
- 浏览器确认主背景为rgb(0,0,0)，Logo图片加载成功；桌面侧栏图标36px。
- 六页桌面检查：1078px视口，document宽1073px，无页面级横向溢出。
- 六页窄屏检查：390px视口，document宽385px，无页面级横向溢出；恢复默认视口。
- 指数月K切换及图表显示通过；MA5/MA20图例颜色和线条颜色统一。
- 调整侧栏关注标签后，三个标签处于同一行。
- 检查后保留原型预览，未清空用户会话记录。

截图：[最终总览](prototype/overview-v2-final.jpg)、[指数](prototype/indices-v2.jpg)、[手机首屏](prototype/mobile-v2.jpg)。其余页面的v2截图位于同目录。部分长页面全屏截图失败，改用成功的可视区域截图交付；不影响网页导航或布局验证。

本次仍为示例原型；未接入真实行情、财报、持仓或提醒。
