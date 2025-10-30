"""
安全工具模块
提供密码加密、JWT Token生成和验证功能
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希密码
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    验证密码强度
    
    要求:
    - 最小8字符
    - 包含字母和数字
    
    Args:
        password: 明文密码
        
    Returns:
        tuple[bool, Optional[str]]: (是否有效, 错误消息)
    """
    if len(password) < 8:
        return False, "密码长度至少8个字符"
    
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not has_letter:
        return False, "密码必须包含至少一个字母"
    
    if not has_digit:
        return False, "密码必须包含至少一个数字"
    
    return True, None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT Access Token
    
    Args:
        data: Token数据（通常包含user_id和email）
        expires_delta: 过期时间增量（默认24小时）
        
    Returns:
        str: JWT Token字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """
    创建Refresh Token
    
    Args:
        user_id: 用户ID
        
    Returns:
        str: Refresh Token字符串（随机字符串，非JWT）
    """
    import secrets
    return secrets.token_urlsafe(32)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证JWT Token
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Optional[Dict[str, Any]]: Token载荷，如果无效则返回None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT Token（不验证签名，用于调试）
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Optional[Dict[str, Any]]: Token载荷，如果无效则返回None
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    从Token中提取用户ID
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Optional[str]: 用户ID，如果Token无效则返回None
    """
    payload = verify_token(token)
    if payload:
        return payload.get("user_id") or payload.get("sub")
    return None


def get_email_from_token(token: str) -> Optional[str]:
    """
    从Token中提取邮箱
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Optional[str]: 邮箱，如果Token无效则返回None
    """
    payload = verify_token(token)
    if payload:
        return payload.get("email")
    return None

