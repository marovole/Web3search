# 生产环境测试脚本使用说明

## 概述

本目录包含用于测试Web3search生产环境的自动化测试脚本。

## 测试脚本

### 1. `test_production.py` - 后端API功能测试

全面的后端API功能测试脚本，测试所有核心功能。

**功能包括**:
- 基础系统测试（健康检查、API文档）
- Quick Chat功能测试
- Deep Research功能测试
- 报告管理功能测试
- 搜索功能测试
- 热点识别功能测试
- 安全测试（CORS、输入验证）
- 性能测试

**使用方法**:
```bash
cd /Users/marovole/GitHub/Web3search
python3 scripts/test_production.py
```

**输出**:
- 控制台输出测试结果
- `production_test_report.json` - JSON格式详细报告

### 2. `test_frontend_ui.py` - 前端UI功能测试

使用Playwright进行前端UI自动化测试。

**功能包括**:
- 页面加载测试
- UI元素检查
- 控制台错误检查
- 响应式设计测试
- API连通性测试

**使用方法**:
```bash
# 需要先安装Playwright
pip install playwright
playwright install chromium

# 运行测试
python3 scripts/test_frontend_ui.py
```

**输出**:
- 控制台输出测试结果
- `frontend_ui_test_report.json` - JSON格式详细报告

### 3. `generate_comprehensive_report.py` - 综合报告生成

整合所有测试结果，生成Markdown格式的综合测试报告。

**使用方法**:
```bash
python3 scripts/generate_comprehensive_report.py
```

**输出**:
- `PRODUCTION_TEST_REPORT.md` - Markdown格式的综合测试报告

## 快速开始

### 运行完整测试套件

```bash
# 1. 运行后端API测试
python3 scripts/test_production.py

# 2. (可选) 运行前端UI测试（需要Playwright）
python3 scripts/test_frontend_ui.py

# 3. 生成综合报告
python3 scripts/generate_comprehensive_report.py
```

## 测试环境

- **前端URL**: https://web3search.vercel.app
- **后端URL**: https://web3search-api.onrender.com
- **API文档**: https://web3search-api.onrender.com/docs

## 测试结果解读

### 测试状态

- ✅ **PASSED**: 测试通过
- ❌ **FAILED**: 测试失败，需要修复
- ⚠️  **WARNING**: 测试通过但有警告，建议检查
- ⏭️  **SKIPPED**: 测试跳过

### 性能指标

- **平均响应时间 < 1秒**: ✅ 优秀
- **平均响应时间 < 3秒**: ⚠️  良好
- **平均响应时间 > 3秒**: ❌ 需改进

## 常见问题

### 1. 前端返回404错误

**问题**: 前端部署可能失败或未正确配置

**解决方案**:
- 检查Vercel部署状态
- 验证构建流程
- 确认域名配置

### 2. API返回500错误

**问题**: 服务器内部错误

**解决方案**:
- 检查服务器日志
- 验证数据库连接
- 检查外部API依赖

### 3. 测试超时

**问题**: 响应时间过长

**解决方案**:
- 检查网络连接
- 验证服务器负载
- 检查外部API响应时间

## 持续集成

可以将这些测试脚本集成到CI/CD流程中：

```yaml
# GitHub Actions 示例
- name: Run Production Tests
  run: |
    python3 scripts/test_production.py
    python3 scripts/generate_comprehensive_report.py
```

## 注意事项

1. 测试会实际调用生产环境API，请谨慎使用
2. 某些测试可能需要较长时间（如Deep Research）
3. 建议在非高峰时段运行完整测试套件
4. 测试结果会保存到JSON文件，可用于进一步分析

## 更新日志

- 2025-11-07: 初始版本，包含基础API测试和报告生成功能

