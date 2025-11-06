"""
极简版 FastAPI 应用
Web3 Search - 加密货币AI搜索引擎
"""
from datetime import datetime
from fastapi import FastAPI

# 创建最简单的 FastAPI 应用
app = FastAPI(
    title="Web3 Search API",
    version="1.0.0",
    description="Web3 Search API - Emergency Mode"
)

@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "status": "healthy",
        "service": "web3search_backend",
        "mode": "emergency",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "web3search_backend",
        "mode": "emergency",
        "timestamp": datetime.now().isoformat()
    }

# 如果这个文件被直接运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
