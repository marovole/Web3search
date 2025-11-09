#!/bin/bash
# 简单的流式响应测试

echo "测试流式聊天响应..."
curl -N -X POST "http://localhost:8787/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "用一句话介绍比特币", "stream": true}' &

# 保存 PID
CURL_PID=$!

# 等待 10 秒后杀掉进程
sleep 10
kill $CURL_PID 2>/dev/null

echo ""
echo "测试完成"
