/**
 * Cloudflare Pages Functions 中间件
 * 移除API代理，让前端直接调用后端
 */

export async function onRequest(context: {
  request: Request;
  env: Env;
  next: () => Promise<Response>;
}): Promise<Response> {
  // 直接传递所有请求，不进行代理
  return context.next();
}
