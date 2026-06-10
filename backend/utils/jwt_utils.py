"""JWT 工具函数：创建、验证 token，以及 FastAPI 依赖注入"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import settings

# HTTPBearer 安全方案，自动从请求头提取 Authorization: Bearer {token}
security = HTTPBearer()


def create_token(user_id: int, openid: str) -> str:
    """创建 JWT token，包含 user_id 和 openid"""
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "openid": openid,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """验证 JWT token，返回 payload 或 None"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI 依赖注入：从请求头提取并验证 JWT token，返回 payload

    用法：
        @router.get("/me")
        def get_me(current_user: dict = Depends(get_current_user)):
            return current_user
    """
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """FastAPI 依赖注入：可选 JWT 认证，未登录时返回 None

    用法：
        @router.post("/generate")
        def generate_summary(
            current_user: Optional[dict] = Depends(get_current_user_optional)
        ):
            user_id = current_user.get("user_id") if current_user else None
    """
    if credentials is None:
        return None
    token = credentials.credentials
    payload = verify_token(token)
    return payload  # 验证失败返回 None，不抛出异常
