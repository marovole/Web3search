"""
缓存策略和CDN配置优化系统
提供智能缓存策略、CDN优化建议、缓存性能监控和自动优化配置
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import statistics
import random
import math
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheType(Enum):
    """缓存类型"""
    BROWSER_CACHE = "browser_cache"
    CDN_CACHE = "cdn_cache"
    EDGE_CACHE = "edge_cache"
    API_CACHE = "api_cache"
    DATABASE_CACHE = "database_cache"
    MEMORY_CACHE = "memory_cache"
    REDIS_CACHE = "redis_cache"

class CacheStrategy(Enum):
    """缓存策略"""
    CACHE_FIRST = "cache_first"
    NETWORK_FIRST = "network_first"
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"
    STALE_IF_ERROR = "stale_if_error"
    CACHE_ONLY = "cache_only"
    NETWORK_ONLY = "network_only"

class ResourceType(Enum):
    """资源类型"""
    HTML = "html"
    CSS = "css"
    JAVASCRIPT = "javascript"
    IMAGE = "image"
    FONT = "font"
    API_RESPONSE = "api_response"
    STATIC_ASSET = "static_asset"
    DYNAMIC_CONTENT = "dynamic_content"

@dataclass
class CacheRule:
    """缓存规则"""
    id: str
    resource_type: ResourceType
    cache_type: CacheType
    strategy: CacheStrategy
    max_age: int  # 秒
    stale_while_revalidate: int  # 秒
    stale_if_error: int  # 秒
    must_revalidate: bool
    no_cache: bool
    no_store: bool
    public: bool
    private: bool
    etag_enabled: bool
    last_modified_enabled: bool
    compression_enabled: bool
    vary_headers: List[str]

@dataclass
class CDNConfiguration:
    """CDN配置"""
    provider: str  # cloudflare, aws_cloudfront, fastly, etc.
    distribution_id: str
    domain_name: str
    cache_key_policy: Dict[str, Any]
    origin_configuration: Dict[str, Any]
    behavior_rules: List[Dict[str, Any]]
    geo_restrictions: Dict[str, Any]
    security_settings: Dict[str, Any]
    compression_settings: Dict[str, Any]
    edge_functions: List[Dict[str, Any]]

@dataclass
class CachePerformanceMetrics:
    """缓存性能指标"""
    cache_type: CacheType
    hit_rate: float  # 命中率
    miss_rate: float  # 未命中率
    avg_response_time: float  # 平均响应时间
    bandwidth_saved: float  # 节省带宽
    cache_size: float  # 缓存大小
    eviction_rate: float  # 驱逐率
    ttl_efficiency: float  # TTL效率

@dataclass
class CacheOptimizationRecommendation:
    """缓存优化建议"""
    id: str
    category: str  # strategy, configuration, performance, cost
    priority: str  # high, medium, low
    title: str
    description: str
    current_config: Dict[str, Any]
    recommended_config: Dict[str, Any]
    expected_improvement: Dict[str, float]
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high

class CacheStrategyOptimizer:
    """缓存策略优化器"""
    
    def __init__(self):
        self.resource_patterns = self._initialize_resource_patterns()
        self.cache_rules = self._initialize_default_rules()
        
    def optimize_cache_rules(self, performance_metrics: Dict[str, CachePerformanceMetrics],
                            current_rules: List[CacheRule]) -> Tuple[List[CacheRule], List[CacheOptimizationRecommendation]]:
        """优化缓存规则"""
        print("🔧 Optimizing cache rules based on performance metrics...")
        
        recommendations = []
        optimized_rules = []
        
        # 分析每个资源类型的性能
        for rule in current_rules:
            optimized_rule, rule_recommendations = self._optimize_single_rule(rule, performance_metrics)
            optimized_rules.append(optimized_rule)
            recommendations.extend(rule_recommendations)
        
        # 生成新的缓存规则
        new_rules = self._generate_missing_rules(performance_metrics)
        optimized_rules.extend(new_rules)
        
        print(f"✅ Generated {len(optimized_rules)} optimized cache rules")
        print(f"💡 Generated {len(recommendations)} optimization recommendations")
        
        return optimized_rules, recommendations
    
    def _optimize_single_rule(self, rule: CacheRule, 
                             performance_metrics: Dict[str, CachePerformanceMetrics]) -> Tuple[CacheRule, List[CacheOptimizationRecommendation]]:
        """优化单个缓存规则"""
        recommendations = []
        optimized_rule = rule
        
        # 获取相关性能指标
        cache_metrics = performance_metrics.get(rule.cache_type.value)
        if not cache_metrics:
            return optimized_rule, recommendations
        
        # 命中率优化
        if cache_metrics.hit_rate < 0.7:  # 命中率低于70%
            if rule.resource_type in [ResourceType.CSS, ResourceType.JAVASCRIPT, ResourceType.IMAGE]:
                # 静态资源可以增加缓存时间
                new_max_age = min(rule.max_age * 2, 31536000)  # 最多1年
                optimized_rule.max_age = new_max_age
                
                recommendations.append(CacheOptimizationRecommendation(
                    id=f"increase_cache_age_{rule.id}",
                    category="strategy",
                    priority="high",
                    title=f"Increase Cache TTL for {rule.resource_type.value}",
                    description=f"Current hit rate is {cache_metrics.hit_rate:.1%}, increasing TTL can improve cache efficiency",
                    current_config={"max_age": rule.max_age},
                    recommended_config={"max_age": new_max_age},
                    expected_improvement={"hit_rate_increase": 0.15, "bandwidth_saved": 0.1},
                    implementation_effort="low",
                    risk_level="low"
                ))
        
        # 响应时间优化
        if cache_metrics.avg_response_time > 100:  # 响应时间超过100ms
            if rule.strategy != CacheStrategy.CACHE_FIRST:
                optimized_rule.strategy = CacheStrategy.CACHE_FIRST
                
                recommendations.append(CacheOptimizationRecommendation(
                    id=f"switch_to_cache_first_{rule.id}",
                    category="strategy",
                    priority="medium",
                    title=f"Switch to Cache-First Strategy for {rule.resource_type.value}",
                    description=f"Current response time is {cache_metrics.avg_response_time:.0f}ms, cache-first can reduce latency",
                    current_config={"strategy": rule.strategy.value},
                    recommended_config={"strategy": CacheStrategy.CACHE_FIRST.value},
                    expected_improvement={"response_time_reduction": 0.3, "hit_rate_increase": 0.1},
                    implementation_effort="medium",
                    risk_level="low"
                ))
        
        # 启用压缩
        if not rule.compression_enabled and rule.resource_type in [ResourceType.JAVASCRIPT, ResourceType.CSS, ResourceType.HTML]:
            optimized_rule.compression_enabled = True
            
            recommendations.append(CacheOptimizationRecommendation(
                id=f"enable_compression_{rule.id}",
                category="performance",
                priority="high",
                title=f"Enable Compression for {rule.resource_type.value}",
                description="Compression can reduce bandwidth usage by 60-80%",
                current_config={"compression_enabled": False},
                recommended_config={"compression_enabled": True},
                expected_improvement={"bandwidth_saved": 0.7, "response_time_reduction": 0.2},
                implementation_effort="low",
                risk_level="low"
            ))
        
        # 启用ETag
        if not rule.etag_enabled and rule.resource_type != ResourceType.DYNAMIC_CONTENT:
            optimized_rule.etag_enabled = True
            
            recommendations.append(CacheOptimizationRecommendation(
                id=f"enable_etag_{rule.id}",
                category="strategy",
                priority="medium",
                title=f"Enable ETag for {rule.resource_type.value}",
                description="ETag enables conditional requests and saves bandwidth",
                current_config={"etag_enabled": False},
                recommended_config={"etag_enabled": True},
                expected_improvement={"bandwidth_saved": 0.3, "conditional_requests": 0.8},
                implementation_effort="low",
                risk_level="low"
            ))
        
        return optimized_rule, recommendations
    
    def _generate_missing_rules(self, performance_metrics: Dict[str, CachePerformanceMetrics]) -> List[CacheRule]:
        """生成缺失的缓存规则"""
        missing_rules = []
        
        # 检查API缓存规则
        api_cache_exists = any(rule.resource_type == ResourceType.API_RESPONSE for rule in self.cache_rules)
        if not api_cache_exists:
            missing_rules.append(CacheRule(
                id="api_response_cache",
                resource_type=ResourceType.API_RESPONSE,
                cache_type=CacheType.API_CACHE,
                strategy=CacheStrategy.STALE_WHILE_REVALIDATE,
                max_age=300,  # 5分钟
                stale_while_revalidate=60,
                stale_if_error=86400,  # 1天
                must_revalidate=True,
                no_cache=False,
                no_store=False,
                public=False,
                private=True,
                etag_enabled=True,
                last_modified_enabled=True,
                compression_enabled=True,
                vary_headers=["Accept", "Authorization"]
            ))
            
            print("📋 Added API response cache rule")
        
        # 检查字体缓存规则
        font_cache_exists = any(rule.resource_type == ResourceType.FONT for rule in self.cache_rules)
        if not font_cache_exists:
            missing_rules.append(CacheRule(
                id="font_cache",
                resource_type=ResourceType.FONT,
                cache_type=CacheType.CDN_CACHE,
                strategy=CacheStrategy.CACHE_FIRST,
                max_age=31536000,  # 1年
                stale_while_revalidate=2592000,  # 30天
                stale_if_error=31536000,
                must_revalidate=False,
                no_cache=False,
                no_store=False,
                public=True,
                private=False,
                etag_enabled=True,
                last_modified_enabled=False,
                compression_enabled=False,  # 字体文件通常已压缩
                vary_headers=["Origin"]
            ))
            
            print("📋 Added font cache rule")
        
        return missing_rules
    
    def _initialize_resource_patterns(self) -> Dict[ResourceType, Dict[str, Any]]:
        """初始化资源模式"""
        return {
            ResourceType.HTML: {
                "extensions": [".html", ".htm"],
                "mime_types": ["text/html"],
                "default_ttl": 3600,  # 1小时
                "cacheable": True,
                "compressible": True
            },
            ResourceType.CSS: {
                "extensions": [".css"],
                "mime_types": ["text/css"],
                "default_ttl": 86400,  # 1天
                "cacheable": True,
                "compressible": True
            },
            ResourceType.JAVASCRIPT: {
                "extensions": [".js", ".mjs"],
                "mime_types": ["application/javascript", "text/javascript"],
                "default_ttl": 86400,  # 1天
                "cacheable": True,
                "compressible": True
            },
            ResourceType.IMAGE: {
                "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
                "mime_types": ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"],
                "default_ttl": 2592000,  # 30天
                "cacheable": True,
                "compressible": False  # 图片已压缩
            },
            ResourceType.FONT: {
                "extensions": [".woff", ".woff2", ".ttf", ".otf", ".eot"],
                "mime_types": ["font/woff", "font/woff2", "font/ttf", "font/otf"],
                "default_ttl": 31536000,  # 1年
                "cacheable": True,
                "compressible": False
            },
            ResourceType.API_RESPONSE: {
                "extensions": [],
                "mime_types": ["application/json", "application/xml"],
                "default_ttl": 300,  # 5分钟
                "cacheable": True,
                "compressible": True
            }
        }
    
    def _initialize_default_rules(self) -> List[CacheRule]:
        """初始化默认缓存规则"""
        return [
            CacheRule(
                id="html_cache",
                resource_type=ResourceType.HTML,
                cache_type=CacheType.BROWSER_CACHE,
                strategy=CacheStrategy.STALE_WHILE_REVALIDATE,
                max_age=3600,
                stale_while_revalidate=300,
                stale_if_error=86400,
                must_revalidate=True,
                no_cache=False,
                no_store=False,
                public=True,
                private=False,
                etag_enabled=True,
                last_modified_enabled=True,
                compression_enabled=True,
                vary_headers=["Accept-Encoding"]
            ),
            CacheRule(
                id="css_cache",
                resource_type=ResourceType.CSS,
                cache_type=CacheType.CDN_CACHE,
                strategy=CacheStrategy.CACHE_FIRST,
                max_age=86400,
                stale_while_revalidate=3600,
                stale_if_error=604800,
                must_revalidate=False,
                no_cache=False,
                no_store=False,
                public=True,
                private=False,
                etag_enabled=True,
                last_modified_enabled=False,
                compression_enabled=True,
                vary_headers=["Accept-Encoding"]
            ),
            CacheRule(
                id="javascript_cache",
                resource_type=ResourceType.JAVASCRIPT,
                cache_type=CacheType.CDN_CACHE,
                strategy=CacheStrategy.CACHE_FIRST,
                max_age=86400,
                stale_while_revalidate=3600,
                stale_if_error=604800,
                must_revalidate=False,
                no_cache=False,
                no_store=False,
                public=True,
                private=False,
                etag_enabled=True,
                last_modified_enabled=False,
                compression_enabled=True,
                vary_headers=["Accept-Encoding"]
            ),
            CacheRule(
                id="image_cache",
                resource_type=ResourceType.IMAGE,
                cache_type=CacheType.CDN_CACHE,
                strategy=CacheStrategy.CACHE_FIRST,
                max_age=2592000,
                stale_while_revalidate=86400,
                stale_if_error=31536000,
                must_revalidate=False,
                no_cache=False,
                no_store=False,
                public=True,
                private=False,
                etag_enabled=True,
                last_modified_enabled=False,
                compression_enabled=False,
                vary_headers=["Accept", "Accept-Encoding"]
            )
        ]

class CDNOptimizer:
    """CDN优化器"""
    
    def __init__(self):
        self.cdn_providers = self._initialize_cdn_providers()
        self.optimization_presets = self._initialize_optimization_presets()
    
    def optimize_cdn_configuration(self, current_config: CDNConfiguration,
                                   performance_metrics: Dict[str, Any]) -> Tuple[CDNConfiguration, List[CacheOptimizationRecommendation]]:
        """优化CDN配置"""
        print("🌐 Optimizing CDN configuration...")
        
        recommendations = []
        optimized_config = current_config
        
        # 缓存键策略优化
        cache_key_recommendations = self._optimize_cache_key_policy(optimized_config, performance_metrics)
        recommendations.extend(cache_key_recommendations)
        
        # 压缩设置优化
        compression_recommendations = self._optimize_compression_settings(optimized_config, performance_metrics)
        recommendations.extend(compression_recommendations)
        
        # 地理限制优化
        geo_recommendations = self._optimize_geo_restrictions(optimized_config, performance_metrics)
        recommendations.extend(geo_recommendations)
        
        # 边缘函数优化
        edge_recommendations = self._optimize_edge_functions(optimized_config, performance_metrics)
        recommendations.extend(edge_recommendations)
        
        print(f"✅ Generated {len(recommendations)} CDN optimization recommendations")
        
        return optimized_config, recommendations
    
    def _optimize_cache_key_policy(self, config: CDNConfiguration, 
                                  performance_metrics: Dict[str, Any]) -> List[CacheOptimizationRecommendation]:
        """优化缓存键策略"""
        recommendations = []
        
        # 检查是否包含查询参数
        if "query_strings" not in config.cache_key_policy:
            config.cache_key_policy["query_strings"] = "none"  # 忽略查询参数以提高缓存命中率
            
            recommendations.append(CacheOptimizationRecommendation(
                id="cdn_cache_key_query_params",
                category="configuration",
                priority="high",
                title="Optimize Cache Key Policy for Query Parameters",
                description="Ignoring query parameters can significantly increase cache hit rate",
                current_config={"query_strings": "all"},
                recommended_config={"query_strings": "none"},
                expected_improvement={"hit_rate_increase": 0.2, "bandwidth_saved": 0.15},
                implementation_effort="low",
                risk_level="medium"
            ))
        
        # 检查HTTP头缓存键
        if "headers" not in config.cache_key_policy:
            config.cache_key_policy["headers"] = ["Accept-Encoding", "Origin"]
            
            recommendations.append(CacheOptimizationRecommendation(
                id="cdn_cache_key_headers",
                category="configuration",
                priority="medium",
                title="Optimize Cache Key Policy for HTTP Headers",
                description="Include only necessary headers in cache key to improve hit rate",
                current_config={"headers": "all"},
                recommended_config={"headers": ["Accept-Encoding", "Origin"]},
                expected_improvement={"hit_rate_increase": 0.1},
                implementation_effort="low",
                risk_level="low"
            ))
        
        return recommendations
    
    def _optimize_compression_settings(self, config: CDNConfiguration,
                                     performance_metrics: Dict[str, Any]) -> List[CacheOptimizationRecommendation]:
        """优化压缩设置"""
        recommendations = []
        
        # 检查Brotli压缩
        if not config.compression_settings.get("brotli_enabled", False):
            config.compression_settings["brotli_enabled"] = True
            config.compression_settings["brotli_level"] = 4
            
            recommendations.append(CacheOptimizationRecommendation(
                id="cdn_enable_brotli",
                category="performance",
                priority="high",
                title="Enable Brotli Compression",
                description="Brotli provides 15-25% better compression than Gzip",
                current_config={"brotli_enabled": False},
                recommended_config={"brotli_enabled": True, "brotli_level": 4},
                expected_improvement={"bandwidth_saved": 0.2, "response_time_reduction": 0.1},
                implementation_effort="low",
                risk_level="low"
            ))
        
        # 检查Gzip压缩级别
        gzip_level = config.compression_settings.get("gzip_level", 6)
        if gzip_level < 6:
            config.compression_settings["gzip_level"] = 6
            
            recommendations.append(CacheOptimizationRecommendation(
                id="cdn_optimize_gzip_level",
                category="performance",
                priority="medium",
                title="Optimize Gzip Compression Level",
                description="Level 6 provides good balance between compression and CPU",
                current_config={"gzip_level": gzip_level},
                recommended_config={"gzip_level": 6},
                expected_improvement={"bandwidth_saved": 0.05},
                implementation_effort="low",
                risk_level="low"
            ))
        
        return recommendations
    
    def _optimize_geo_restrictions(self, config: CDNConfiguration,
                                  performance_metrics: Dict[str, Any]) -> List[CacheOptimizationRecommendation]:
        """优化地理限制"""
        recommendations = []
        
        # 检查是否启用了不必要的地理限制
        if config.geo_restrictions.get("enabled", False):
            # 分析流量地理分布
            geo_distribution = performance_metrics.get("geo_distribution", {})
            
            # 如果主要流量集中在少数地区，可以考虑优化
            if geo_distribution:
                top_regions = sorted(geo_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
                total_top_traffic = sum(traffic for _, traffic in top_regions)
                total_traffic = sum(geo_distribution.values())
                
                if total_top_traffic / total_traffic > 0.9:  # 90%流量在前5个地区
                    recommendations.append(CacheOptimizationRecommendation(
                        id="cdn_optimize_geo_restrictions",
                        category="cost",
                        priority="medium",
                        title="Optimize Geographic Restrictions",
                        description=f"90% of traffic comes from top 5 regions, consider optimizing geo distribution",
                        current_config={"geo_restrictions": "all_regions"},
                        recommended_config={"geo_restrictions": list(region for region, _ in top_regions)},
                        expected_improvement={"cost_reduction": 0.1},
                        implementation_effort="medium",
                        risk_level="medium"
                    ))
        
        return recommendations
    
    def _optimize_edge_functions(self, config: CDNConfiguration,
                                performance_metrics: Dict[str, Any]) -> List[CacheOptimizationRecommendation]:
        """优化边缘函数"""
        recommendations = []
        
        # 检查是否启用了响应压缩函数
        has_compression_function = any(
            func.get("type") == "compression" for func in config.edge_functions
        )
        
        if not has_compression_function:
            config.edge_functions.append({
                "type": "compression",
                "trigger": {"response_type": ["text/html", "text/css", "application/javascript"]},
                "action": {"compress": True, "algorithm": "brotli"}
            })
            
            recommendations.append(CacheOptimizationRecommendation(
                id="cdn_edge_compression",
                category="performance",
                priority="high",
                title="Add Edge Compression Function",
                description="Edge functions can compress responses at CDN edge for better performance",
                current_config={"edge_compression": False},
                recommended_config={"edge_compression": True, "algorithm": "brotli"},
                expected_improvement={"bandwidth_saved": 0.25, "response_time_reduction": 0.15},
                implementation_effort="medium",
                risk_level="low"
            ))
        
        # 检查图片优化函数
        has_image_optimization = any(
            func.get("type") == "image_optimization" for func in config.edge_functions
        )
        
        if not has_image_optimization:
            config.edge_functions.append({
                "type": "image_optimization",
                "trigger": {"request_uri": ["*.jpg", "*.png", "*.webp"]},
                "action": {"optimize": True, "webp_conversion": True, "quality": 85}
            })
            
            recommendations.append(CacheOptimizationRecommendation(
                id="cdn_edge_image_optimization",
                category="performance",
                priority="medium",
                title="Add Edge Image Optimization Function",
                description="Automatic image optimization and WebP conversion at CDN edge",
                current_config={"image_optimization": False},
                recommended_config={"image_optimization": True, "webp_conversion": True},
                expected_improvement={"bandwidth_saved": 0.3, "response_time_reduction": 0.2},
                implementation_effort="medium",
                risk_level="low"
            ))
        
        return recommendations
    
    def _initialize_cdn_providers(self) -> Dict[str, Dict[str, Any]]:
        """初始化CDN提供商配置"""
        return {
            "cloudflare": {
                "features": ["brotli", "http2", "http3", "edge_functions", "image_optimization"],
                "default_ttl": 7200,
                "max_ttl": 31536000,
                "compression_algorithms": ["gzip", "brotli"]
            },
            "aws_cloudfront": {
                "features": ["gzip", "http2", "lambda_edge", "field_level_encryption"],
                "default_ttl": 86400,
                "max_ttl": 31536000,
                "compression_algorithms": ["gzip"]
            },
            "fastly": {
                "features": ["gzip", "brotli", "http2", "edge_compute", "image_optimization"],
                "default_ttl": 3600,
                "max_ttl": 31536000,
                "compression_algorithms": ["gzip", "brotli"]
            }
        }
    
    def _initialize_optimization_presets(self) -> Dict[str, Dict[str, Any]]:
        """初始化优化预设"""
        return {
            "performance": {
                "cache_ttl": {"static": 2592000, "api": 300},
                "compression": {"brotli": True, "gzip_level": 6},
                "optimization": {"image_optimization": True, "minification": True}
            },
            "cost": {
                "cache_ttl": {"static": 604800, "api": 60},
                "compression": {"brotli": False, "gzip_level": 4},
                "optimization": {"image_optimization": False, "minification": False}
            },
            "balanced": {
                "cache_ttl": {"static": 86400, "api": 300},
                "compression": {"brotli": True, "gzip_level": 6},
                "optimization": {"image_optimization": True, "minification": True}
            }
        }

class CachePerformanceAnalyzer:
    """缓存性能分析器"""
    
    def __init__(self):
        self.benchmark_metrics = self._initialize_benchmarks()
    
    def analyze_cache_performance(self, metrics: Dict[str, CachePerformanceMetrics]) -> Dict[str, Any]:
        """分析缓存性能"""
        print("📊 Analyzing cache performance...")
        
        analysis = {
            "overall_score": 0,
            "cache_efficiency": {},
            "performance_issues": [],
            "optimization_opportunities": [],
            "cost_analysis": {},
            "recommendations_summary": {}
        }
        
        # 计算整体得分
        total_hit_rate = sum(m.hit_rate for m in metrics.values())
        avg_hit_rate = total_hit_rate / len(metrics) if metrics else 0
        analysis["overall_score"] = min(avg_hit_rate * 100, 100)
        
        # 分析每个缓存类型
        for cache_type, metrics_data in metrics.items():
            cache_analysis = self._analyze_single_cache_type(cache_type, metrics_data)
            analysis["cache_efficiency"][cache_type] = cache_analysis
            
            # 识别性能问题
            if metrics_data.hit_rate < 0.5:
                analysis["performance_issues"].append({
                    "cache_type": cache_type,
                    "issue": "Low hit rate",
                    "value": metrics_data.hit_rate,
                    "threshold": 0.5
                })
            
            if metrics_data.avg_response_time > 200:
                analysis["performance_issues"].append({
                    "cache_type": cache_type,
                    "issue": "High response time",
                    "value": metrics_data.avg_response_time,
                    "threshold": 200
                })
        
        # 成本分析
        analysis["cost_analysis"] = self._analyze_cache_costs(metrics)
        
        # 优化机会
        analysis["optimization_opportunities"] = self._identify_optimization_opportunities(metrics)
        
        print(f"✅ Cache performance analysis completed")
        print(f"📈 Overall cache score: {analysis['overall_score']:.1f}/100")
        
        return analysis
    
    def _analyze_single_cache_type(self, cache_type: str, metrics: CachePerformanceMetrics) -> Dict[str, Any]:
        """分析单个缓存类型"""
        benchmark = self.benchmark_metrics.get(cache_type, self.benchmark_metrics["default"])
        
        analysis = {
            "hit_rate_score": min(metrics.hit_rate / benchmark["hit_rate"], 1.0) * 100,
            "response_time_score": max(0, (1 - metrics.avg_response_time / benchmark["response_time"])) * 100,
            "efficiency_score": 0,
            "grade": "C"
        }
        
        # 计算效率得分
        analysis["efficiency_score"] = (analysis["hit_rate_score"] + analysis["response_time_score"]) / 2
        
        # 评定等级
        score = analysis["efficiency_score"]
        if score >= 90:
            analysis["grade"] = "A"
        elif score >= 80:
            analysis["grade"] = "B"
        elif score >= 70:
            analysis["grade"] = "C"
        elif score >= 60:
            analysis["grade"] = "D"
        else:
            analysis["grade"] = "F"
        
        return analysis
    
    def _analyze_cache_costs(self, metrics: Dict[str, CachePerformanceMetrics]) -> Dict[str, Any]:
        """分析缓存成本"""
        cost_analysis = {
            "total_bandwidth_saved": 0,
            "estimated_cost_savings": 0,
            "cache_storage_cost": 0,
            "roi": 0
        }
        
        # 计算节省的带宽和成本
        bandwidth_cost_per_gb = 0.1  # 假设每GB $0.1
        
        for cache_type, metrics_data in metrics.items():
            monthly_bandwidth_saved = metrics_data.bandwidth_saved * 30  # 假设是日节省
            cost_analysis["total_bandwidth_saved"] += monthly_bandwidth_saved
            cost_analysis["estimated_cost_savings"] += monthly_bandwidth_saved * bandwidth_cost_per_gb
            
            # 估算存储成本
            storage_cost_per_gb = 0.05  # 假设每GB $0.05
            cost_analysis["cache_storage_cost"] += metrics_data.cache_size * storage_cost_per_gb
        
        # 计算ROI
        if cost_analysis["cache_storage_cost"] > 0:
            cost_analysis["roi"] = cost_analysis["estimated_cost_savings"] / cost_analysis["cache_storage_cost"]
        
        return cost_analysis
    
    def _identify_optimization_opportunities(self, metrics: Dict[str, CachePerformanceMetrics]) -> List[Dict[str, Any]]:
        """识别优化机会"""
        opportunities = []
        
        for cache_type, metrics_data in metrics.items():
            # 低命中率优化
            if metrics_data.hit_rate < 0.7:
                opportunities.append({
                    "cache_type": cache_type,
                    "opportunity": "Increase cache hit rate",
                    "potential_improvement": (0.7 - metrics_data.hit_rate) * 100,
                    "effort": "medium",
                    "impact": "high"
                })
            
            # 高驱逐率优化
            if metrics_data.eviction_rate > 0.1:
                opportunities.append({
                    "cache_type": cache_type,
                    "opportunity": "Reduce cache eviction rate",
                    "potential_improvement": metrics_data.eviction_rate * 50,
                    "effort": "medium",
                    "impact": "medium"
                })
            
            # TTL效率优化
            if metrics_data.ttl_efficiency < 0.8:
                opportunities.append({
                    "cache_type": cache_type,
                    "opportunity": "Optimize TTL settings",
                    "potential_improvement": (0.8 - metrics_data.ttl_efficiency) * 100,
                    "effort": "low",
                    "impact": "medium"
                })
        
        return opportunities
    
    def _initialize_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """初始化基准指标"""
        return {
            "default": {
                "hit_rate": 0.8,
                "response_time": 100,
                "bandwidth_saved": 1000,  # GB/day
                "cache_size": 100  # GB
            },
            "browser_cache": {
                "hit_rate": 0.7,
                "response_time": 10,
                "bandwidth_saved": 500,
                "cache_size": 10
            },
            "cdn_cache": {
                "hit_rate": 0.9,
                "response_time": 50,
                "bandwidth_saved": 2000,
                "cache_size": 500
            },
            "api_cache": {
                "hit_rate": 0.6,
                "response_time": 20,
                "bandwidth_saved": 100,
                "cache_size": 50
            }
        }

class CacheConfigurationGenerator:
    """缓存配置生成器"""
    
    def __init__(self):
        self.config_templates = self._initialize_config_templates()
    
    def generate_nginx_config(self, cache_rules: List[CacheRule]) -> str:
        """生成Nginx缓存配置"""
        config = "# Nginx Cache Configuration\n"
        config += "# Generated by Web3search Cache Optimizer\n\n"
        
        # 基础配置
        config += "# Basic cache settings\n"
        config += "proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;\n"
        config += "proxy_cache_path /var/cache/nginx/static levels=1:2 keys_zone=static_cache:100m max_size=10g inactive=7d;\n\n"
        
        # 为每个资源类型生成配置
        for rule in cache_rules:
            config += self._generate_nginx_location_block(rule)
        
        # 压缩配置
        config += "\n# Compression settings\n"
        config += "gzip on;\n"
        config += "gzip_vary on;\n"
        config += "gzip_min_length 1024;\n"
        config += "gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;\n"
        
        if any(rule.compression_enabled for rule in cache_rules):
            config += "# Brotli compression (if available)\n"
            config += "brotli on;\n"
            config += "brotli_comp_level 4;\n"
            config += "brotli_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;\n"
        
        return config
    
    def generate_apache_config(self, cache_rules: List[CacheRule]) -> str:
        """生成Apache缓存配置"""
        config = "# Apache Cache Configuration\n"
        config += "# Generated by Web3search Cache Optimizer\n\n"
        
        # 启用模块
        config += "<IfModule mod_expires.c>\n"
        config += "  ExpiresActive On\n"
        
        # 为每个资源类型生成过期规则
        for rule in cache_rules:
            config += self._generate_apache_expires_rule(rule)
        
        config += "</IfModule>\n\n"
        
        # 压缩配置
        config += "<IfModule mod_deflate.c>\n"
        config += "  SetOutputFilter DEFLATE\n"
        config += "  SetEnvIfNoCase Request_URI \\\n"
        config += "    \\.(?:gif|jpe?g|png)$ no-gzip dont-vary\n"
        config += "  SetEnvIfNoCase Request_URI \\\n"
        config += "    \\.(?:exe|t?gz|zip|bz2|sit|rar)$ no-gzip dont-vary\n"
        config += "</IfModule>\n"
        
        return config
    
    def generate_cloudflare_config(self, cache_rules: List[CacheRule]) -> Dict[str, Any]:
        """生成Cloudflare配置"""
        config = {
            "zone_settings": {},
            "page_rules": [],
            "transform_rules": []
        }
        
        # 缓存级别设置
        cache_levels = {}
        for rule in cache_rules:
            cache_levels[rule.resource_type.value] = {
                "cache_ttl": rule.max_age,
                "browser_cache_ttl": rule.max_age,
                "edge_cache_ttl": rule.max_age,
                "bypass_cache_on_cookie": rule.private,
                "cache_by_device_type": "desktop" in rule.vary_headers,
                "cache_deception_armor": rule.must_revalidate
            }
        
        config["zone_settings"]["cache_level"] = "simplified"
        config["zone_settings"]["browser_cache_ttl"] = 31536000  # 1年
        config["zone_settings"]["edge_cache_ttl"] = 2592000  # 30天
        config["zone_settings"]["cache_everything"] = True
        config["zone_settings"]["always_online"] = True
        
        # 页面规则
        for rule in cache_rules:
            if rule.resource_type == ResourceType.API_RESPONSE:
                config["page_rules"].append({
                    "targets": [{"target": "url", "constraint": {"operator": "matches", "value": "*/api/*"}}],
                    "actions": [
                        {"id": "cache_level", "value": "cache_everything"},
                        {"id": "edge_cache_ttl", "value": rule.max_age},
                        {"id": "browser_cache_ttl", "value": rule.max_age}
                    ]
                })
        
        return config
    
    def _generate_nginx_location_block(self, rule: CacheRule) -> str:
        """生成Nginx location块"""
        location_map = {
            ResourceType.HTML: "~ \\.html$",
            ResourceType.CSS: "~ \\.css$",
            ResourceType.JAVASCRIPT: "~ \\.(js|mjs)$",
            ResourceType.IMAGE: "~ \\.(jpg|jpeg|png|gif|webp|svg)$",
            ResourceType.FONT: "~ \\.(woff|woff2|ttf|otf|eot)$",
            ResourceType.API_RESPONSE: "~ ^/api/"
        }
        
        location_pattern = location_map.get(rule.resource_type, f"~ {rule.resource_type.value}")
        
        config = f"location {location_pattern} {{\n"
        
        # 缓存策略
        if rule.strategy == CacheStrategy.CACHE_FIRST:
            config += "    proxy_cache_valid 200 " + str(rule.max_age) + ";\n"
        elif rule.strategy == CacheStrategy.STALE_WHILE_REVALIDATE:
            config += "    proxy_cache_valid 200 " + str(rule.max_age) + ";\n"
            config += "    proxy_cache_background_update on;\n"
        
        # 缓存头
        if rule.max_age > 0:
            config += f"    expires {rule.max_age}s;\n"
        
        if rule.no_cache:
            config += "    add_header Cache-Control \"no-cache\";\n"
        elif rule.no_store:
            config += "    add_header Cache-Control \"no-store\";\n"
        else:
            cache_control = []
            if rule.public:
                cache_control.append("public")
            if rule.private:
                cache_control.append("private")
            if rule.must_revalidate:
                cache_control.append("must-revalidate")
            if rule.stale_while_revalidate > 0:
                cache_control.append(f"stale-while-revalidate={rule.stale_while_revalidate}")
            if rule.stale_if_error > 0:
                cache_control.append(f"stale-if-error={rule.stale_if_error}")
            
            if cache_control:
                config += f"    add_header Cache-Control \"{', '.join(cache_control)}, max-age={rule.max_age}\";\n"
        
        # ETag
        if rule.etag_enabled:
            config += "    etag on;\n"
        
        # 压缩
        if rule.compression_enabled:
            config += "    gzip on;\n"
        
        config += "}\n\n"
        
        return config
    
    def _generate_apache_expires_rule(self, rule: CacheRule) -> str:
        """生成Apache过期规则"""
        mime_types = {
            ResourceType.HTML: "text/html",
            ResourceType.CSS: "text/css",
            ResourceType.JAVASCRIPT: "application/javascript",
            ResourceType.IMAGE: "image/jpeg image/png image/gif image/webp",
            ResourceType.FONT: "font/woff font/woff2",
            ResourceType.API_RESPONSE: "application/json"
        }
        
        mime_type = mime_types.get(rule.resource_type, rule.resource_type.value)
        
        config = f"  ExpiresByType {mime_type} \"access plus {self._seconds_to_human(rule.max_age)}\"\n"
        
        return config
    
    def _seconds_to_human(self, seconds: int) -> str:
        """将秒转换为人类可读格式"""
        if seconds >= 31536000:  # 1年
            years = seconds // 31536000
            return f"{years} years"
        elif seconds >= 2592000:  # 30天
            months = seconds // 2592000
            return f"{months} months"
        elif seconds >= 86400:  # 1天
            days = seconds // 86400
            return f"{days} days"
        elif seconds >= 3600:  # 1小时
            hours = seconds // 3600
            return f"{hours} hours"
        else:
            return f"{seconds} seconds"
    
    def _initialize_config_templates(self) -> Dict[str, str]:
        """初始化配置模板"""
        return {
            "nginx_header": "# Nginx Configuration Generated by Web3search Cache Optimizer\n",
            "apache_header": "# Apache Configuration Generated by Web3search Cache Optimizer\n",
            "cloudflare_header": "# Cloudflare Configuration Generated by Web3search Cache Optimizer\n"
        }

def main():
    """主函数 - 缓存策略和CDN配置优化系统"""
    print("🚀 Starting Cache Strategy and CDN Configuration Optimization System...")
    
    # 创建优化器
    cache_optimizer = CacheStrategyOptimizer()
    cdn_optimizer = CDNOptimizer()
    analyzer = CachePerformanceAnalyzer()
    generator = CacheConfigurationGenerator()
    
    # 生成模拟缓存性能数据
    print("\n📊 Generating cache performance metrics...")
    
    cache_metrics = {
        "browser_cache": CachePerformanceMetrics(
            cache_type=CacheType.BROWSER_CACHE,
            hit_rate=0.65,
            miss_rate=0.35,
            avg_response_time=15,
            bandwidth_saved=500,
            cache_size=50,
            eviction_rate=0.05,
            ttl_efficiency=0.75
        ),
        "cdn_cache": CachePerformanceMetrics(
            cache_type=CacheType.CDN_CACHE,
            hit_rate=0.85,
            miss_rate=0.15,
            avg_response_time=80,
            bandwidth_saved=2000,
            cache_size=500,
            eviction_rate=0.03,
            ttl_efficiency=0.90
        ),
        "api_cache": CachePerformanceMetrics(
            cache_type=CacheType.API_CACHE,
            hit_rate=0.45,
            miss_rate=0.55,
            avg_response_time=25,
            bandwidth_saved=100,
            cache_size=30,
            eviction_rate=0.12,
            ttl_efficiency=0.60
        ),
        "redis_cache": CachePerformanceMetrics(
            cache_type=CacheType.REDIS_CACHE,
            hit_rate=0.92,
            miss_rate=0.08,
            avg_response_time=5,
            bandwidth_saved=50,
            cache_size=20,
            eviction_rate=0.02,
            ttl_efficiency=0.95
        )
    }
    
    print(f"📈 Generated metrics for {len(cache_metrics)} cache types")
    
    # 分析缓存性能
    print("\n📊 Analyzing cache performance...")
    performance_analysis = analyzer.analyze_cache_performance(cache_metrics)
    
    # 优化缓存策略
    print("\n🔧 Optimizing cache strategies...")
    current_rules = cache_optimizer.cache_rules
    optimized_rules, cache_recommendations = cache_optimizer.optimize_cache_rules(cache_metrics, current_rules)
    
    # 创建CDN配置
    print("\n🌐 Creating CDN configuration...")
    current_cdn_config = CDNConfiguration(
        provider="cloudflare",
        distribution_id="E1234567890ABC",
        domain_name="cdn.web3search.com",
        cache_key_policy={"query_strings": "all"},
        origin_configuration={"protocol": "https", "port": 443},
        behavior_rules=[],
        geo_restrictions={"enabled": False},
        security_settings={"tls_version": "1.2", "hsts_enabled": True},
        compression_settings={"gzip_enabled": True, "gzip_level": 4, "brotli_enabled": False},
        edge_functions=[]
    )
    
    optimized_cdn_config, cdn_recommendations = cdn_optimizer.optimize_cdn_configuration(
        current_cdn_config, performance_analysis
    )
    
    # 生成配置文件
    print("\n📄 Generating configuration files...")
    
    # Nginx配置
    nginx_config = generator.generate_nginx_config(optimized_rules)
    with open("nginx_cache_config.conf", "w") as f:
        f.write(nginx_config)
    
    # Apache配置
    apache_config = generator.generate_apache_config(optimized_rules)
    with open("apache_cache_config.conf", "w") as f:
        f.write(apache_config)
    
    # Cloudflare配置
    cloudflare_config = generator.generate_cloudflare_config(optimized_rules)
    with open("cloudflare_cache_config.json", "w") as f:
        json.dump(cloudflare_config, f, indent=2)
    
    # 生成优化报告
    print("\n📋 Generating optimization report...")
    
    optimization_report = {
        "generated_at": datetime.now().isoformat(),
        "performance_analysis": performance_analysis,
        "cache_optimization": {
            "rules_count": len(optimized_rules),
            "recommendations_count": len(cache_recommendations),
            "recommendations": [asdict(rec) for rec in cache_recommendations]
        },
        "cdn_optimization": {
            "provider": optimized_cdn_config.provider,
            "recommendations_count": len(cdn_recommendations),
            "recommendations": [asdict(rec) for rec in cdn_recommendations]
        },
        "configurations_generated": {
            "nginx": "nginx_cache_config.conf",
            "apache": "apache_cache_config.conf",
            "cloudflare": "cloudflare_cache_config.json"
        }
    }
    
    with open("cache_optimization_report.json", "w") as f:
        json.dump(optimization_report, f, indent=2, default=str)
    
    # 显示摘要
    print(f"\n📊 Cache Strategy and CDN Optimization Summary:")
    print(f"  • Overall cache performance score: {performance_analysis['overall_score']:.1f}/100")
    print(f"  • Cache types analyzed: {len(cache_metrics)}")
    print(f"  • Performance issues identified: {len(performance_analysis['performance_issues'])}")
    print(f"  • Optimization opportunities: {len(performance_analysis['optimization_opportunities'])}")
    print(f"  • Cache rules optimized: {len(optimized_rules)}")
    print(f"  • Cache recommendations: {len(cache_recommendations)}")
    print(f"  • CDN recommendations: {len(cdn_recommendations)}")
    
    # 显示性能分析结果
    print(f"\n📈 Cache Performance Analysis:")
    for cache_type, analysis in performance_analysis["cache_efficiency"].items():
        print(f"  • {cache_type}:")
        print(f"    - Hit Rate Score: {analysis['hit_rate_score']:.1f}/100")
        print(f"    - Response Time Score: {analysis['response_time_score']:.1f}/100")
        print(f"    - Overall Grade: {analysis['grade']}")
    
    # 显示成本分析
    cost_analysis = performance_analysis["cost_analysis"]
    print(f"\n💰 Cost Analysis:")
    print(f"  • Monthly bandwidth saved: {cost_analysis['total_bandwidth_saved']:.1f} GB")
    print(f"  • Estimated cost savings: ${cost_analysis['estimated_cost_savings']:.2f}/month")
    print(f"  • Cache storage cost: ${cost_analysis['cache_storage_cost']:.2f}/month")
    print(f"  • ROI: {cost_analysis['roi']:.1f}x")
    
    # 显示高优先级建议
    high_priority_recommendations = [
        rec for rec in cache_recommendations + cdn_recommendations 
        if rec.priority == "high"
    ]
    
    if high_priority_recommendations:
        print(f"\n🚨 High Priority Recommendations:")
        for rec in high_priority_recommendations[:5]:
            print(f"  • {rec.title}")
            print(f"    - {rec.description}")
            print(f"    - Expected improvement: {rec.expected_improvement}")
    
    print(f"\n✅ Cache Strategy and CDN Configuration Optimization System completed successfully!")
    print("📁 Generated files:")
    print("  • nginx_cache_config.conf - Optimized Nginx cache configuration")
    print("  • apache_cache_config.conf - Optimized Apache cache configuration")
    print("  • cloudflare_cache_config.json - Cloudflare configuration")
    print("  • cache_optimization_report.json - Comprehensive optimization report")
    
    print(f"\n🎯 System Features:")
    print("  • Intelligent cache strategy optimization")
    print("  • Multi-provider CDN configuration")
    print("  • Performance-based rule generation")
    print("  • Cost analysis and ROI calculation")
    print("  • Configuration file generation (Nginx, Apache, Cloudflare)")
    print("  • Comprehensive performance analysis")
    print("  • Actionable optimization recommendations")
    
    return optimization_report

if __name__ == "__main__":
    main()
