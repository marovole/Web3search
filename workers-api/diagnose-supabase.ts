// 快速诊断Supabase连接
import 'dotenv/config'
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = process.env.SUPABASE_URL || ''
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || ''

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('❌ 错误: 未找到环境变量 SUPABASE_URL 或 SUPABASE_ANON_KEY')
  process.exit(1)
}

async function testConnection() {
  console.log('🔍 诊断Supabase连接...')
  console.log('URL:', SUPABASE_URL)
  console.log('Key:', SUPABASE_ANON_KEY.substring(0, 20) + '...')

  try {
    const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        persistSession: false,
        autoRefreshToken: false,
      },
    })

    console.log('\n✅ 客户端创建成功')

    // 尝试简单查询
    console.log('\n🔎 测试数据库查询...')
    const { data, error } = await supabase
      .from('projects')
      .select('id')
      .limit(1)

    if (error) {
      console.error('❌ 查询失败:', error.message)
      console.error('错误详情:', JSON.stringify(error, null, 2))
    } else {
      console.log('✅ 查询成功! 数据:', data)
    }
  } catch (error) {
    console.error('❌ 连接失败:', error)
  }
}

testConnection()
