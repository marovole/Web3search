#!/bin/bash

# 部署前检查脚本 - Phase 4.3
# 用途：在部署到 Render.com 之前进行本地验证

set -e

echo "=================================================="
echo "Web3 Search - 部署前检查脚本"
echo "=================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
CHECKS_PASSED=0
CHECKS_FAILED=0

# 检查函数
check_item() {
    local item=$1
    local command=$2

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $item"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $item"
        ((CHECKS_FAILED++))
    fi
}

# ===== 检查 1: Git 状态 =====
echo "1. 检查 Git 状态..."
check_item "Git 仓库已初始化" "git rev-parse --git-dir > /dev/null 2>&1"
check_item "无未提交的修改" "test -z \"\$(git status --porcelain)\""
echo ""

# ===== 检查 2: 配置文件 =====
echo "2. 检查配置文件..."
check_item "Dockerfile 存在" "test -f Dockerfile"
check_item "render.yaml 存在" "test -f render.yaml"
check_item ".env.example 存在" "test -f .env.example"
check_item "docs/DEPLOYMENT.md 存在" "test -f docs/DEPLOYMENT.md"
check_item "README.md 存在" "test -f README.md"
echo ""

# ===== 检查 3: 依赖文件 =====
echo "3. 检查关键依赖文件..."
check_item "requirements.txt 存在" "test -f requirements.txt"
check_item "requirements.txt 包含 weasyprint" "grep -q weasyprint requirements.txt"
check_item "requirements.txt 包含 markdown2" "grep -q markdown2 requirements.txt"
check_item "requirements.txt 包含 fastapi" "grep -q fastapi requirements.txt"
check_item "requirements.txt 包含 sqlalchemy" "grep -q sqlalchemy requirements.txt"
echo ""

# ===== 检查 4: Docker 镜像 =====
echo "4. 检查 Dockerfile 配置..."
check_item "Dockerfile 包含 WeasyPrint 库" "grep -q 'libpango\\|libcairo' Dockerfile"
check_item "Dockerfile 包含中文字体" "grep -q 'fonts-noto-cjk\\|fonts-wqy' Dockerfile"
check_item "Dockerfile 包含 fc-cache 字体更新" "grep -q 'fc-cache' Dockerfile"
check_item "Dockerfile 包含健康检查" "grep -q HEALTHCHECK Dockerfile"
echo ""

# ===== 检查 5: 应用代码 =====
echo "5. 检查应用代码结构..."
check_item "app/main.py 存在" "test -f app/main.py"
check_item "app/core/config.py 包含 BASE_DIR" "grep -q 'BASE_DIR' app/core/config.py"
check_item "analyzers/analyzer_output.py 存在" "test -f app/services/research_engine/analyzers/analyzer_output.py"
check_item "所有分析器已更新" "grep -q 'from app.services.llm import llm_client' app/services/research_engine/analyzers/competitor_analyzer.py"
check_item "深度研究模块完整" "test -f app/services/research_engine/deep_research.py"
echo ""

# ===== 检查 6: 测试文件 =====
echo "6. 检查测试文件..."
check_item "集成测试存在" "test -f tests/integration/test_report_pipeline.py"
check_item "测试包含 PDF 导出测试" "grep -q 'test_pdf_export' tests/integration/test_report_pipeline.py"
check_item "测试包含中文字体测试" "grep -q 'test_chinese_font' tests/integration/test_report_pipeline.py"
echo ""

# ===== 检查 7: 文档 =====
echo "7. 检查文档完整性..."
check_item "API.md 包含 9 大分析维度" "grep -q '九大分析维度' docs/API.md"
check_item "API.md 包含 PDF 导出说明" "grep -q '导出报告为PDF' docs/API.md"
check_item "DEPLOYMENT.md 包含 Render 部署说明" "grep -q 'Render.com' docs/DEPLOYMENT.md"
check_item "README.md 包含完整项目描述" "grep -q 'Web3 Search Backend API' README.md"
echo ""

# ===== 检查 8: 可选的本地测试 =====
echo "8. 可选的本地测试..."
if command -v python3 &> /dev/null; then
    check_item "Python 3 已安装" "python3 --version"

    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        check_item "虚拟环境已创建" "test -d venv"
    fi
fi
echo ""

# ===== 摘要 =====
echo "=================================================="
echo "检查摘要"
echo "=================================================="
echo -e "通过: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "失败: ${RED}$CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！可以进行部署${NC}"
    echo ""
    echo "下一步："
    echo "1. 在 Render.com 仪表板创建新的 Blueprint"
    echo "2. 连接 GitHub 仓库"
    echo "3. 设置环境变量（OPENROUTER_API_KEY 等）"
    echo "4. 开始部署"
    echo "5. 监控部署日志"
    echo "6. 执行部署后验证"
    echo ""
    echo "详细的部署指南请参考: RENDER_DEPLOYMENT_GUIDE.md"
    exit 0
else
    echo -e "${RED}✗ 有 $CHECKS_FAILED 个检查失败，请修复后再部署${NC}"
    echo ""
    echo "请检查以下项目："
    echo "1. 所有必需的文件是否存在"
    echo "2. Dockerfile 配置是否正确"
    echo "3. render.yaml 配置是否完整"
    echo "4. 应用代码是否已正确修改"
    echo ""
    exit 1
fi
