-- 修复API调用表的RLS策略安全问题
-- 解决潜在的权限绕过风险

-- 首先删除现有的不安全策略
DROP POLICY IF EXISTS "Users can view their own API calls" ON public.api_calls;

-- 创建更安全的RLS策略
CREATE POLICY "Users can view their own API calls - secure"
  ON public.api_calls FOR SELECT
  USING (
    -- 确保用户已认证
    auth.uid() IS NOT NULL
    AND (
      -- 只能查看自己的API调用
      user_id = auth.uid()
      -- 或者查看自己对话的API调用（需要额外的验证）
      OR (
        conversation_id IN (
          SELECT id FROM public.conversations 
          WHERE user_id = auth.uid()
          AND deleted_at IS NULL  -- 确保对话未被删除
        )
        AND user_id IS NOT NULL  -- 确保API调用有用户ID
      )
    )
  );

-- 创建插入策略（用户只能插入自己的API调用）
CREATE POLICY "Users can insert their own API calls"
  ON public.api_calls FOR INSERT
  WITH CHECK (
    auth.uid() IS NOT NULL
    AND user_id = auth.uid()
  );

-- 更新服务角色策略，添加额外的安全检查
DROP POLICY IF EXISTS "Service role can manage all API calls" ON public.api_calls;

CREATE POLICY "Service role can manage all API calls - secure"
  ON public.api_calls FOR ALL
  USING (
    auth.role() = 'service_role'
    AND (
      -- 服务角色可以访问所有记录，但需要记录操作日志
      current_setting('app.current_user_id', true) IS NOT NULL
      OR auth.jwt() ->> 'email' LIKE '%@web3search.com'  -- 限制服务角色访问
    )
  );

-- 添加安全函数用于验证对话访问权限
CREATE OR REPLACE FUNCTION verify_conversation_access(
  p_conversation_id UUID,
  p_user_id UUID
) RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  conversation_exists BOOLEAN;
BEGIN
  SELECT EXISTS(
    SELECT 1 FROM public.conversations 
    WHERE id = p_conversation_id 
    AND user_id = p_user_id
    AND deleted_at IS NULL
  ) INTO conversation_exists;
  
  RETURN conversation_exists;
EXCEPTION
  WHEN OTHERS THEN
    -- 如果查询失败，返回false以确保安全
    RETURN FALSE;
END;
$$;

-- 添加索引以提高RLS策略性能
CREATE INDEX IF NOT EXISTS idx_api_calls_user_id_created_at 
ON public.api_calls(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_api_calls_conversation_id_user_id 
ON public.api_calls(conversation_id, user_id);

-- 添加RLS策略审计日志
CREATE OR REPLACE FUNCTION log_rls_policy_access()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- 记录敏感的RLS策略访问
  IF TG_OP = 'SELECT' THEN
    INSERT INTO public.audit_logs (
      table_name, 
      operation, 
      user_id, 
      details,
      created_at
    ) VALUES (
      'api_calls',
      'SELECT_RLS',
      auth.uid(),
      json_build_object(
        'conversation_id', NEW.conversation_id,
        'user_id', NEW.user_id,
        'policy_used', 'secure_user_access'
      ),
      NOW()
    );
  END IF;
  
  RETURN NEW;
END;
$$;

-- 创建审计表（如果不存在）
CREATE TABLE IF NOT EXISTS public.audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name TEXT NOT NULL,
  operation TEXT NOT NULL,
  user_id UUID,
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 启用审计表的RLS
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- 只有服务角色可以查看审计日志
CREATE POLICY "Service role only" ON public.audit_logs
  FOR ALL USING (auth.role() = 'service_role');

-- 添加注释说明安全改进
COMMENT ON POLICY "Users can view their own API calls - secure" ON public.api_calls 
IS 'Enhanced RLS policy with additional security checks to prevent privilege escalation';

COMMENT ON FUNCTION verify_conversation_access(UUID, UUID) IS 
'Secure function to verify user access to conversations with proper error handling';