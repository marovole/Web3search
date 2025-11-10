/**
 * Cloudflare Pages Functions 中间件
 * 处理 API 代理和请求路由
 * 
 * 文档: https://developers.cloudflare.com/pages/platform/functions/
 */

interface Env {
  ASSETS: any;
}

export async function onRequest(context: {
  request: Request;
  env: Env;
  next: () => Promise<Response>;
}): Promise<Response> {
  const url = new URL(context.request.url);
  const pathname = url.pathname;

  // API 请求代理到后端
  if (pathname.startsWith('/api/')) {
    const backendUrl = 'https://web3search-api.marovole.workers.dev' + pathname + url.search;
    
    try {
      // 创建新的请求，保留原始请求的方法、头部和body
      const backendRequest = new Request(backendUrl, {
        method: context.request.method,
        headers: context.request.headers,
        body: context.request.method !== 'GET' && context.request.method !== 'HEAD' 
          ? context.request.body 
          : undefined,
      });

      const response = await fetch(backendRequest);
      
      // 添加 CORS 头部
      const headers = new Headers(response.headers);
      headers.set('Access-Control-Allow-Origin', '*');
      headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    } catch (error) {
      console.error('API proxy error:', error);
      return new Response(JSON.stringify({ 
        error: 'API proxy error',
        message: error instanceof Error ? error.message : 'Unknown error'
      }), {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  }

  // 对于其他请求，继续正常处理
  return context.next();
}
