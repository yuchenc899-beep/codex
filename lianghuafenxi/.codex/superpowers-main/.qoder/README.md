# Superpowers for Qoder

完整的软件开发工作流技能系统,支持 [Qoder](https://qoder.com)。

## 安装

```bash
# 克隆并安装
git clone https://github.com/obra/superpowers.git
cd superpowers
.qoder/setup-skills.sh

# 重启 Qoder IDE
```

重启后输入 `/` 查看 14 个可用技能。

## 使用

**自动**: 直接描述需求,AI 自动选择技能  
**手动**: `/brainstorming`、`/test-driven-development` 等

## 核心技能

- **brainstorming** - 设计优化
- **test-driven-development** - TDD 循环
- **systematic-debugging** - 根因分析
- **writing-plans** - 任务规划
- **executing-plans** - 批量执行
- **requesting-code-review** - 代码审查

输入 `/` 查看全部 14 个技能。

## 工作流

设计 → 规划 → TDD 开发 → 审查 → 合并

## 更新

```bash
cd superpowers && git pull
# 重启 Qoder
```

## 故障排查

技能未显示: 检查 `ls -la .qoder/skills/` 后重启  
无法触发: 手动使用 `/技能名` 测试

---

**问题反馈**: https://github.com/obra/superpowers/issues  
**主文档**: https://github.com/obra/superpowers
