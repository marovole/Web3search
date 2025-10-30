#!/bin/bash
# 依赖安全扫描脚本
# 自动运行npm audit并生成安全报告

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"
OUTPUT_DIR="$SCRIPT_DIR/../frontend/security-reports"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

echo "🔍 开始依赖安全扫描..."

cd "$FRONTEND_DIR"

# 运行npm audit并生成JSON报告
echo "📊 运行npm audit..."
npm audit --json > "$OUTPUT_DIR/audit-report.json" || true

# 运行npm audit并生成人类可读的报告
echo "📋 生成安全报告..."
npm audit > "$OUTPUT_DIR/audit-report.txt" || true

# 检查是否有严重漏洞
VULNERABILITIES=$(jq -r '.metadata.vulnerabilities.total // 0' "$OUTPUT_DIR/audit-report.json" 2>/dev/null || echo "0")

if [ "$VULNERABILITIES" -gt 0 ]; then
    echo "⚠️  发现 $VULNERABILITIES 个安全漏洞"
    echo "📄 详细报告请查看: $OUTPUT_DIR/audit-report.txt"
    
    # 检查是否有严重漏洞
    CRITICAL=$(jq -r '.metadata.vulnerabilities.critical // 0' "$OUTPUT_DIR/audit-report.json" 2>/dev/null || echo "0")
    HIGH=$(jq -r '.metadata.vulnerabilities.high // 0' "$OUTPUT_DIR/audit-report.json" 2>/dev/null || echo "0")
    
    if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
        echo "🚨 发现严重漏洞！"
        echo "   - Critical: $CRITICAL"
        echo "   - High: $HIGH"
        echo ""
        echo "💡 建议运行以下命令修复："
        echo "   npm audit fix"
        exit 1
    else
        echo "✅ 所有漏洞为中等或低严重性"
        exit 0
    fi
else
    echo "✅ 未发现安全漏洞"
    exit 0
fi

