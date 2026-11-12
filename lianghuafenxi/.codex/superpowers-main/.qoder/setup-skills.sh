#!/usr/bin/env bash
# Superpowers 技能安装脚本 for Qoder

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
QODER_SKILLS_DIR="${SCRIPT_DIR}/skills"
SOURCE_SKILLS_DIR="${PROJECT_ROOT}/skills"

echo "🚀 安装 Superpowers 技能..."

mkdir -p "${QODER_SKILLS_DIR}"

count=0
for skill_dir in "${SOURCE_SKILLS_DIR}"/*; do
    [ -d "${skill_dir}" ] && [ -f "${skill_dir}/SKILL.md" ] || continue
    skill_name=$(basename "${skill_dir}")
    target_dir="${QODER_SKILLS_DIR}/${skill_name}"
    
    rm -rf "${target_dir}"
    ln -s "${skill_dir}" "${target_dir}"
    echo "✓ ${skill_name}"
    ((count++))
done

echo ""
echo "✅ 已链接 ${count} 个技能"
echo ""
echo "重启 Qoder 后输入 / 查看所有技能"
