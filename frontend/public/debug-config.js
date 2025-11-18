// 调试脚本：检查实际加载的环境变量
console.log('=== Web3search 环境变量调试 ===');
console.log('VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
console.log('VITE_ENVIRONMENT:', import.meta.env.VITE_ENVIRONMENT);
console.log('VITE_USE_MOCK_API:', import.meta.env.VITE_USE_MOCK_API);

// 检查所有VITE开头的环境变量
Object.keys(import.meta.env).forEach(key => {
  if (key.startsWith('VITE_')) {
    console.log(`${key}:`, import.meta.env[key]);
  }
});

console.log('=== 调试结束 ===');
