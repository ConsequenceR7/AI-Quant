#!/bin/bash
# ============================================================
# GitHub Pages 部署脚本
# 用法: bash deploy.sh "提交信息"
# ============================================================

set -e

echo "============================================"
echo "  量化看板 GitHub Pages 部署"
echo "============================================"

# 检查是否有未提交更改
if [[ -n $(git status --porcelain) ]]; then
    echo "[*] 发现文件变更，准备提交..."
    git add -A
    COMMIT_MSG="${1:-更新量化分析看板}"
    git commit -m "$COMMIT_MSG"
    echo "[OK] 已提交: $COMMIT_MSG"
else
    echo "[*] 无文件变更，跳过提交"
fi

# 推送到 GitHub
echo "[*] 推送到 GitHub..."
git push origin main

echo ""
echo "============================================"
echo "[Done] 部署完成！"
echo "访问: https://你的用户名.github.io/仓库名/"
echo "============================================"
