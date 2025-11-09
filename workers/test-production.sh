#!/bin/bash

# 生产环境烟雾测试脚本
BASE_URL="https://web3search-api.marovole.workers.dev"

echo "======================================"
echo "测试 1: 健康检查"
echo "======================================"
curl -s "${BASE_URL}/api/v1/health" | jq '.'

echo ""
echo "======================================"
echo "测试 2: 搜索自动完成"
echo "======================================"
curl -s "${BASE_URL}/api/v1/search/autocomplete?q=ethereum&limit=5" | jq '.'

echo ""
echo "======================================"
echo "测试 3: 聊天 API (非流式)"
echo "======================================"
curl -s -X POST "${BASE_URL}/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "用一句话介绍区块链", "stream": false}' | jq '.message'

echo ""
echo "======================================"
echo "测试 4: 速率限制检查"
echo "======================================"
echo "发送 3 个连续请求检查速率限制头..."
for i in {1..3}; do
  echo "请求 $i:"
  curl -I -s "${BASE_URL}/api/v1/health" | grep -i "ratelimit"
done

echo ""
echo "======================================"
echo "所有测试完成！"
echo "======================================"
