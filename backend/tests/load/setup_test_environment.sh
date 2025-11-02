#!/bin/bash
# 负载测试环境设置脚本

set -e

echo "🚀 Setting up load test environment..."

# 创建必要的目录
mkdir -p reports
mkdir -p logs
mkdir -p data

# 检查Python依赖
echo "📦 Checking Python dependencies..."
pip install locust==2.20.0 gevent==23.7.0 requests aiohttp

# 检查系统资源
echo "💻 Checking system resources..."
echo "Available memory: $(free -h | grep '^Mem:' | awk '{print $7}')"
echo "CPU cores: $(nproc)"
echo "Disk space: $(df -h . | tail -1 | awk '{print $4}')"

# 检查文件描述符限制
echo "📁 Checking file descriptor limits..."
echo "Current ulimit: $(ulimit -n)"
if [ $(ulimit -n) -lt 65536 ]; then
    echo "⚠️  Warning: File descriptor limit is low. Consider running:"
    echo "   ulimit -n 65536"
fi

# 检查网络配置
echo "🌐 Checking network configuration..."
echo "Port range: $(sysctl net.ipv4.ip_local_port_range | cut -d'=' -f2)"

# 验证API服务
echo "🔍 Verifying API service..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ API service is running"
else
    echo "❌ API service is not responding"
    echo "   Please start the API service before running load tests"
    exit 1
fi

# 准备测试数据
echo "📝 Preparing test data..."
python prepare_load_test_data.py

echo "✅ Load test environment setup completed!"
echo ""
echo "🎯 Next steps:"
echo "1. Run basic test: locust -f locustfile.py --host=http://localhost:8000"
echo "2. Run advanced test: locust -f advanced_user_behavior.py --host=http://localhost:8000"
echo "3. Run scenario test: python load_test_config.py"
