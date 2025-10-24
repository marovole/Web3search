#!/bin/bash

# ================================
# GitHub推送脚本
# ================================

set -e

echo "📦 准备推送代码到GitHub..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Git状态
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ 这不是一个Git仓库${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Git仓库检查通过${NC}"
echo ""

# 检查是否已有远程仓库
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")

if [ ! -z "$CURRENT_REMOTE" ]; then
    echo -e "${YELLOW}⚠️  已配置远程仓库: $CURRENT_REMOTE${NC}"
    echo ""
    read -p "是否使用现有仓库? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入新的GitHub仓库URL (格式: https://github.com/用户名/仓库名.git): " NEW_REMOTE
        git remote set-url origin "$NEW_REMOTE"
        echo -e "${GREEN}✅ 远程仓库已更新${NC}"
    fi
else
    echo -e "${BLUE}📝 请先在GitHub创建新仓库${NC}"
    echo ""
    echo "步骤："
    echo "1. 访问 https://github.com/new"
    echo "2. 仓库名: Web3search"
    echo "3. 可见性: ${YELLOW}Public${NC} (Render免费计划要求)"
    echo "4. 不要初始化README、.gitignore或LICENSE（我们已有）"
    echo "5. 点击 'Create repository'"
    echo ""
    read -p "创建完成后按回车继续..."
    echo ""

    read -p "请输入GitHub仓库URL (格式: https://github.com/用户名/Web3search.git): " REPO_URL

    if [ -z "$REPO_URL" ]; then
        echo -e "${RED}❌ 仓库URL不能为空${NC}"
        exit 1
    fi

    git remote add origin "$REPO_URL"
    echo -e "${GREEN}✅ 远程仓库已添加: $REPO_URL${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查是否有未提交的更改
if [ ! -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  检测到未提交的更改${NC}"
    git status --short
    echo ""
    read -p "是否提交这些更改? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "chore: 部署到Render前的最终更新

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
        echo -e "${GREEN}✅ 更改已提交${NC}"
    else
        echo -e "${YELLOW}⚠️  跳过提交${NC}"
    fi
fi

echo ""

# 显示当前提交
echo "📊 准备推送的提交:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git log --oneline -5
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 推送到GitHub
echo "🚀 推送到GitHub..."
read -p "确认推送? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}推送已取消${NC}"
    exit 0
fi

echo ""
echo "正在推送..."

# 尝试推送
if git push -u origin main; then
    echo ""
    echo -e "${GREEN}✅ 代码已成功推送到GitHub！${NC}"
    echo ""

    # 获取仓库URL
    REPO_URL=$(git remote get-url origin)
    REPO_WEB_URL=$(echo $REPO_URL | sed 's/\.git$//' | sed 's/git@github\.com:/https:\/\/github.com\//')

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}🎉 GitHub推送完成！${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📍 仓库地址: $REPO_WEB_URL"
    echo ""
    echo "🔗 下一步："
    echo "   1. 访问 https://render.com"
    echo "   2. 使用GitHub账户登录"
    echo "   3. 创建新的Blueprint部署"
    echo ""
    echo -e "${BLUE}详细步骤请查看: DEPLOYMENT_RENDER.md${NC}"
    echo ""

else
    echo ""
    echo -e "${RED}❌ 推送失败${NC}"
    echo ""
    echo "可能的原因："
    echo "1. 仓库URL错误"
    echo "2. 没有推送权限"
    echo "3. 分支名称不匹配"
    echo ""
    echo "请检查GitHub仓库设置或使用以下命令手动推送："
    echo "  git push -u origin main --force"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
