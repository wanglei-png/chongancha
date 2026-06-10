"""微信登录 & JWT 认证路由"""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.user import User
from utils.jwt_utils import create_token, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


# ============================================================
# Pydantic 请求/响应模型
# ============================================================


class WxLoginRequest(BaseModel):
    """微信登录请求"""

    code: str = Field(..., description="前端 wx.login 获取的临时登录凭证")


class WxLoginResponse(BaseModel):
    """微信登录响应"""

    token: str
    user_id: int
    is_new_user: bool


class UserInfoResponse(BaseModel):
    """用户信息响应"""

    id: int
    openid: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    subscription_status: str = "none"
    subscription_expire_at: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# API 接口
# ============================================================


@router.post("/login", response_model=WxLoginResponse)
async def wx_login(request: WxLoginRequest, db: Session = Depends(get_db)):
    """微信小程序登录

    1. 用 code 向微信服务器换取 openid 和 session_key
    2. 根据 openid 查找或创建用户
    3. 生成 JWT token 返回
    """
    # 向微信服务器请求 jscode2session
    wx_url = (
        f"https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={settings.WX_APPID}"
        f"&secret={settings.WX_SECRET}"
        f"&js_code={request.code}"
        f"&grant_type=authorization_code"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            wx_resp = await client.get(wx_url)
            wx_data = wx_resp.json()
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"微信接口请求失败: {str(e)}",
        )

    # 检查微信返回的错误
    if "errcode" in wx_data and wx_data["errcode"] != 0:
        errcode = wx_data["errcode"]
        errmsg = wx_data.get("errmsg", "未知错误")
        # -1: 系统繁忙; 40029: code 无效; 45011: 频率限制
        if errcode == 40029:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="登录凭证已过期或无效，请重新获取",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"微信登录失败 (errcode={errcode}): {errmsg}",
        )

    openid = wx_data["openid"]
    # session_key 可用于后续解密敏感信息，暂不存储
    # session_key = wx_data.get("session_key")
    unionid = wx_data.get("unionid")

    # 根据 openid 查找或创建用户
    user = db.query(User).filter(User.openid == openid).first()
    is_new_user = False
    if not user:
        user = User(
            openid=openid,
            unionid=unionid,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new_user = True
    else:
        # 更新 unionid（如果微信返回了且用户之前没有）
        if unionid and not user.unionid:
            user.unionid = unionid
            db.commit()

    # 生成 JWT token
    token = create_token(user_id=user.id, openid=user.openid)

    return WxLoginResponse(
        token=token,
        user_id=user.id,
        is_new_user=is_new_user,
    )


@router.get("/me", response_model=UserInfoResponse)
def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前登录用户信息（需 JWT 认证）"""
    user_id = current_user.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    return UserInfoResponse(
        id=user.id,
        openid=user.openid,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        subscription_status=user.subscription_status,
        subscription_expire_at=str(user.subscription_expire_at)
        if user.subscription_expire_at
        else None,
    )
