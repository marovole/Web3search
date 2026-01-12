/**
 * 测试Supabase数据库连接
 */

import 'dotenv/config';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('❌ 错误: 未找到环境变量 SUPABASE_URL 或 SUPABASE_ANON_KEY');
  process.exit(1);
}

async function testConnection() {
  console.log('🔍 测试数据库连接...\n');

  const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });

  // 测试1: 查询conversations表
  console.log('📊 测试1: 查询conversations表...');
  try {
    const { data, error } = await supabase
      .from('conversations')
      .select('id', { count: 'exact', head: true })
      .limit(1);

    if (error) {
      console.log('❌ 失败:', error.message);
      console.log('详情:', error);
    } else {
      console.log('✅ 成功! 表存在且可访问');
    }
  } catch (err) {
    console.log('❌ 异常:', err.message);
  }

  // 测试2: 查询projects表
  console.log('\n📊 测试2: 查询projects表...');
  try {
    const { data, error } = await supabase
      .from('projects')
      .select('symbol, name')
      .limit(5);

    if (error) {
      console.log('❌ 失败:', error.message);
    } else {
      console.log('✅ 成功! 找到', data.length, '个项目:');
      data.forEach(p => console.log(`  - ${p.symbol}: ${p.name}`));
    }
  } catch (err) {
    console.log('❌ 异常:', err.message);
  }

  // 测试3: 检查表权限
  console.log('\n📊 测试3: 检查RLS策略...');
  try {
    // 尝试选择，看看是否有权限问题
    const { data, error, count } = await supabase
      .from('conversations')
      .select('*', { count: 'exact' });

    if (error) {
      console.log('❌ RLS可能阻止了访问:', error.message);
      console.log('   提示: 可能需要调整RLS策略');
    } else {
      console.log('✅ 成功! 找到', count, '条记录');
    }
  } catch (err) {
    console.log('❌ 异常:', err.message);
  }

  console.log('\n✅ 测试完成！');
}

testConnection().catch(err => {
  console.error('💥 未处理的错误:', err);
  process.exit(1);
});
