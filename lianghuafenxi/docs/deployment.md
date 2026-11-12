# 发布与运维

2026-11-12。当前资源见 prototype/wrangler.jsonc；主站为 https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/ 。

## 已有资源

本人已认领账号YOUR_ACCOUNT；Worker yuchen-dashboard；D1 yuchen-market-cache；PUBLIC_DATA与ASSETS已绑定。数据库只保存公开历史/财报。不要重复创建数据库或重新匿名部署替换现有服务。

最后一次业务发布版本 be080643-bf57-4786-a38f-b43b84d386f4。本轮资料重构不代表重新发布业务代码。

## 本地与检查

在prototype目录先npm ci，两个终端分别npm run gateway和npm run dev -- --strictPort。云端D1不由Node开发网关自动加载。npm run preview只服务静态构建。

发布前运行npm test、npm run build、wrangler deploy --dry-run，检查只上传dist和Worker依赖，不包含private、真实持仓清单、令牌、配置备份或私人截图。

## 发布原站点

使用官方Wrangler；本项目验证版本4.160.1。先wrangler whoami，选择wrangler配置对应的原账号；多账号环境必须明确目标账号，不能仅凭默认账号部署。官方OAuth所需范围为account:read、user:read、workers:write、workers_scripts:write、workers_routes:write及d1:write。

已有表结构升级运行wrangler d1 migrations apply yuchen-market-cache --remote，再wrangler deploy。迁移前核对SQL；破坏性变化另行备份与审核。已认领后不使用--temporary。

授权失效时重新官方登录；本机回调存在超时或旧state问题时可用wrangler login --device。设备码短时有效，一次只用新码；先在同一浏览器登录Cloudflare，CSRF会话错误时先恢复正常登录，不关闭安全保护。OAuth令牌、设备挑战及认领URL不写入仓库。

本次网络排障使用系统既有本地代理；代理地址是环境配置，不硬编码进业务代码。切换网络后重新核对，不能假设任何workers.dev入口直连可达。

## 发布后验证

- /api/v1/health返回200且publicDataCache=d1。
- 公开报价、估值有来源时间及正确单位；备用切换有警告。
- 同一有效历史区间/财报请求两次，第二次layer=d1且fetchedAt不变；浏览器可有自身缓存，应以独立请求核验。
- 个人信息仍只在会话中；导入导出可恢复、持仓日涨跌列可排序。
- 记录版本及失败，不将单个公开样例当全覆盖验收。

回滚可通过Cloudflare部署版本管理选择先前已验证版本；应用回滚不自动回滚数据库表结构。公开缓存失效可重新采集，不能以此替代私人会话备份。没有后台Cron；免费额度及来源故障仍可能影响服务。

