# 云资源与验收

2026-11-12当前实现。

主站https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/ 。Worker为yuchen-dashboard，ASSETS为静态资源，PUBLIC_DATA绑定本人账号的yuchen-market-cache。资源ID/兼容日期以prototype/wrangler.jsonc为准。

匿名站点已经认领，普通账号OAuth发布；旧courageous-specialist临时地址、认领链接和设备码均不是当前操作入口。凭据仅保留官方用户配置，不写入项目文档。

保持免费路线，未开通付费套餐、Containers、Cron、KV/R2或付费模型。配额不是无限容量，超限可能失败。D1故障可回源，数据库和源同时失败不保证持续成功。

未实施Cloudflare Access私人身份保护；主站是公开应用，不宣称有私人云账户鉴权。私人台账不上传；D1仅保存公开历史/财报，并经受限接口读取，无通用SQL/整库导出API。

66项测试和生产构建通过；公开报价/估值、五年财报及243条年度日线D1命中已实测。全清单/全周期、移动端本轮视觉检查、长时高并发、完整配额预算、复权跨年即时一致性尚未验收。

[逐次部署验证](../validation/cloudflare-deployment-2026-11-12.md)保留真实失败过程，以最终验证章节为当前结果。步骤见 [发布运维](../deployment.md)。

