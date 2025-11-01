"""
情绪分析WebSocket端点
提供实时情绪数据的WebSocket连接服务
"""
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse

from .connection_manager import connection_manager
from .message_handlers import message_handler
from .sentiment_broadcaster import sentiment_broadcaster

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/sentiment/{client_id}")
async def sentiment_websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    auto_connect: Optional[bool] = Query(True, description="是否自动连接广播器")
):
    """
    WebSocket端点 - 情绪数据实时推送

    Args:
        websocket: WebSocket连接
        client_id: 客户端ID
        auto_connect: 是否自动连接广播器
    """
    try:
        # 建立连接
        client_id = await connection_manager.connect(websocket, client_id)
        logger.info(f"WebSocket连接已建立: {client_id}")

        # 等待客户端消息
        while True:
            try:
                # 接收客户端消息
                message = await websocket.receive_text()

                # 处理消息
                await message_handler.handle_message(websocket, client_id, message)

            except WebSocketDisconnect:
                logger.info(f"WebSocket客户端主动断开: {client_id}")
                break
            except Exception as e:
                logger.error(f"处理客户端 {client_id} 消息时出错: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket连接出错: {e}")
    finally:
        # 清理连接
        await connection_manager.disconnect(client_id)


@router.get("/ws/status")
async def get_websocket_status():
    """
    获取WebSocket服务状态

    Returns:
        Dict: WebSocket服务状态信息
    """
    connection_stats = connection_manager.get_connection_stats()
    broadcast_stats = sentiment_broadcaster.get_broadcast_stats()

    return {
        "status": "running",
        "timestamp": connection_manager.connection_metadata.get("last_ping", ""),
        "websocket_endpoint": "/ws/sentiment/{client_id}",
        "connections": connection_stats,
        "broadcaster": broadcast_stats
    }


@router.post("/ws/broadcast/{symbol}")
async def force_broadcast(symbol: str):
    """
    强制广播指定币种的最新情绪数据

    Args:
        symbol: 币种符号

    Returns:
        Dict: 广播结果
    """
    success = await sentiment_broadcaster.force_broadcast_symbol(symbol)

    return {
        "success": success,
        "symbol": symbol,
        "message": f"强制广播 {symbol} {'成功' if success else '失败'}"
    }


@router.get("/ws/test")
async def websocket_test_page():
    """
    WebSocket测试页面

    Returns:
        HTMLResponse: 测试页面HTML
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket情绪数据测试</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .container {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .control-panel {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            button {
                padding: 8px 16px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background: #0056b3;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            input {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .status {
                padding: 10px;
                background: #f8f9fa;
                border-radius: 4px;
            }
            .connected {
                background: #d4edda;
                color: #155724;
            }
            .disconnected {
                background: #f8d7da;
                color: #721c24;
            }
            .data-display {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                background: #f8f9fa;
            }
            .message {
                margin: 5px 0;
                padding: 5px;
                border-left: 3px solid #007bff;
                background: white;
            }
            .error {
                border-left-color: #dc3545;
                background: #f8d7da;
            }
        </style>
    </head>
    <body>
        <h1>WebSocket情绪数据测试</h1>

        <div class="container">
            <div class="control-panel">
                <input type="text" id="clientId" placeholder="客户端ID (可选)" value="test-client">
                <button id="connectBtn">连接</button>
                <button id="disconnectBtn" disabled>断开</button>
            </div>

            <div class="control-panel">
                <input type="text" id="symbolInput" placeholder="币种符号 (如 BTC)" value="BTC">
                <button id="subscribeBtn" disabled>订阅</button>
                <button id="unsubscribeBtn" disabled>取消订阅</button>
                <button id="forceUpdateBtn" disabled>强制更新</button>
            </div>

            <div id="status" class="status disconnected">
                状态: 未连接
            </div>

            <div class="data-display">
                <h3>消息日志</h3>
                <div id="messages"></div>
            </div>
        </div>

        <script>
            let ws = null;
            let clientId = null;

            const connectBtn = document.getElementById('connectBtn');
            const disconnectBtn = document.getElementById('disconnectBtn');
            const subscribeBtn = document.getElementById('subscribeBtn');
            const unsubscribeBtn = document.getElementById('unsubscribeBtn');
            const forceUpdateBtn = document.getElementById('forceUpdateBtn');
            const symbolInput = document.getElementById('symbolInput');
            const clientIdInput = document.getElementById('clientId');
            const statusDiv = document.getElementById('status');
            const messagesDiv = document.getElementById('messages');

            function addMessage(message, isError = false) {
                const messageDiv = document.createElement('div');
                messageDiv.className = isError ? 'message error' : 'message';
                messageDiv.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${message}`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function updateStatus(connected) {
                if (connected) {
                    statusDiv.className = 'status connected';
                    statusDiv.textContent = `状态: 已连接 (客户端: ${clientId})`;
                    connectBtn.disabled = true;
                    disconnectBtn.disabled = false;
                    subscribeBtn.disabled = false;
                    unsubscribeBtn.disabled = false;
                    forceUpdateBtn.disabled = false;
                } else {
                    statusDiv.className = 'status disconnected';
                    statusDiv.textContent = '状态: 未连接';
                    connectBtn.disabled = false;
                    disconnectBtn.disabled = true;
                    subscribeBtn.disabled = true;
                    unsubscribeBtn.disabled = true;
                    forceUpdateBtn.disabled = true;
                }
            }

            connectBtn.addEventListener('click', () => {
                clientId = clientIdInput.value || 'test-client';
                const wsUrl = `ws://localhost:8000/api/v1/ws/sentiment/${clientId}`;

                try {
                    ws = new WebSocket(wsUrl);

                    ws.onopen = () => {
                        addMessage(`WebSocket连接已建立: ${clientId}`);
                        updateStatus(true);
                    };

                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        addMessage(`收到消息: ${JSON.stringify(data, null, 2)}`);
                    };

                    ws.onclose = () => {
                        addMessage('WebSocket连接已关闭');
                        updateStatus(false);
                    };

                    ws.onerror = (error) => {
                        addMessage(`WebSocket错误: ${error}`, true);
                        updateStatus(false);
                    };
                } catch (error) {
                    addMessage(`连接失败: ${error}`, true);
                }
            });

            disconnectBtn.addEventListener('click', () => {
                if (ws) {
                    ws.close();
                    updateStatus(false);
                }
            });

            subscribeBtn.addEventListener('click', () => {
                const symbol = symbolInput.value.trim().toUpperCase();
                if (!symbol) {
                    addMessage('请输入币种符号', true);
                    return;
                }

                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        symbol: symbol
                    }));
                    addMessage(`发送订阅请求: ${symbol}`);
                }
            });

            unsubscribeBtn.addEventListener('click', () => {
                const symbol = symbolInput.value.trim().toUpperCase();
                if (!symbol) {
                    addMessage('请输入币种符号', true);
                    return;
                }

                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'unsubscribe',
                        symbol: symbol
                    }));
                    addMessage(`发送取消订阅请求: ${symbol}`);
                }
            });

            forceUpdateBtn.addEventListener('click', () => {
                const symbol = symbolInput.value.trim().toUpperCase();
                if (!symbol) {
                    addMessage('请输入币种符号', true);
                    return;
                }

                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'force_update',
                        symbol: symbol
                    }));
                    addMessage(`发送强制更新请求: ${symbol}`);
                }
            });

            // 定期发送ping消息
            setInterval(() => {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'ping' }));
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# 启动和停止广播器的生命周期管理
@router.on_event("startup")
async def startup_event():
    """应用启动时启动广播器"""
    await sentiment_broadcaster.start()
    logger.info("WebSocket情绪数据广播器已启动")


@router.on_event("shutdown")
async def shutdown_event():
    """应用关闭时停止广播器"""
    await sentiment_broadcaster.stop()
    logger.info("WebSocket情绪数据广播器已停止")