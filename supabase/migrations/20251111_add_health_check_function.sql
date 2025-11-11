-- 创建数据库健康检查函数
-- 用于快速测试数据库连接状态

CREATE OR REPLACE FUNCTION health_check()
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
  -- 简单的连接测试，不查询实际数据
  PERFORM 1;
  RETURN TRUE;
EXCEPTION
  WHEN OTHERS THEN
    RETURN FALSE;
END;
$$;

-- 添加注释
COMMENT ON FUNCTION health_check() IS '快速数据库健康检查函数，用于测试连接状态';