/**
 * 自动执行数据库迁移脚本
 * 使用Supabase客户端执行SQL
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createClient } from '@supabase/supabase-js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 从环境变量读取配置
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('❌ 错误: 未找到环境变量 SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

async function runMigration() {
  console.log('🚀 开始执行数据库迁移...\n');

  // 创建Supabase客户端（使用service role key以获得管理权限）
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });

  // 读取SQL文件
  const sqlFile = path.join(__dirname, '../supabase/FINAL_SAFE_MIGRATION.sql');
  console.log('📖 读取SQL文件:', sqlFile);

  const sql = fs.readFileSync(sqlFile, 'utf8');
  console.log('✅ SQL文件读取成功，共', sql.split('\n').length, '行\n');

  try {
    console.log('⚙️  执行SQL...');

    // 使用Supabase的RPC来执行原始SQL
    // 注意：这需要在数据库中创建一个执行SQL的函数
    // 但由于我们没有这个函数，我们需要分步执行

    // 方法：通过Supabase的REST API执行SQL
    const { data, error } = await supabase.rpc('exec_sql', { sql_query: sql });

    if (error) {
      console.error('❌ 执行失败:', error.message);
      console.error('详细信息:', error);
      process.exit(1);
    }

    console.log('\n✅ 迁移执行成功！');
    console.log('📊 结果:', data);

  } catch (err) {
    console.error('❌ 发生错误:', err.message);
    console.error(err);
    process.exit(1);
  }

  // 验证表是否创建成功
  console.log('\n🔍 验证数据库表...');

  const tables = [
    'conversations',
    'messages',
    'projects',
    'background_tasks',
    'deep_research_tasks',
    'reports',
    'api_calls_telemetry'
  ];

  for (const table of tables) {
    const { data, error } = await supabase
      .from(table)
      .select('id', { count: 'exact', head: true })
      .limit(1);

    if (error) {
      console.log(`❌ ${table} - 不存在或无法访问`);
    } else {
      console.log(`✅ ${table} - 已创建`);
    }
  }

  // 检查projects表数据
  console.log('\n🪙 检查项目数据...');
  const { data: projects, error: projectsError } = await supabase
    .from('projects')
    .select('symbol, name')
    .order('symbol');

  if (!projectsError && projects) {
    projects.forEach(p => {
      console.log(`  - ${p.symbol}: ${p.name}`);
    });
  }

  console.log('\n🎉 完成！');
}

runMigration().catch(err => {
  console.error('💥 未处理的错误:', err);
  process.exit(1);
});
