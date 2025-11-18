#!/usr/bin/env node

// Web3search Cloudflare Pages 环境变量修复脚本
// 解决前端API配置问题

const { execSync } = require('child_process');

console.log('🔧 Web3search Cloudflare Pages 环境变量修复脚本');
console.log('==================================================');

// 需要设置的环境变量
const envVars = {
  'VITE_API_BASE_URL': 'https://web3search-api.marovole.workers.dev',
  'VITE_ENVIRONMENT': 'production',
  'VITE_USE_MOCK_API': 'false',
  'VITE_ENABLE_SENTRY': 'false',
  'VITE_ENABLE_ANALYTICS': 'true',
  'VITE_ENABLE_EXPERIMENTAL_FEATURES': 'false',
  'VITE_DEFAULT_CHAT_MODE': 'quick',
  'VITE_DEBUG_MODE': 'false',
  'VITE_GA_MEASUREMENT_ID': 'G-M0DW9G90FT',
  'VITE_SENTRY_DSN': '',
  'VITE_SENTRY_ENVIRONMENT': 'production'
};

console.log('\n📋 需要设置的环境变量：');
Object.entries(envVars).forEach(([key, value]) => {
  console.log(`  ${key}: ${value}`);
});

console.log('\n🚀 手动设置步骤：');
console.log('1. 登录 Cloudflare Dashboard: https://dash.cloudflare.com');
console.log('2. 进入 Pages 部分');
console.log('3. 选择 web3search 项目');
console.log('4. 点击 Settings 选项卡');
console.log('5. 在 Environment variables 部分添加以下变量：');
console.log('');

Object.entries(envVars).forEach(([key, value]) => {
  console.log(`   ${key} = ${value}`);
});

console.log('\n6. 保存变量后，重新部署项目');
console.log('7. 等待部署完成（通常需要1-2分钟）');

console.log('\n🔍 验证步骤：');
console.log('部署完成后，访问 https://web3search.pages.dev');
console.log('打开浏览器开发者工具，检查控制台日志：');
console.log('- 应该显示: 🌐 Real API Mode - Connecting to backend at https://web3search-api.marovole.workers.dev');
console.log('- 不应该有 API 连接错误');

console.log('\n⚡ 使用 Wrangler CLI 设置（可选）：');
console.log('如果已安装 wrangler，可以使用以下命令：');
console.log('');

Object.entries(envVars).forEach(([key, value]) => {
  console.log(`npx wrangler pages secret put ${key}`);
  console.log(`# 输入: ${value}`);
  console.log('');
});

console.log('✅ 修复完成后，系统将完全正常工作！');
console.log('🎉 Quick Chat 和 Deep Research 功能都将可用！');
