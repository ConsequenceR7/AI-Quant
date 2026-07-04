#!/bin/bash
# ============================================================
# GitHub Pages 一键推送脚本
# 在 Git Bash 中运行: bash push.sh
# ============================================================

KEYFILE="/c/Users/联想/.ssh/id_rsa"
export GIT_SSH_COMMAND="ssh -i \"$KEYFILE\" -o UserKnownHostsFile=/tmp/gh_known_hosts -o StrictHostKeyChecking=accept-new"

echo "=== 推送量化分析看板到 GitHub ==="
cd "D:\桌面\量化\TASK1" || cd /d/桌面/量化/TASK1

# 确保 GitHub 主机密钥已知
ssh-keyscan github.com >> /tmp/gh_known_hosts 2>/dev/null

# 推送
git push -u origin master

echo ""
echo "=== 推送完成！==="
echo "下一步：在 GitHub 仓库 Settings > Pages 中启用 GitHub Pages"
echo "Source 选 'Deploy from a branch'，Branch 选 'master'，Folder 选 '/' (root)"
echo "访问地址: https://consequencer7.github.io/AI-Quant/"
