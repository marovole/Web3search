import { SupabaseClient } from '@supabase/supabase-js'
import type { Conversation, Message } from '../types/chat'

/**
 * 对话管理模块
 * 处理对话和消息的数据库操作
 */

/**
 * 创建新对话
 */
export async function createConversation(
  supabase: SupabaseClient,
  sessionId: string,
  userId?: string
): Promise<Conversation> {
  const { data, error } = await supabase
    .from('conversations')
    .insert({
      session_id: sessionId,
      user_id: userId,
      message_count: 0,
      total_tokens: 0,
      is_active: true,
    })
    .select()
    .single()

  if (error) {
    throw new Error(`Failed to create conversation: ${error.message}`)
  }

  return {
    id: data.session_id,
    user_id: data.user_id,
    created_at: data.created_at,
    updated_at: data.last_activity,
  }
}

/**
 * 获取或创建对话
 * 如果 conversation_id 存在，返回现有对话；否则创建新对话
 */
export async function getOrCreateConversation(
  supabase: SupabaseClient,
  conversationId?: string,
  userId?: string
): Promise<{ conversation: Conversation; isNew: boolean }> {
  // 如果提供了 conversation_id，尝试查找
  if (conversationId) {
    const { data } = await supabase
      .from('conversations')
      .select('*')
      .eq('session_id', conversationId)
      .single()

    if (data) {
      return {
        conversation: {
          id: data.session_id,
          user_id: data.user_id,
          created_at: data.created_at,
          updated_at: data.last_activity,
        },
        isNew: false,
      }
    }
  }

  // 创建新对话
  const sessionId = conversationId || crypto.randomUUID()
  const conversation = await createConversation(supabase, sessionId, userId)

  return { conversation, isNew: true }
}

/**
 * 保存消息到数据库
 */
export async function saveMessage(
  supabase: SupabaseClient,
  conversationId: string,
  role: 'user' | 'assistant' | 'system',
  content: string,
  model?: string,
  tokenCount?: number
): Promise<Message> {
  // 获取 conversation 的内部 ID
  const { data: conv } = await supabase
    .from('conversations')
    .select('id')
    .eq('session_id', conversationId)
    .single()

  if (!conv) {
    throw new Error('Conversation not found')
  }

  const { data, error } = await supabase
    .from('messages')
    .insert({
      conversation_id: conv.id,
      role,
      content,
      model,
      token_count: tokenCount,
    })
    .select()
    .single()

  if (error) {
    throw new Error(`Failed to save message: ${error.message}`)
  }

  return {
    id: data.id.toString(),
    conversation_id: conversationId,
    role: data.role,
    content: data.content,
    model: data.model,
    tokens: data.token_count,
    created_at: data.created_at,
  }
}

/**
 * 查询对话历史消息
 */
export async function getConversationMessages(
  supabase: SupabaseClient,
  conversationId: string,
  limit: number = 50
): Promise<Message[]> {
  // 获取 conversation 的内部 ID
  const { data: conv } = await supabase
    .from('conversations')
    .select('id')
    .eq('session_id', conversationId)
    .single()

  if (!conv) {
    return []
  }

  const { data, error } = await supabase
    .from('messages')
    .select('*')
    .eq('conversation_id', conv.id)
    .order('created_at', { ascending: true })
    .limit(limit)

  if (error) {
    console.error('Failed to fetch messages:', error)
    return []
  }

  return data.map((msg) => ({
    id: msg.id.toString(),
    conversation_id: conversationId,
    role: msg.role,
    content: msg.content,
    model: msg.model,
    tokens: msg.token_count,
    created_at: msg.created_at,
  }))
}

/**
 * 更新对话的最后活动时间和统计信息
 */
export async function updateConversationStats(
  supabase: SupabaseClient,
  conversationId: string,
  additionalTokens: number
): Promise<void> {
  const { data: conv } = await supabase
    .from('conversations')
    .select('id, message_count, total_tokens')
    .eq('session_id', conversationId)
    .single()

  if (!conv) {
    return
  }

  await supabase
    .from('conversations')
    .update({
      message_count: conv.message_count + 1,
      total_tokens: conv.total_tokens + additionalTokens,
      last_activity: new Date().toISOString(),
    })
    .eq('id', conv.id)
}
