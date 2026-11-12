#!/usr/bin/env bash
# Superpowers 快速安装脚本 for Qoder

set -euo pipefail

echo "🚀 Superpowers 安装向导"
echo "========================"
echo ""

# 检测是否在 superpowers 仓库中
if [ -f "$(dirname "$0")/setup-skills.sh" ]; then
    SUPERPOWERS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
    echo "📦 从本地仓库安装: $SUPERPOWERS_DIR"
else
    SUPERPOWERS_DIR="$HOME/.qoder/superpowers"
    if [ ! -d "$SUPERPOWERS_DIR" ]; then
        echo "📥 克隆 Superpowers..."
        git clone https://github.com/obra/superpowers.git "$SUPERPOWERS_DIR"
        echo "✅ 克隆完成"
    else
        echo "✅ 已存在: $SUPERPOWERS_DIR"
    fi
fi

echo ""
echo "安装范围:"
echo "  1) 当前项目"
echo "  2) 全局(所有项目)"
read -p "选择 [1/2]: " scope

case "$scope" in
    1) SKILLS_DIR=".qoder/skills"; RULES_DIR=".qoder/rules" ;;
    2) SKILLS_DIR="$HOME/.qoder/skills"; RULES_DIR="$HOME/.qoder/rules" ;;
    *) echo "❌ 无效选择"; exit 1 ;;
esac

mkdir -p "$SKILLS_DIR" "$RULES_DIR"

echo ""
echo "🔗 创建技能链接..."
count=0
for skill_dir in "$SUPERPOWERS_DIR/skills"/*; do
    [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ] || continue
    skill_name=$(basename "$skill_dir")
    target="$SKILLS_DIR/$skill_name"
    rm -rf "$target"
    ln -s "$skill_dir" "$target"
    echo "  ✓ $skill_name"
    ((count++))
done

echo ""
echo "✅ 已链接 $count 个技能"

# 复制规则文件
if [ -f "$SUPERPOWERS_DIR/.qoder/rules/superpowers-core.md" ]; then
    cp "$SUPERPOWERS_DIR/.qoder/rules/superpowers-core.md" "$RULES_DIR/"
    echo "✅ 规则文件已安装"
fi

echo ""
echo "════════════════════════"
echo "✨ 安装完成!"
echo "════════════════════════"
echo ""
echo "下一步:"
echo "  1. 重启 Qoder IDE"
echo "  2. 在设置中将 'superpowers-core' 设为 'Always Apply'"
echo "  3. 输入 / 查看所有技能"
echo ""
echo "示例: '我想添加登录功能' 或 '/brainstorming'"
echo ""
