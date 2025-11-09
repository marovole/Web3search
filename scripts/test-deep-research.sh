#!/bin/bash

# 深度研究 API 测试脚本
# 使用方法：./scripts/test-deep-research.sh [URL] [QUERY]

set -e

# 默认值
API_URL="${1:-http://localhost:8787}"
QUERY="${2:-Bitcoin}"
ENDPOINT="$API_URL/api/v1/chat/deep-research/stream"

echo "========================================"
echo "深度研究 API 测试"
echo "========================================"
echo "API URL: $ENDPOINT"
echo "Query: $QUERY"
echo "========================================"
echo ""

# 测试请求体
REQUEST_BODY=$(cat <<EOF
{
  "query": "$QUERY",
  "dimensions": ["market_analysis", "technical_analysis"],
  "use_cache": false
}
EOF
)

echo "发送请求..."
echo "$REQUEST_BODY"
echo ""
echo "========================================"
echo "SSE 响应流："
echo "========================================"
echo ""

# 发送请求并实时显示 SSE 流
curl -N -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_BODY" \
  2>/dev/null | while IFS= read -r line; do
    # 解析 SSE 数据行
    if [[ $line == data:* ]]; then
      # 提取 JSON 数据
      json_data="${line#data: }"

      # 如果是 [DONE]，直接输出
      if [[ $json_data == "[DONE]" ]]; then
        echo ""
        echo "========================================"
        echo "✅ 测试完成！"
        echo "========================================"
        break
      fi

      # 解析并美化输出 JSON（如果安装了 jq）
      if command -v jq &> /dev/null; then
        event_type=$(echo "$json_data" | jq -r '.type' 2>/dev/null || echo "unknown")

        case $event_type in
          dimension_start)
            dimension=$(echo "$json_data" | jq -r '.dimension')
            echo ""
            echo "📊 开始分析: $dimension"
            echo "----------------------------------------"
            ;;
          delta)
            content=$(echo "$json_data" | jq -r '.content')
            echo -n "$content"
            ;;
          dimension_complete)
            dimension=$(echo "$json_data" | jq -r '.dimension')
            echo ""
            echo "----------------------------------------"
            echo "✅ 完成: $dimension"
            ;;
          error)
            dimension=$(echo "$json_data" | jq -r '.dimension')
            message=$(echo "$json_data" | jq -r '.message')
            echo ""
            echo "❌ 错误 ($dimension): $message"
            ;;
          report_complete)
            conversation_id=$(echo "$json_data" | jq -r '.conversation_id')
            echo ""
            echo "========================================"
            echo "📝 报告完成"
            echo "Conversation ID: $conversation_id"
            echo "========================================"
            ;;
          *)
            echo "$json_data" | jq '.' 2>/dev/null || echo "$json_data"
            ;;
        esac
      else
        # 如果没有 jq，直接输出原始数据
        echo "$json_data"
      fi
    fi
  done

echo ""
echo "测试脚本执行完成。"
