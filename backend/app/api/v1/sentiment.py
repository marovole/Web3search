"""
社交情绪分析API端点
提供Web3项目社交情绪分析的RESTful API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

from app.services.social_sentiment_engine import social_sentiment_engine
from app.models.sentiment import SentimentAnalysis, KOLAnalysis, PlatformMetrics
from app.core.database import get_db
from app.core.config import settings
from app.schemas.sentiment import (
    SentimentRequest, SentimentResponse, 
    TrendingTopicsResponse, SentimentComparisonResponse,
    SentimentAlertResponse
)

router = APIRouter()


@router.post("/sentiment/analyze", response_model=SentimentResponse)
async def analyze_sentiment(
    request: SentimentRequest,
    db = Depends(get_db)
):
    """
    分析指定加密货币的综合社交情绪
    
    Args:
        request: 情感分析请求
        db: 数据库会话
        
    Returns:
        SentimentResponse: 情感分析结果
    """
    try:
        # 参数验证
        if not request.symbol or len(request.symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="币种符号不能为空")
        
        if request.time_range_hours < 1 or request.time_range_hours > 168:  # 最大7天
            raise HTTPException(status_code=400, detail="时间范围必须在1-168小时之间")
        
        # 执行情感分析
        result = await social_sentiment_engine.get_comprehensive_sentiment(
            symbol=request.symbol.upper(),
            hours=request.time_range_hours,
            platforms=request.platforms,
            include_kol=request.include_kol
        )
        
        # 保存到数据库（异步）
        if request.save_to_db:
            asyncio.create_task(_save_sentiment_to_db(result, db))
        
        return SentimentResponse(
            success=True,
            data=result,
            message="情感分析完成",
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"情感分析失败: {str(e)}"
        )


@router.get("/sentiment/{symbol}")
async def get_symbol_sentiment(
    symbol: str,
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    platforms: Optional[str] = Query(None, description="平台列表，用逗号分隔"),
    include_kol: bool = Query(True, description="是否包含KOL分析"),
    db = Depends(get_db)
):
    """
    获取指定币种的社交情绪分析
    
    Args:
        symbol: 币种符号
        hours: 时间范围
        platforms: 平台列表
        include_kol: 是否包含KOL分析
        db: 数据库会话
        
    Returns:
        Dict: 情感分析结果
    """
    try:
        # 解析平台列表
        platform_list = None
        if platforms:
            platform_list = [p.strip().lower() for p in platforms.split(',') if p.strip()]
            
            # 验证平台名称
            valid_platforms = ["twitter", "reddit", "telegram"]
            platform_list = [p for p in platform_list if p in valid_platforms]
            
            if not platform_list:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无效的平台名称，支持的平台: {', '.join(valid_platforms)}"
                )
        
        # 执行情感分析
        result = await social_sentiment_engine.get_comprehensive_sentiment(
            symbol=symbol.upper(),
            hours=hours,
            platforms=platform_list,
            include_kol=include_kol
        )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取情感分析失败: {str(e)}"
        )


@router.get("/sentiment/trending", response_model=TrendingTopicsResponse)
async def get_trending_topics(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    platforms: Optional[str] = Query(None, description="平台列表，用逗号分隔"),
    limit: int = Query(20, ge=1, le=100, description="返回结果数量限制"),
    db = Depends(get_db)
):
    """
    获取热门加密货币话题
    
    Args:
        hours: 时间范围
        platforms: 平台列表
        limit: 结果数量限制
        db: 数据库会话
        
    Returns:
        TrendingTopicsResponse: 热门话题响应
    """
    try:
        # 解析平台列表
        platform_list = None
        if platforms:
            platform_list = [p.strip().lower() for p in platforms.split(',') if p.strip()]
            
            valid_platforms = ["twitter", "reddit", "telegram"]
            platform_list = [p for p in platform_list if p in valid_platforms]
        
        # 获取热门话题
        result = await social_sentiment_engine.get_trending_topics(
            hours=hours,
            platforms=platform_list
        )
        
        # 限制结果数量
        result["topics"] = result["topics"][:limit]
        
        return TrendingTopicsResponse(
            success=True,
            data=result,
            message="热门话题获取完成",
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取热门话题失败: {str(e)}"
        )


@router.post("/sentiment/compare", response_model=SentimentComparisonResponse)
async def compare_sentiment(
    symbols: List[str],
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    db = Depends(get_db)
):
    """
    比较多个币种的情感分析
    
    Args:
        symbols: 币种符号列表
        hours: 时间范围
        db: 数据库会话
        
    Returns:
        SentimentComparisonResponse: 情感对比响应
    """
    try:
        # 参数验证
        if not symbols or len(symbols) == 0:
            raise HTTPException(status_code=400, detail="币种列表不能为空")
        
        if len(symbols) > 10:
            raise HTTPException(status_code=400, detail="最多同时比较10个币种")
        
        # 标准化币种符号
        normalized_symbols = [symbol.upper().strip() for symbol in symbols]
        
        # 执行对比分析
        result = await social_sentiment_engine.get_sentiment_comparison(
            symbols=normalized_symbols,
            hours=hours
        )
        
        return SentimentComparisonResponse(
            success=True,
            data=result,
            message="情感对比分析完成",
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"情感对比分析失败: {str(e)}"
        )


@router.get("/sentiment/history/{symbol}")
async def get_sentiment_history(
    symbol: str,
    days: int = Query(7, ge=1, le=30, description="历史天数"),
    db = Depends(get_db)
):
    """
    获取指定币种的历史情感数据
    
    Args:
        symbol: 币种符号
        days: 历史天数
        db: 数据库会话
        
    Returns:
        Dict: 历史情感数据
    """
    try:
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 从数据库查询历史数据
        history_query = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.symbol == symbol.upper(),
            SentimentAnalysis.created_at >= start_date,
            SentimentAnalysis.created_at <= end_date,
            SentimentAnalysis.platform == "comprehensive"  # 只查询综合数据
        ).order_by(SentimentAnalysis.created_at.desc()).all()
        
        # 格式化历史数据
        history_data = []
        for record in history_query:
            history_data.append({
                "date": record.created_at.isoformat(),
                "sentiment_score": record.sentiment_score,
                "confidence": record.confidence,
                "classification": record.classification,
                "volume": record.volume,
                "engagement": record.engagement,
                "sentiment_distribution": record.sentiment_distribution
            })
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "time_range_days": days,
                "history": history_data,
                "total_records": len(history_data)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取历史情感数据失败: {str(e)}"
        )


@router.get("/sentiment/alerts", response_model=SentimentAlertResponse)
async def get_sentiment_alerts(
    symbol: Optional[str] = Query(None, description="币种符号过滤"),
    severity: Optional[str] = Query(None, description="预警级别过滤"),
    is_active: Optional[bool] = Query(None, description="是否活跃"),
    limit: int = Query(50, ge=1, le=200, description="返回结果数量限制"),
    db = Depends(get_db)
):
    """
    获取情感预警列表
    
    Args:
        symbol: 币种符号过滤
        severity: 预警级别过滤
        is_active: 是否活跃
        limit: 结果数量限制
        db: 数据库会话
        
    Returns:
        SentimentAlertResponse: 情感预警响应
    """
    try:
        # 构建查询
        query = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.platform == "comprehensive"
        )
        
        if symbol:
            query = query.filter(SentimentAnalysis.symbol == symbol.upper())
        
        if is_active is not None:
            query = query.filter(SentimentAnalysis.is_active == is_active)
        
        # 执行查询
        alerts = query.order_by(
            SentimentAnalysis.created_at.desc()
        ).limit(limit).all()
        
        # 格式化预警数据
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "id": alert.id,
                "symbol": alert.symbol,
                "sentiment_score": alert.sentiment_score,
                "classification": alert.classification,
                "confidence": alert.confidence,
                "volume": alert.volume,
                "created_at": alert.created_at.isoformat(),
                "insights": alert.insights
            })
        
        return SentimentAlertResponse(
            success=True,
            data={
                "alerts": alert_data,
                "total_count": len(alert_data),
                "filters": {
                    "symbol": symbol,
                    "is_active": is_active
                }
            },
            message="情感预警获取完成",
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取情感预警失败: {str(e)}"
        )


@router.get("/sentiment/platforms")
async def get_platform_status(
    db = Depends(get_db)
):
    """
    获取各平台的状态和配置信息
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict: 平台状态信息
    """
    try:
        # 获取平台配置信息
        platforms = {
            "twitter": {
                "name": "Twitter",
                "enabled": settings.TWITTER_ENABLED,
                "rate_limit": 100,
                "weight": 0.4,
                "description": "社交媒体平台，实时讨论和情绪传播"
            },
            "reddit": {
                "name": "Reddit",
                "enabled": settings.REDDIT_ENABLED,
                "rate_limit": 60,
                "weight": 0.35,
                "description": "论坛平台，深度讨论和社区分析"
            },
            "telegram": {
                "name": "Telegram",
                "enabled": settings.TELEGRAM_ENABLED,
                "rate_limit": 30,
                "weight": 0.25,
                "description": "即时通讯平台，加密货币项目官方频道"
            }
        }
        
        # 获取最近的成功采集时间（简化实现）
        for platform_name in platforms:
            platforms[platform_name]["last_success"] = None
            platforms[platform_name]["error_count"] = 0
        
        return {
            "success": True,
            "data": {
                "platforms": platforms,
                "total_enabled": sum(1 for p in platforms.values() if p["enabled"]),
                "engine_status": "running"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取平台状态失败: {str(e)}"
        )


@router.get("/sentiment/stats")
async def get_sentiment_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db = Depends(get_db)
):
    """
    获取情感分析的统计数据
    
    Args:
        days: 统计天数
        db: 数据库会话
        
    Returns:
        Dict: 统计数据
    """
    try:
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 查询统计数据
        total_analyses = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.created_at >= start_date,
            SentimentAnalysis.platform == "comprehensive"
        ).count()
        
        # 按情感分类统计
        positive_count = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.created_at >= start_date,
            SentimentAnalysis.platform == "comprehensive",
            SentimentAnalysis.classification.in_(["positive", "strong_positive"])
        ).count()
        
        negative_count = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.created_at >= start_date,
            SentimentAnalysis.platform == "comprehensive",
            SentimentAnalysis.classification.in_(["negative", "strong_negative"])
        ).count()
        
        neutral_count = total_analyses - positive_count - negative_count
        
        # 计算平均值
        avg_sentiment = 0.0
        if total_analyses > 0:
            sentiment_sum = db.query(SentimentAnalysis).filter(
                SentimentAnalysis.created_at >= start_date,
                SentimentAnalysis.platform == "comprehensive"
            ).with_entities(SentimentAnalysis.sentiment_score).all()
            
            avg_sentiment = sum(s[0] for s in sentiment_sum) / len(sentiment_sum)
        
        # 热门币种统计
        popular_symbols = db.query(SentimentAnalysis.symbol, db.func.count(SentimentAnalysis.id)).filter(
            SentimentAnalysis.created_at >= start_date,
            SentimentAnalysis.platform == "comprehensive"
        ).group_by(SentimentAnalysis.symbol).order_by(
            db.func.count(SentimentAnalysis.id).desc()
        ).limit(10).all()
        
        stats = {
            "time_range_days": days,
            "total_analyses": total_analyses,
            "sentiment_distribution": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "positive_percentage": round(positive_count / total_analyses * 100, 1) if total_analyses > 0 else 0,
                "negative_percentage": round(negative_count / total_analyses * 100, 1) if total_analyses > 0 else 0,
                "neutral_percentage": round(neutral_count / total_analyses * 100, 1) if total_analyses > 0 else 0
            },
            "average_sentiment": round(avg_sentiment, 3),
            "popular_symbols": [
                {"symbol": symbol[0], "count": symbol[1]}
                for symbol in popular_symbols
            ]
        }
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取统计数据失败: {str(e)}"
        )


async def _save_sentiment_to_db(result: Dict[str, Any], db):
    """
    异步保存情感分析结果到数据库
    
    Args:
        result: 情感分析结果
        db: 数据库会话
    """
    try:
        # 保存主情感分析记录
        sentiment_record = SentimentAnalysis(
            symbol=result["symbol"],
            platform="comprehensive",
            sentiment_score=result["final_sentiment_score"],
            confidence=result["confidence"],
            classification=result["sentiment_classification"],
            volume=result["total_volume"],
            engagement=result["total_engagement"],
            sentiment_distribution=result["sentiment_distribution"],
            raw_data=result["platform_breakdown"],
            insights=result["insights"],
            time_range_hours=result["time_range_hours"]
        )
        
        db.add(sentiment_record)
        db.commit()
        db.refresh(sentiment_record)
        
        # 保存KOL分析（如果存在）
        if result.get("kol_analysis"):
            kol_data = result["kol_analysis"]
            kol_record = KOLAnalysis(
                sentiment_id=sentiment_record.id,
                kol_count=kol_data.get("kol_count", 0),
                positive_kol_count=kol_data.get("positive_kol_count", 0),
                negative_kol_count=kol_data.get("negative_kol_count", 0),
                neutral_kol_count=kol_data.get("neutral_kol_count", 0),
                weighted_sentiment_score=kol_data.get("weighted_sentiment_score", 0.0),
                total_engagement=kol_data.get("total_engagement", 0),
                kol_details=kol_data.get("kol_sentiments", [])
            )
            
            db.add(kol_record)
        
        # 保存平台指标
        for platform, data in result["platform_breakdown"].items():
            platform_record = PlatformMetrics(
                sentiment_id=sentiment_record.id,
                platform=platform,
                platform_sentiment_score=data["sentiment_score"],
                platform_volume=data["volume"],
                platform_engagement=data["engagement"],
                platform_weight=data["weight"],
                platform_data=data.get("data", {})
            )
            
            db.add(platform_record)
        
        db.commit()
        
    except Exception as e:
        print(f"⚠️ 保存情感分析数据到数据库失败: {e}")
        db.rollback()
