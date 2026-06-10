"""微信支付服务"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from config import settings
from models.order import Order


class PaymentService:
    """微信支付服务封装"""

    def __init__(self, db: Session):
        self.db = db
        self.appid = settings.WX_APPID
        self.mch_id = settings.WX_MCH_ID
        self.api_key = settings.WX_API_KEY
        self.notify_url = settings.WX_NOTIFY_URL

    def create_order(
        self,
        user_id: int,
        product_type: str,
        amount: float,
        order_no: str,
    ) -> Order:
        """创建订单"""
        order = Order(
            user_id=user_id,
            order_no=order_no,
            product_type=product_type,
            amount=amount,
            status="pending",
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    async def request_wx_pay(self, order: Order, openid: str) -> Dict[str, Any]:
        """请求微信支付统一下单（占位实现）"""
        # TODO: 调用微信支付统一下单 API
        # 参考文档：https://pay.weixin.qq.com/wiki/doc/apiv3/apis/chapter3_5_1.shtml
        return {
            "prepay_id": "mock_prepay_id",
            "order_no": order.order_no,
        }

    def handle_pay_notify(self, order_no: str, transaction_id: str) -> Optional[Order]:
        """处理支付回调"""
        order = (
            self.db.query(Order)
            .filter(Order.order_no == order_no)
            .first()
        )
        if order and order.status == "pending":
            order.status = "paid"
            order.pay_time = datetime.now()
            order.wx_transaction_id = transaction_id
            self.db.commit()
            self.db.refresh(order)
        return order

    def get_order_by_no(self, order_no: str) -> Optional[Order]:
        """根据订单号查询订单"""
        return (
            self.db.query(Order)
            .filter(Order.order_no == order_no)
            .first()
        )
