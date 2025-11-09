#!/bin/bash

# 聊天 API 测试脚本
# 测试流程：
# 1. 创建新对话（不提供 conversation_id）
# 2. 继续对话（提供 conversation_id）
# 3. 查询对话历史

BASE_URL="http://localhost:8787/api/v1/chat"

echo "======================================"
echo "测试 1: 创建新对话（非流式）"
echo "======================================"
RESPONSE=$(curl -s -X POST "${BASE_URL}/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是比特币？",
    "stream": false
  }')

echo "响应: ${RESPONSE}" | jq '.'

# 提取 conversation_id
CONV_ID=$(echo "${RESPONSE}" | jq -r '.conversation_id')
echo ""
echo "获取到的 conversation_id: ${CONV_ID}"

if [ "${CONV_ID}" == "null" ] || [ -z "${CONV_ID}" ]; then
  echo "错误: 无法获取 conversation_id"
  exit 1
fi

echo ""
echo "======================================"
echo "测试 2: 继续对话（使用相同 conversation_id）"
echo "======================================"
curl -s -X POST "${BASE_URL}/quick-chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"它是什么时候创建的？\",
    \"conversation_id\": \"${CONV_ID}\",
    \"stream\": false
  }" | jq '.'

echo ""
echo "======================================"
echo "测试 3: 查询对话历史"
echo "======================================"
curl -s -X GET "${BASE_URL}/conversations/${CONV_ID}" | jq '.'

echo ""
echo "======================================"
echo "测试 4: 流式对话"
echo "======================================"
echo "发送流式请求..."
curl -N -X POST "${BASE_URL}/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "简单介绍一下以太坊",
    "stream": true
  }'

echo ""
echo "======================================"
echo "测试完成！"
echo "======================================"
