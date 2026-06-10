"""微信支付路由（支持模拟支付模式）"""

import hashlib
import json
import random
import string
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.order import Order
from models.user import User
from utils.jwt_utils import get_current_user

router = APIRouter(prefix="/api/v1/payment", tags=["支付"])

# ============================================================
# 定价配置
# ============================================================

PRODUCT_PRICES = {
    "single": 1.9,
    "monthly": 19.0,
    "yearly": 159.0,
}

# ============================================================
# Pydantic 请求/响应模型
# ============================================================


class CreateOrderRequest(BaseModel):
    """创建订单请求"""

    product_type: str = Field(
        ..., pattern="^(single|monthly|yearly)$", description="商品类型"
    )
    symptom_id: Optional[str] = Field(default=None, description="关联的症状ID（单次查询时）")


class CreateOrderResponse(BaseModel):
    """创建订单响应（前端调支付所需参数）"""

    order_no: str
    amount: float
    prepay_id: str
    appId: str
    timeStamp: str
    nonceStr: str
    package: str
    signType: str
    paySign: str


class OrderQueryResponse(BaseModel):
    """订单查询响应"""

    order_no: str
    status: str
    amount: float
    pay_time: Optional[str] = None
    product_type: str


# ============================================================
# 辅助函数
# ============================================================


def _generate_order_no() -> str:
    """生成唯一订单号：ORDER + 时间戳(14位) + 随机数(6位)"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = "".join(random.choices(string.digits, k=6))
    return f"ORDER{ts}{rand}"


def _get_product_amount(product_type: str) -> float:
    """根据商品类型获取金额"""
    amount = PRODUCT_PRICES.get(product_type)
    if amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的商品类型: {product_type}",
        )
    return amount


def _generate_nonce_str(length: int = 32) -> str:
    """生成随机字符串"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _mock_prepay_params(order_no: str, amount: float) -> dict:
    """模拟支付：生成前端调支付所需的参数（不真正调用微信API）"""
    app_id = settings.WX_APPID or "mock_appid"
    nonce_str = _generate_nonce_str()
    time_stamp = str(int(time.time()))
    package = f"prepay_id=mock_{order_no}_{nonce_str}"

    # 模拟签名（真实场景使用 RSA 签名）
    sign_str = (
        f"{app_id}\n{time_stamp}\n{nonce_str}\n{package}\n"
    )
    pay_sign = hashlib.sha256(sign_str.encode()).hexdigest()

    return {
        "prepay_id": package.replace("prepay_id=", ""),
        "appId": app_id,
        "timeStamp": time_stamp,
        "nonceStr": nonce_str,
        "package": package,
        "signType": "RSA",
        "paySign": pay_sign,
    }


async def _real_prepay_params(
    order_no: str, amount: float, openid: str, description: str
) -> dict:
    """真实支付：调用微信支付统一下单 API v3（JSAPI 方式）"""
    wx_url = "https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi"
    # 金额单位：分
    total_fen = int(round(amount * 100))

    body = {
        "appid": settings.WX_APPID,
        "mchid": settings.WX_MCH_ID,
        "description": description,
        "out_trade_no": order_no,
        "notify_url": settings.WX_NOTIFY_URL,
        "amount": {"total": total_fen, "currency": "CNY"},
        "payer": {"openid": openid},
    }

    # TODO: 使用微信支付 API v3 的认证方式（商户证书 + RSA 签名）
    # 这里需要加载商户证书和 API v3 密钥
    # 参考：https://pay.weixin.qq.com/wiki/doc/apiv3/wechatpay/wechatpay-1.shtml
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        # "Authorization": _generate_wx_authorization(method="POST", url=wx_url, body=body),
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(wx_url, json=body, headers=headers)
        wx_data = resp.json()

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"微信支付统一下单失败: {wx_data}",
        )

    prepay_id = wx_data.get("prepay_id")
    if not prepay_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="微信支付返回缺少 prepay_id",
        )

    # 生成前端调起支付所需的参数
    nonce_str = _generate_nonce_str()
    time_stamp = str(int(time.time()))
    package = f"prepay_id={prepay_id}"

    # 签名串
    sign_str = f"{settings.WX_APPID}\n{time_stamp}\n{nonce_str}\n{package}\n"
    # TODO: 使用商户证书私钥进行 RSA 签名
    pay_sign = hashlib.sha256(sign_str.encode()).hexdigest()

    return {
        "prepay_id": prepay_id,
        "appId": settings.WX_APPID,
        "timeStamp": time_stamp,
        "nonceStr": nonce_str,
        "package": package,
        "signType": "RSA",
        "paySign": pay_sign,
    }


def _is_mock_payment() -> bool:
    """判断是否使用模拟支付模式"""
    # 当 WX_MCH_ID 为空时自动启用模拟支付
    return not settings.WX_MCH_ID or settings.APP_ENV == "development"


def _handle_subscription_upgrade(user: User, product_type: str, db: Session):
    """处理订阅升级：更新用户的 subscription_status 和 subscription_expire_at"""
    now = datetime.now()

    if product_type == "monthly":
        if user.subscription_status != "none" and user.subscription_expire_at:
            # 续期：在现有到期时间上延长
            new_expire = user.subscription_expire_at + timedelta(days=30)
        else:
            new_expire = now + timedelta(days=30)
        user.subscription_status = "monthly"

    elif product_type == "yearly":
        if user.subscription_status != "none" and user.subscription_expire_at:
            new_expire = user.subscription_expire_at + timedelta(days=365)
        else:
            new_expire = now + timedelta(days=365)
        user.subscription_status = "yearly"

    user.subscription_expire_at = new_expire
    db.commit()


# ============================================================
# API 接口
# ============================================================


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    request: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建支付订单（需 JWT 认证）

    根据 product_type 确定金额：
    - single: 1.9 元（单次查询）
    - monthly: 19 元（月度订阅）
    - yearly: 159 元（年度订阅）
    """
    user_id = current_user.get("user_id")
    openid = current_user.get("openid")

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 确定金额
    amount = _get_product_amount(request.product_type)

    # 生成订单号
    order_no = _generate_order_no()

    # 商品描述
    descriptions = {
        "single": "宠安查-单次症状查询",
        "monthly": "宠安查-月度订阅",
        "yearly": "宠安查-年度订阅",
    }
    description = descriptions.get(request.product_type, "宠安查-支付")

    # 插入订单
    order = Order(
        user_id=user_id,
        order_no=order_no,
        product_type=request.product_type,
        amount=amount,
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 获取前端调支付所需参数
    if _is_mock_payment():
        # 模拟支付模式
        pay_params = _mock_prepay_params(order_no, amount)
    else:
        # 真实支付模式
        pay_params = await _real_prepay_params(
            order_no=order_no,
            amount=amount,
            openid=openid,
            description=description,
        )

    return CreateOrderResponse(
        order_no=order_no,
        amount=amount,
        **pay_params,
    )


@router.post("/notify")
async def pay_notify(request: Request, db: Session = Depends(get_db)):
    """微信支付回调通知（不需要 JWT，微信服务器直接调用）

    接收微信支付的回调通知，验证签名，更新订单状态。
    如果是订阅类型（monthly/yearly），更新用户订阅信息。
    """
    # 读取原始请求体（微信回调为 XML 格式）
    body = await request.body()
    body_str = body.decode("utf-8")

    if _is_mock_payment():
        # 模拟支付回调：从查询参数获取订单号
        # 模拟模式下，前端支付成功后直接调用此接口通知后端
        try:
            data = await request.json()
            order_no = data.get("order_no", "")
            transaction_id = data.get("transaction_id", f"mock_tx_{order_no}")
        except Exception:
            # 兼容 XML 格式
            import xml.etree.ElementTree as ET

            root = ET.fromstring(body_str)
            order_no = root.findtext("out_trade_no", "")
            transaction_id = root.findtext("transaction_id", f"mock_tx_{order_no}")
    else:
        # 真实支付回调：验证微信签名
        # TODO: 验证微信支付回调签名
        # 参考：https://pay.weixin.qq.com/wiki/doc/apiv3/wechatpay/wechatpay-4.shtml
        import xml.etree.ElementTree as ET

        root = ET.fromstring(body_str)
        order_no = root.findtext("out_trade_no", "")
        transaction_id = root.findtext("transaction_id", "")

        # 验证签名（TODO）
        # if not _verify_wx_notify_signature(request, body_str):
        #     return _xml_response("FAIL", "签名验证失败")

    if not order_no:
        return _xml_response("FAIL", "缺少订单号")

    # 查询订单
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        return _xml_response("FAIL", "订单不存在")

    if order.status == "paid":
        # 已支付，重复通知直接返回成功
        return _xml_response("SUCCESS", "OK")

    # 更新订单状态
    order.status = "paid"
    order.pay_time = datetime.now()
    order.wx_transaction_id = transaction_id
    db.commit()

    # 如果是订阅类型，更新用户订阅信息
    if order.product_type in ("monthly", "yearly"):
        user = db.query(User).filter(User.id == order.user_id).first()
        if user:
            _handle_subscription_upgrade(user, order.product_type, db)

    return _xml_response("SUCCESS", "OK")


@router.get("/query/{order_no}", response_model=OrderQueryResponse)
def query_order(
    order_no: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询订单支付状态（需 JWT 认证）"""
    user_id = current_user.get("user_id")

    order = (
        db.query(Order)
        .filter(Order.order_no == order_no, Order.user_id == user_id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )

    return OrderQueryResponse(
        order_no=order.order_no,
        status=order.status,
        amount=float(order.amount),
        pay_time=str(order.pay_time) if order.pay_time else None,
        product_type=order.product_type,
    )


# ============================================================
# 内部工具函数
# ============================================================


def _xml_response(return_code: str, return_msg: str) -> str:
    """生成微信支付回调 XML 响应"""
    return f"""<xml>
    <return_code><![CDATA[{return_code}]]></return_code>
    <return_msg><![CDATA[{return_msg}]]></return_msg>
</xml>"""
