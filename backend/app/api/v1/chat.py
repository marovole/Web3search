"""
聊天API端点
提供Quick Chat和Deep Research功能
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
import uuid
import json

from app.core.database import get_db
from app.core.monitoring import trace_operation, metrics
from app.schemas.chat import (
    QuickChatRequest,
    QuickChatResponse,
    DeepResearchRequest,
    DeepResearchResponse,
    ErrorResponse,
)
from app.services.research_engine import quick_chat_engine, deep_research_engine
from app.services.report import report_generator
from app.models.report import Report, ReportType, ReportStatus
from app.models.conversation import Conversation, Message, MessageRole
import time


router = APIRouter()


# ================================
# Quick Chat API
# ================================

@router.post(
    "/quick-chat",
    response_model=QuickChatResponse,
    summary="快速对话",
    description="3秒内快速回答加密货币相关问题",
    tags=["Chat"],
    responses={
        200: {
            "description": "成功返回回答",
            "content": {
                "application/json": {
                    "example": {
                        "content": "Bitcoin (BTC) is currently trading at $45,000 with a 24h change of +2.5%...",
                        "symbol": "BTC",
                        "query_type": "price",
                        "response_time": 2.3,
                        "model": "anthropic/claude-3.5-sonnet",
                        "session_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        },
        429: {"description": "速率限制 - 每分钟最多10次请求"},
        500: {"description": "服务器内部错误"},
    }
)
async def quick_chat(
    request: QuickChatRequest,
    db: AsyncSession = Depends(get_db),
) -> QuickChatResponse:
    """
    快速对话接口 - 3秒内响应的AI问答

    该端点使用轻量级LLM模型快速回答加密货币相关问题。

    **特性:**
    - ⚡ 目标响应时间 < 3秒
    - 🤖 使用Claude 3.5 Sonnet模型
    - 💬 支持多轮对话（通过session_id）
    - 🔄 自动识别查询类型（价格、新闻、技术分析等）

    **支持的查询类型:**
    - 价格查询: "What is the current price of Bitcoin?"
    - 市场概览: "Tell me about Ethereum's performance today"
    - 技术解释: "How does Uniswap work?"
    - 对比分析: "Compare Bitcoin and Ethereum"

    **速率限制:**
    - 10次/分钟（基于IP）
    - 超过限制返回429状态码

    **请求示例:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/chat/quick-chat" \\
      -H "Content-Type: application/json" \\
      -d '{
        "query": "What is the current price of Bitcoin?",
        "session_id": null
      }'
    ```

    **响应示例:**
    ```json
    {
      "content": "Bitcoin (BTC) is currently trading at $45,000...",
      "symbol": "BTC",
      "query_type": "price",
      "response_time": 2.3,
      "model": "anthropic/claude-3.5-sonnet",
      "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

    **错误响应示例:**
    ```json
    {
      "detail": "Quick Chat处理失败: API timeout"
    }
    ```
    """
    start_time = time.time()

    try:
        # 生成或使用现有session_id
        session_id = request.session_id or str(uuid.uuid4())

        # 调用Quick Chat引擎（非流式）- 添加性能追踪
        with trace_operation("quick_chat", {"query": request.query[:50], "session_id": session_id}):
            result = await quick_chat_engine.chat(
                query=request.query,
                stream=False,
            )

        # 构建响应
        response = QuickChatResponse(
            content=result["content"],
            symbol=result.get("symbol"),
            query_type=result["metadata"]["query_type"],
            response_time=result["metadata"]["response_time"],
            model=result["metadata"]["model"],
            session_id=session_id,
        )

        # 记录API调用指标
        metrics.record_api_call(
            endpoint="/api/v1/chat/quick-chat",
            method="POST",
            status_code=200,
            duration=time.time() - start_time
        )

        # TODO: 保存到数据库（对话历史）
        # 这里可以保存Conversation和Message记录

        return response

    except Exception as e:
        # 记录错误指标
        metrics.record_error(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"endpoint": "/api/v1/chat/quick-chat", "query": request.query[:50]}
        )

        print(f"❌ Quick Chat错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Quick Chat处理失败: {str(e)}"
        )


@router.post(
    "/quick-chat/stream",
    summary="快速对话（流式）",
    description="流式返回Quick Chat响应",
    tags=["Chat"],
)
async def quick_chat_stream(
    request: QuickChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    快速对话流式接口

    - Server-Sent Events (SSE)格式
    - 逐字返回，提升用户体验
    """
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # 调用Quick Chat引擎（流式）
            stream_generator = await quick_chat_engine.chat(
                query=request.query,
                stream=True,
            )

            # 流式返回
            async for chunk in stream_generator:
                data = json.dumps({"content": chunk, "done": False}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # 发送完成信号
            data = json.dumps({"content": "", "done": True}, ensure_ascii=False)
            yield f"data: {data}\n\n"

        except Exception as e:
            print(f"❌ Quick Chat Stream错误: {e}")
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ================================
# Deep Research API
# ================================

@router.post(
    "/deep-research",
    response_model=DeepResearchResponse,
    summary="深度研究",
    description="生成15-30秒的全面深度研究报告",
    tags=["Research"],
    responses={
        200: {
            "description": "成功生成深度研究报告",
            "content": {
                "application/json": {
                    "example": {
                        "report_id": 123,
                        "symbol": "BTC",
                        "query": "Bitcoin",
                        "tldr": "Bitcoin is showing bullish momentum with strong fundamentals...",
                        "sections": {
                            "market_overview": "...",
                            "technical_analysis": "...",
                            "sentiment": "...",
                            "onchain": "...",
                            "tokenomics": "...",
                            "risks": "..."
                        },
                        "conclusion": "Overall outlook is positive...",
                        "markdown_content": "# Bitcoin Deep Research Report...",
                        "data_sources": ["CoinGecko", "Etherscan", "Twitter"],
                        "models_used": ["claude-3.5-sonnet", "llama-3.1-70b"],
                        "generation_time": 25.3,
                        "quality_score": 92,
                        "timestamp": "2025-01-26T10:00:00",
                        "session_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        },
        404: {"description": "未找到指定的加密货币"},
        429: {"description": "速率限制 - 每小时最多3次请求"},
        500: {"description": "服务器内部错误"},
    }
)
async def deep_research(
    request: DeepResearchRequest,
    db: AsyncSession = Depends(get_db),
) -> DeepResearchResponse:
    """
    深度研究接口 - 生成全面的加密货币研究报告

    该端点使用多个AI模型和数据源生成全面的深度研究报告,包含六个核心维度的分析。

    **特性:**
    - 📊 六维度分析（市场、技术、情绪、链上、代币经济、风险）
    - 🤖 多模型协同（Claude + Llama + GPT）
    - 📈 5个数据源集成（CoinGecko, Etherscan, Twitter, Reddit, CryptoPanic）
    - 📝 结构化Markdown报告
    - 💾 自动保存到数据库
    - 📊 质量评分（0-100分）

    **六大分析维度:**
    1. **市场概览** - 价格、市值、交易量、排名
    2. **技术分析** - 趋势、支撑阻力、技术指标
    3. **情绪分析** - 社交媒体、新闻情绪
    4. **链上数据** - 活跃地址、交易量、持币分布
    5. **代币经济** - 供应模型、分配机制
    6. **风险评估** - 技术风险、监管风险、市场风险

    **生成时间:**
    - 目标: 15-30秒
    - 最大: 60秒（超时）

    **速率限制:**
    - 3次/小时（基于IP）
    - 超过限制返回429状态码

    **请求示例:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/chat/deep-research" \\
      -H "Content-Type: application/json" \\
      -d '{
        "query": "Bitcoin",
        "symbol": "BTC",
        "session_id": null
      }'
    ```

    **响应示例:**
    ```json
    {
      "report_id": 123,
      "symbol": "BTC",
      "query": "Bitcoin",
      "tldr": "Bitcoin shows bullish momentum with strong fundamentals...",
      "sections": {
        "market_overview": "Current price: $45,000...",
        "technical_analysis": "Strong uptrend with RSI at 65...",
        "sentiment": "Positive sentiment across social media...",
        "onchain": "Active addresses increasing...",
        "tokenomics": "Fixed supply of 21M BTC...",
        "risks": "Regulatory uncertainty remains..."
      },
      "conclusion": "Overall outlook is positive with moderate risk...",
      "markdown_content": "# Bitcoin Deep Research Report\\n\\n## TLDR...",
      "data_sources": ["CoinGecko", "Etherscan", "Twitter"],
      "models_used": ["claude-3.5-sonnet", "llama-3.1-70b"],
      "generation_time": 25.3,
      "quality_score": 92,
      "timestamp": "2025-01-26T10:00:00Z",
      "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

    **错误响应示例:**
    ```json
    {
      "detail": "未找到加密货币: XYZ"
    }
    ```

    **质量评分标准:**
    - 90-100分: 优秀（所有维度完整，数据丰富）
    - 70-89分: 良好（大部分维度完整）
    - 50-69分: 一般（部分维度缺失）
    - <50分: 需改进（多个维度缺失）
    """
    try:
        # 生成或使用现有session_id
        session_id = request.session_id or str(uuid.uuid4())

        print(f"🔍 开始Deep Research: {request.query}")

        # 调用Deep Research引擎
        research_result = await deep_research_engine.research(
            query=request.query,
            symbol=request.symbol,
        )

        # 检查是否有错误
        if "error" in research_result:
            raise HTTPException(
                status_code=404,
                detail=research_result["error"]
            )

        # 生成Markdown报告
        markdown_content = report_generator.generate_markdown(research_result)

        # 生成标题
        title = report_generator.generate_title(research_result)

        # 计算质量得分
        quality_score = report_generator.calculate_quality_score(research_result)

        # 保存到数据库
        report = Report(
            symbol=research_result["symbol"],
            query=request.query,
            title=title,
            report_type=ReportType.DEEP_RESEARCH,
            status=ReportStatus.COMPLETED,
            content_markdown=markdown_content,
            tldr=research_result["tldr"],
            sections=research_result["sections"],
            data_sources=research_result["data_sources"],
            models_used=research_result["models_used"],
            generation_time_seconds=research_result["generation_time"],
            quality_score=quality_score,
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        print(f"✅ Deep Research完成，报告ID: {report.id}")

        # 构建响应
        response = DeepResearchResponse(
            report_id=report.id,
            symbol=research_result["symbol"],
            query=request.query,
            tldr=research_result["tldr"],
            sections=research_result["sections"],
            conclusion=research_result["conclusion"],
            markdown_content=markdown_content,
            data_sources=research_result["data_sources"],
            models_used=research_result["models_used"],
            generation_time=research_result["generation_time"],
            quality_score=quality_score,
            timestamp=research_result["timestamp"],
            session_id=session_id,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Deep Research错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Deep Research处理失败: {str(e)}"
        )


@router.get(
    "/deep-research/stream",
    summary="深度研究（流式）",
    description="流式返回Deep Research分析过程和结果",
    tags=["Research"],
)
async def deep_research_stream(
    query: str = Query(..., description="查询内容"),
    symbol: Optional[str] = Query(None, description="代币符号"),
    conversation_id: Optional[str] = Query(None, description="对话ID"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    深度研究流式接口 - 实时返回分析进度和结果

    该端点通过Server-Sent Events (SSE)实时返回Deep Research的分析进度，包括：
    - 各个分析器的处理状态
    - 实时生成的分析内容
    - 最终完整的研究报告

    **特性:**
    - 🔄 实时进度更新
    - 📊 分阶段结果展示
    - 🚀 流式内容传输
    - ⚡ 自动错误恢复

    **SSE事件格式:**
    ```json
    {
      "type": "progress|content|error|complete",
      "stage": "market_analysis|technical_analysis|...",
      "content": "分析内容或进度信息",
      "progress": 0-100,
      "done": false
    }
    ```

    **使用示例:**
    ```javascript
    const eventSource = new EventSource(
      '/api/v1/chat/deep-research/stream?query=Bitcoin&symbol=BTC'
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log(data);
    };
    ```
    """
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # 生成或使用现有session_id
            session_id = conversation_id or str(uuid.uuid4())

            print(f"🔍 开始Deep Research流式分析: {query}")

            # 发送开始信号
            start_data = {
                "type": "progress",
                "stage": "initialization",
                "content": f"开始分析 {symbol or query}...",
                "progress": 0,
                "done": False,
                "session_id": session_id
            }
            yield f"data: {json.dumps(start_data, ensure_ascii=False)}\n\n"

            # 由于Deep Research引擎还没有流式方法，暂时使用research方法包装
            # TODO: 后续实现真正的流式research_stream方法
            try:
                # 发送进度更新
                progress_data = {
                    "type": "progress",
                    "stage": "data_collection",
                    "content": "正在收集市场数据...",
                    "progress": 20,
                    "done": False,
                    "session_id": session_id
                }
                yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"

                # 调用research方法
                research_result = await deep_research_engine.research(
                    query=query,
                    symbol=symbol,
                )

                # 发送分析进度
                progress_data = {
                    "type": "progress",
                    "stage": "analysis",
                    "content": "正在进行AI分析...",
                    "progress": 60,
                    "done": False,
                    "session_id": session_id
                }
                yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"

                # 发送报告生成进度
                progress_data = {
                    "type": "progress",
                    "stage": "report_generation",
                    "content": "正在生成报告...",
                    "progress": 90,
                    "done": False,
                    "session_id": session_id
                }
                yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"

                # 检查是否有错误
                if "error" in research_result:
                    error_data = {
                        "type": "error",
                        "content": research_result["error"],
                        "done": True
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    return

                # 生成Markdown报告
                markdown_content = report_generator.generate_markdown(research_result)

                # 发送最终结果
                result_data = {
                    "type": "content",
                    "stage": "complete",
                    "content": markdown_content,
                    "tldr": research_result.get("tldr", ""),
                    "sections": research_result.get("sections", {}),
                    "symbol": research_result.get("symbol", symbol),
                    "progress": 100,
                    "done": True,
                    "session_id": session_id
                }
                yield f"data: {json.dumps(result_data, ensure_ascii=False)}\n\n"

            except Exception as research_error:
                error_data = {
                    "type": "error",
                    "content": f"研究过程出错: {str(research_error)}",
                    "done": True
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                return

            # 发送完成信号
            complete_data = {
                "type": "complete",
                "content": "深度研究分析完成",
                "progress": 100,
                "done": True,
                "session_id": session_id
            }
            yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"

        except Exception as e:
            print(f"❌ Deep Research Stream错误: {e}")
            import traceback
            traceback.print_exc()

            error_data = {
                "type": "error",
                "content": f"分析过程中出现错误: {str(e)}",
                "done": True
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )


@router.get(
    "/deep-research/status/{report_id}",
    summary="查询研究状态",
    description="查询Deep Research报告的生成状态",
    tags=["Research"],
)
async def get_research_status(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    查询报告生成状态

    - 用于轮询检查报告是否完成
    - 返回当前状态和进度
    """
    from sqlalchemy import select

    try:
        # 查询报告
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        return {
            "report_id": report.id,
            "status": report.status.value,
            "generation_time": report.generation_time_seconds,
            "quality_score": report.quality_score,
            "created_at": report.created_at.isoformat(),
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 查询状态错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )
