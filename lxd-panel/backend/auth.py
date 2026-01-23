import secrets
import hashlib
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader


# 默认API密钥 (安装时会生成新的)
API_KEY = "change-this-key-on-install"

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """生成随机API密钥"""
    return secrets.token_urlsafe(32)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """验证API密钥"""
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="无效的API密钥"
        )
    return api_key


def set_api_key(key: str):
    """设置API密钥"""
    global API_KEY
    API_KEY = key
