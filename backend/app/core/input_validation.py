"""
输入验证工具模块
提供统一的输入验证和清理功能，包括：
1. SQL注入防护
2. XSS攻击防护
3. 文件路径安全验证
4. 数据类型和格式验证
5. 恶意输入检测
"""

import re
import os
import hashlib
import logging
from typing import Optional, List, Dict, Any, Union
from fastapi import HTTPException, status
from pydantic import BaseModel, validator, Field

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """输入验证错误"""
    pass


class SecurityValidator:
    """安全验证器"""

    # SQL注入检测模式
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|/\*|\*/|;)",
        r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",
        r"(\bOR\b|\bAND\b)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?",
        r"(WAITFOR\s+DELAY|SLEEP\s*\(|BENCHMARK\s*\()",
        r"(CHAR\s*\(|ASCII\s*\(|ORD\s*\()",
        r"(INFORMATION_SCHEMA|SYS\.|MASTER\.)",
        r"(0x[0-9a-fA-F]+|X'[0-9a-fA-F]+')",
    ]

    # XSS攻击检测模式
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript\s*:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<form[^>]*>",
        r"eval\s*\(",
        r"setTimeout\s*\(",
        r"setInterval\s*\(",
    ]

    # 文件路径遍历检测模式
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"/etc/passwd",
        r"/proc/",
        r"c:\\windows\\system32",
        r"\.\./\.\./",
        r"%2e%2e%2f",
        r"..%2f",
        r"%5c",
    ]

    @classmethod
    def sanitize_string(cls, input_str: str, max_length: int = 1000) -> str:
        """
        清理字符串输入

        Args:
            input_str: 输入字符串
            max_length: 最大长度限制

        Returns:
            清理后的字符串
        """
        if not input_str:
            return ""

        # 长度限制
        if len(input_str) > max_length:
            input_str = input_str[:max_length]

        # 移除控制字符
        cleaned = ''.join(char for char in input_str if ord(char) >= 32 or char in '\t\n\r')

        # 移除潜在的XSS代码
        for pattern in cls.XSS_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    @classmethod
    def detect_sql_injection(cls, input_str: str) -> bool:
        """
        检测SQL注入攻击

        Args:
            input_str: 输入字符串

        Returns:
            是否检测到SQL注入
        """
        if not input_str:
            return False

        # 转换为小写进行检测
        lower_input = input_str.lower()

        # 检查SQL注入模式
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, lower_input):
                logger.warning(f"检测到SQL注入尝试: {input_str[:50]}...")
                return True

        return False

    @classmethod
    def detect_xss(cls, input_str: str) -> bool:
        """
        检测XSS攻击

        Args:
            input_str: 输入字符串

        Returns:
            是否检测到XSS攻击
        """
        if not input_str:
            return False

        # 检查XSS模式
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_str, flags=re.IGNORECASE):
                logger.warning(f"检测到XSS攻击尝试: {input_str[:50]}...")
                return True

        return False

    @classmethod
    def validate_path(cls, file_path: str, base_dir: str) -> bool:
        """
        验证文件路径安全性

        Args:
            file_path: 文件路径
            base_dir: 基础目录

        Returns:
            路径是否安全
        """
        if not file_path or not base_dir:
            return False

        try:
            # 规范化路径
            normalized_path = os.path.normpath(file_path)
            normalized_base = os.path.normpath(base_dir)

            # 检查路径遍历模式
            for pattern in cls.PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, file_path, flags=re.IGNORECASE):
                    logger.warning(f"检测到路径遍历尝试: {file_path}")
                    return False

            # 检查是否在基础目录内
            if not normalized_path.startswith(normalized_base):
                logger.warning(f"路径不在基础目录内: {file_path}")
                return False

            return True

        except Exception as e:
            logger.error(f"路径验证错误: {e}")
            return False

    @classmethod
    def validate_field_name(cls, field_name: str, allowed_fields: List[str]) -> str:
        """
        验证字段名称（用于数据库排序等）

        Args:
            field_name: 字段名称
            allowed_fields: 允许的字段列表

        Returns:
            验证后的字段名称

        Raises:
            ValidationError: 如果字段名称无效
        """
        if not field_name:
            raise ValidationError("字段名称不能为空")

        if field_name not in allowed_fields:
            raise ValidationError(f"无效的字段名称: {field_name}，允许的字段: {', '.join(allowed_fields)}")

        # 检查字段名称是否包含危险字符
        if re.search(r'[;\'"\\]', field_name):
            raise ValidationError("字段名称包含非法字符")

        return field_name

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        验证邮箱格式

        Args:
            email: 邮箱地址

        Returns:
            邮箱是否有效
        """
        if not email:
            return False

        # 基础邮箱格式验证
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False

        # 长度限制
        if len(email) > 254:  # RFC 5321标准
            return False

        return True

    @classmethod
    def validate_password(cls, password: str) -> Dict[str, Any]:
        """
        验证密码强度

        Args:
            password: 密码

        Returns:
            密码强度信息
        """
        if not password:
            return {"valid": False, "errors": ["密码不能为空"]}

        errors = []
        score = 0

        # 长度检查
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        else:
            errors.append("密码长度至少需要8个字符")

        # 字符类型检查
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            errors.append("需要包含大写字母")

        if re.search(r'[a-z]', password):
            score += 1
        else:
            errors.append("需要包含小写字母")

        if re.search(r'\d', password):
            score += 1
        else:
            errors.append("需要包含数字")

        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 2
        else:
            errors.append("需要包含特殊字符")

        # 检查常见密码
        common_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey"
        ]
        if password.lower() in common_passwords:
            score = 0
            errors.append("不能使用常见密码")

        strength = "弱"
        if score >= 7:
            strength = "非常强"
        elif score >= 5:
            strength = "强"
        elif score >= 3:
            strength = "中等"

        return {
            "valid": len(errors) == 0,
            "score": score,
            "strength": strength,
            "errors": errors
        }

    @classmethod
    def validate_symbol(cls, symbol: str) -> bool:
        """
        验证加密货币符号格式

        Args:
            symbol: 币种符号

        Returns:
            符号是否有效
        """
        if not symbol:
            return False

        # 只允许字母、数字和常见的币种符号
        symbol_pattern = r'^[A-Z0-9]+$'
        return bool(re.match(symbol_pattern, symbol.upper()))

    @classmethod
    def validate_page_size(cls, page_size: int, max_size: int = 100) -> int:
        """
        验证分页大小

        Args:
            page_size: 页面大小
            max_size: 最大允许大小

        Returns:
            验证后的页面大小
        """
        if page_size <= 0:
            return 10  # 默认值
        if page_size > max_size:
            return max_size
        return page_size

    @classmethod
    def validate_sort_direction(cls, sort_desc: bool) -> bool:
        """
        验证排序方向

        Args:
            sort_desc: 是否降序

        Returns:
            验证后的排序方向
        """
        return bool(sort_desc)


class SafeRequest(BaseModel):
    """安全的请求基类"""

    @validator('*', pre=True)
    def sanitize_inputs(cls, v):
        """清理所有输入"""
        if isinstance(v, str):
            return SecurityValidator.sanitize_string(v)
        return v


class SearchQuery(BaseModel):
    """搜索查询模型"""
    q: str = Field(..., min_length=1, max_length=100, description="搜索查询")

    @validator('q')
    def validate_search_query(cls, v):
        # 检查SQL注入
        if SecurityValidator.detect_sql_injection(v):
            raise ValueError("Invalid search query")

        # 检查XSS
        if SecurityValidator.detect_xss(v):
            raise ValueError("Invalid search query")

        return SecurityValidator.sanitize_string(v, max_length=100)


class SortQuery(BaseModel):
    """排序查询模型"""
    order_by: str = Field("created_at", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")

    def __init__(self, allowed_fields: List[str], **data):
        self._allowed_fields = allowed_fields
        super().__init__(**data)

    @validator('order_by')
    def validate_order_by(cls, v, values):
        allowed_fields = getattr(cls, '_allowed_fields', ['created_at'])
        return SecurityValidator.validate_field_name(v, allowed_fields)


class FileUpload(BaseModel):
    """文件上传模型"""
    filename: str = Field(..., description="文件名")
    content_type: str = Field(..., description="文件类型")

    @validator('filename')
    def validate_filename(cls, v):
        # 检查XSS攻击
        if SecurityValidator.detect_xss(v):
            raise ValueError("Invalid filename: XSS detected")

        # 检查路径遍历攻击
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid filename: path traversal detected")

        # 检查特殊字符
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in v for char in invalid_chars):
            raise ValueError("Invalid filename: contains invalid characters")

        return SecurityValidator.sanitize_string(v, max_length=255)

    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/gif',
            'text/plain',
            'application/json'
        ]

        if v not in allowed_types:
            raise ValueError(f"Unsupported file type: {v}")

        return v


# 便捷验证函数
def validate_and_sanitize_input(data: Dict[str, Any], rules: Dict[str, Dict]) -> Dict[str, Any]:
    """
    验证和清理输入数据

    Args:
        data: 输入数据
        rules: 验证规则

    Returns:
        验证后的数据
    """
    validated_data = {}

    for field, rule in rules.items():
        value = data.get(field)

        if value is None and rule.get('required', False):
            raise ValidationError(f"Field '{field}' is required")

        if value is None:
            continue

        # 类型验证
        expected_type = rule.get('type', str)
        if not isinstance(value, expected_type):
            try:
                value = expected_type(value)
            except (ValueError, TypeError):
                raise ValidationError(f"Field '{field}' must be of type {expected_type.__name__}")

        # 长度验证
        if isinstance(value, str):
            max_length = rule.get('max_length', 1000)
            min_length = rule.get('min_length', 0)

            if len(value) > max_length:
                value = value[:max_length]

            if len(value) < min_length:
                raise ValidationError(f"Field '{field}' must be at least {min_length} characters")

        # 安全验证
        if isinstance(value, str):
            # SQL注入检查
            if SecurityValidator.detect_sql_injection(value):
                raise ValidationError(f"Field '{field}' contains invalid content")

            # XSS检查
            if SecurityValidator.detect_xss(value):
                raise ValidationError(f"Field '{field}' contains invalid content")

            # 清理
            value = SecurityValidator.sanitize_string(value)

        validated_data[field] = value

    return validated_data


# HTTP错误处理
def handle_validation_error(error: ValidationError) -> HTTPException:
    """处理验证错误"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(error)
    )


def handle_security_error(error: Exception) -> HTTPException:
    """处理安全错误"""
    logger.error(f"Security error: {error}")
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid request"
    )