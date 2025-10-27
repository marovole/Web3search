"""
输出格式控制（任务 11.6）

功能：
1. JSON Schema定义
2. 输出验证
3. 格式约束
4. 与模板系统集成

支持的格式：
- QuickChatResponse: Quick Chat标准输出
- ResearchReport: Deep Research报告
- PriceAnalysis: 价格分析
- SentimentReport: 情绪分析报告
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json
import jsonschema
from jsonschema import validate, ValidationError


# ================================
# 输出格式枚举
# ================================

class OutputFormat(str, Enum):
    """支持的输出格式"""
    QUICK_CHAT = "quick_chat"
    DEEP_RESEARCH = "deep_research"
    PRICE_ANALYSIS = "price_analysis"
    SENTIMENT_REPORT = "sentiment_report"
    RISK_ASSESSMENT = "risk_assessment"
    TOKENOMICS_ANALYSIS = "tokenomics_analysis"


# ================================
# JSON Schema定义
# ================================

QUICK_CHAT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["summary", "analysis", "risk_warning"],
    "properties": {
        "summary": {
            "type": "string",
            "description": "核心观点摘要（1-2句话）",
            "minLength": 20,
            "maxLength": 200
        },
        "analysis": {
            "type": "object",
            "required": ["key_points"],
            "properties": {
                "key_points": {
                    "type": "array",
                    "description": "关键分析点",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 5
                },
                "data_sources": {
                    "type": "array",
                    "description": "数据来源",
                    "items": {"type": "string"}
                }
            }
        },
        "recommendation": {
            "type": "string",
            "description": "操作建议（可选）"
        },
        "risk_warning": {
            "type": "string",
            "description": "风险提示",
            "minLength": 10
        },
        "confidence": {
            "type": "number",
            "description": "置信度（0-1）",
            "minimum": 0,
            "maximum": 1
        }
    }
}

DEEP_RESEARCH_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["title", "executive_summary", "sections", "conclusion"],
    "properties": {
        "title": {
            "type": "string",
            "description": "报告标题"
        },
        "executive_summary": {
            "type": "string",
            "description": "执行摘要（200-300字）",
            "minLength": 200,
            "maxLength": 500
        },
        "sections": {
            "type": "array",
            "description": "报告章节",
            "items": {
                "type": "object",
                "required": ["title", "content"],
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "subsections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "minItems": 5,
            "maxItems": 10
        },
        "conclusion": {
            "type": "object",
            "required": ["core_view", "key_arguments"],
            "properties": {
                "core_view": {"type": "string"},
                "key_arguments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3
                },
                "risk_factors": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "references": {
            "type": "array",
            "description": "参考文献",
            "items": {"type": "string"}
        }
    }
}

PRICE_ANALYSIS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["symbol", "current_price", "analysis", "outlook"],
    "properties": {
        "symbol": {
            "type": "string",
            "description": "代币符号"
        },
        "current_price": {
            "type": "number",
            "description": "当前价格"
        },
        "analysis": {
            "type": "object",
            "properties": {
                "trend": {
                    "type": "string",
                    "enum": ["bullish", "bearish", "neutral"],
                    "description": "趋势方向"
                },
                "support_levels": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "支撑位"
                },
                "resistance_levels": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "阻力位"
                },
                "technical_indicators": {
                    "type": "object",
                    "description": "技术指标",
                    "properties": {
                        "rsi": {"type": "number"},
                        "macd": {"type": "string"},
                        "ma50": {"type": "number"},
                        "ma200": {"type": "number"}
                    }
                }
            }
        },
        "outlook": {
            "type": "object",
            "required": ["timeframe", "scenario"],
            "properties": {
                "timeframe": {
                    "type": "string",
                    "enum": ["short_term", "medium_term", "long_term"]
                },
                "scenario": {
                    "type": "string",
                    "description": "预期情景"
                },
                "price_target": {
                    "type": "object",
                    "properties": {
                        "low": {"type": "number"},
                        "base": {"type": "number"},
                        "high": {"type": "number"}
                    }
                }
            }
        }
    }
}

SENTIMENT_REPORT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["symbol", "overall_sentiment", "metrics"],
    "properties": {
        "symbol": {
            "type": "string"
        },
        "overall_sentiment": {
            "type": "string",
            "enum": ["very_positive", "positive", "neutral", "negative", "very_negative"]
        },
        "sentiment_score": {
            "type": "number",
            "minimum": -1,
            "maximum": 1,
            "description": "情绪得分（-1到1）"
        },
        "metrics": {
            "type": "object",
            "properties": {
                "twitter": {
                    "type": "object",
                    "properties": {
                        "mentions": {"type": "integer"},
                        "sentiment": {"type": "number"}
                    }
                },
                "reddit": {
                    "type": "object",
                    "properties": {
                        "posts": {"type": "integer"},
                        "sentiment": {"type": "number"}
                    }
                }
            }
        },
        "key_topics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "热门话题"
        },
        "sentiment_drivers": {
            "type": "array",
            "items": {"type": "string"},
            "description": "情绪驱动因素"
        }
    }
}

RISK_ASSESSMENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["symbol", "overall_risk", "risk_factors"],
    "properties": {
        "symbol": {"type": "string"},
        "overall_risk": {
            "type": "string",
            "enum": ["very_high", "high", "medium", "low", "very_low"]
        },
        "risk_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "风险得分（0-10）"
        },
        "risk_factors": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["category", "level", "description"],
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["market", "technical", "regulatory", "liquidity", "competition"]
                    },
                    "level": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                    },
                    "description": {"type": "string"}
                }
            },
            "minItems": 1
        },
        "mitigation_strategies": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}


# ================================
# Schema注册表
# ================================

SCHEMA_REGISTRY: Dict[OutputFormat, Dict[str, Any]] = {
    OutputFormat.QUICK_CHAT: QUICK_CHAT_SCHEMA,
    OutputFormat.DEEP_RESEARCH: DEEP_RESEARCH_SCHEMA,
    OutputFormat.PRICE_ANALYSIS: PRICE_ANALYSIS_SCHEMA,
    OutputFormat.SENTIMENT_REPORT: SENTIMENT_REPORT_SCHEMA,
    OutputFormat.RISK_ASSESSMENT: RISK_ASSESSMENT_SCHEMA,
}


# ================================
# 验证器
# ================================

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class OutputValidator:
    """输出格式验证器"""

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        初始化验证器

        Args:
            schema: JSON Schema（可选）
        """
        self.schema = schema

    def validate(self, data: Any) -> ValidationResult:
        """
        验证数据

        Args:
            data: 待验证数据（dict或JSON字符串）

        Returns:
            ValidationResult: 验证结果
        """
        if self.schema is None:
            return ValidationResult(is_valid=True)

        # 如果是字符串，尝试解析为JSON
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"JSON解析失败: {str(e)}"]
                )

        # JSON Schema验证
        try:
            validate(instance=data, schema=self.schema)
            return ValidationResult(is_valid=True)
        except ValidationError as e:
            return ValidationResult(
                is_valid=False,
                errors=[str(e)]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"验证失败: {str(e)}"]
            )

    @staticmethod
    def from_format(format_type: OutputFormat) -> "OutputValidator":
        """
        从格式类型创建验证器

        Args:
            format_type: 输出格式类型

        Returns:
            OutputValidator: 验证器实例
        """
        schema = SCHEMA_REGISTRY.get(format_type)
        return OutputValidator(schema=schema)


# ================================
# 格式说明生成器
# ================================

class FormatSpecGenerator:
    """格式说明生成器"""

    @staticmethod
    def generate_format_instruction(format_type: OutputFormat) -> str:
        """
        生成格式说明（用于prompt）

        Args:
            format_type: 输出格式类型

        Returns:
            str: 格式说明文本
        """
        schema = SCHEMA_REGISTRY.get(format_type)
        if not schema:
            return ""

        instructions = {
            OutputFormat.QUICK_CHAT: """
## 输出格式要求

请按照以下JSON格式输出分析结果：

```json
{
  "summary": "核心观点摘要（1-2句话，20-200字）",
  "analysis": {
    "key_points": ["关键点1", "关键点2", "关键点3"],
    "data_sources": ["数据来源1", "数据来源2"]
  },
  "recommendation": "操作建议（可选）",
  "risk_warning": "风险提示（至少10字）",
  "confidence": 0.75  // 置信度（0-1）
}
```

**重要**：
- summary必须简洁明了，20-200字
- key_points至少2个，最多5个
- risk_warning必须包含
- confidence表示分析置信度
""",
            OutputFormat.PRICE_ANALYSIS: """
## 输出格式要求

请按照以下JSON格式输出价格分析：

```json
{
  "symbol": "BTC",
  "current_price": 45000.00,
  "analysis": {
    "trend": "bullish",  // bullish/bearish/neutral
    "support_levels": [43000, 41000],
    "resistance_levels": [47000, 50000],
    "technical_indicators": {
      "rsi": 65,
      "macd": "golden_cross",
      "ma50": 44000,
      "ma200": 40000
    }
  },
  "outlook": {
    "timeframe": "short_term",  // short_term/medium_term/long_term
    "scenario": "情景描述",
    "price_target": {
      "low": 42000,
      "base": 48000,
      "high": 52000
    }
  }
}
```
""",
            OutputFormat.SENTIMENT_REPORT: """
## 输出格式要求

请按照以下JSON格式输出情绪分析：

```json
{
  "symbol": "ETH",
  "overall_sentiment": "positive",  // very_positive/positive/neutral/negative/very_negative
  "sentiment_score": 0.65,  // -1到1
  "metrics": {
    "twitter": {
      "mentions": 15000,
      "sentiment": 0.7
    },
    "reddit": {
      "posts": 500,
      "sentiment": 0.6
    }
  },
  "key_topics": ["升级", "质押", "Layer2"],
  "sentiment_drivers": ["技术升级预期", "质押收益上升"]
}
```
"""
        }

        return instructions.get(format_type, "")


# ================================
# 便捷函数
# ================================

def validate_output(
    data: Any,
    format_type: Optional[OutputFormat] = None,
    schema: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    便捷函数：验证输出

    Args:
        data: 待验证数据
        format_type: 格式类型（可选）
        schema: 自定义schema（可选）

    Returns:
        ValidationResult: 验证结果
    """
    if format_type:
        validator = OutputValidator.from_format(format_type)
    else:
        validator = OutputValidator(schema=schema)

    return validator.validate(data)


def get_format_instruction(format_type: OutputFormat) -> str:
    """
    便捷函数：获取格式说明

    Args:
        format_type: 格式类型

    Returns:
        str: 格式说明
    """
    return FormatSpecGenerator.generate_format_instruction(format_type)
