#!/usr/bin/env python3
"""
部署诊断脚本
用于检查 Deep Research 和前端部署问题
"""
import requests
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# 配置
BACKEND_URL = "https://web3search-api.onrender.com"
FRONTEND_URL = "https://web3search.netlify.app"  # 或 Vercel URL

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def check_backend_health() -> bool:
    """检查后端健康状态"""
    print_info("检查后端健康状态...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            print_success(f"后端健康检查通过: {response.json()}")
            return True
        else:
            print_error(f"后端健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"后端连接失败: {e}")
        return False

def check_deep_research_endpoint() -> Dict[str, Any]:
    """检查 Deep Research 端点"""
    print_info("测试 Deep Research 端点...")
    try:
        # 先测试一个简单的请求
        payload = {
            "query": "Bitcoin",
            "symbol": "BTC"
        }
        
        print_info(f"发送请求到: {BACKEND_URL}/api/v1/chat/deep-research")
        print_info(f"请求载荷: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/chat/deep-research",
            json=payload,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        result = {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "headers": dict(response.headers),
        }
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:500]  # 只取前500字符
        
        if response.status_code == 200:
            print_success(f"Deep Research 请求成功")
        elif response.status_code == 500:
            print_error(f"Deep Research 返回 500 错误")
            print_error(f"响应: {json.dumps(result['response'], indent=2, ensure_ascii=False)}")
        else:
            print_warning(f"Deep Research 返回状态码: {response.status_code}")
            print_info(f"响应: {json.dumps(result['response'], indent=2, ensure_ascii=False)}")
        
        return result
        
    except requests.exceptions.Timeout:
        print_error("Deep Research 请求超时（60秒）")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print_error(f"Deep Research 请求异常: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def check_frontend_routes() -> Dict[str, Any]:
    """检查前端路由"""
    print_info("检查前端路由...")
    routes_to_check = [
        "/",
        "/chat",
        "/history",
        "/watchlist",
        "/settings",
    ]
    
    results = {}
    for route in routes_to_check:
        try:
            url = f"{FRONTEND_URL}{route}"
            print_info(f"检查路由: {route}")
            response = requests.get(url, timeout=10, allow_redirects=True)
            
            results[route] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "url": url,
            }
            
            if response.status_code == 200:
                print_success(f"  {route} -> 200 OK")
            elif response.status_code == 404:
                print_error(f"  {route} -> 404 Not Found")
            else:
                print_warning(f"  {route} -> {response.status_code}")
                
        except Exception as e:
            print_error(f"  {route} -> 异常: {e}")
            results[route] = {"success": False, "error": str(e)}
    
    return results

def check_api_docs() -> bool:
    """检查 API 文档"""
    print_info("检查 API 文档...")
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=10)
        if response.status_code == 200:
            print_success("API 文档可访问")
            return True
        else:
            print_warning(f"API 文档状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"API 文档不可访问: {e}")
        return False

def generate_report(results: Dict[str, Any]):
    """生成诊断报告"""
    print("\n" + "="*60)
    print("📊 部署诊断报告")
    print("="*60)
    print(f"时间: {datetime.now().isoformat()}")
    print(f"后端URL: {BACKEND_URL}")
    print(f"前端URL: {FRONTEND_URL}")
    print()
    
    # 后端健康检查
    if results.get("backend_health"):
        print_success("后端服务: 正常")
    else:
        print_error("后端服务: 异常")
    
    # API 文档
    if results.get("api_docs"):
        print_success("API 文档: 可访问")
    else:
        print_warning("API 文档: 不可访问")
    
    # Deep Research
    deep_research = results.get("deep_research", {})
    if deep_research.get("success"):
        print_success("Deep Research: 正常")
    else:
        print_error("Deep Research: 异常")
        if "response" in deep_research:
            print_error(f"  错误详情: {json.dumps(deep_research['response'], indent=2, ensure_ascii=False)}")
    
    # 前端路由
    frontend_routes = results.get("frontend_routes", {})
    failed_routes = [route for route, result in frontend_routes.items() if not result.get("success")]
    if not failed_routes:
        print_success("前端路由: 全部正常")
    else:
        print_error(f"前端路由: {len(failed_routes)} 个路由失败")
        for route in failed_routes:
            print_error(f"  - {route}")
    
    print("\n" + "="*60)
    
    # 保存报告到文件
    report_file = f"deployment_diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print_info(f"详细报告已保存到: {report_file}")

def main():
    """主函数"""
    print("🔍 开始部署诊断...\n")
    
    results = {}
    
    # 1. 检查后端健康状态
    results["backend_health"] = check_backend_health()
    print()
    
    # 2. 检查 API 文档
    results["api_docs"] = check_api_docs()
    print()
    
    # 3. 检查 Deep Research
    results["deep_research"] = check_deep_research_endpoint()
    print()
    
    # 4. 检查前端路由
    results["frontend_routes"] = check_frontend_routes()
    print()
    
    # 5. 生成报告
    generate_report(results)
    
    # 返回退出码
    if not results.get("backend_health") or not results.get("deep_research", {}).get("success"):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()

