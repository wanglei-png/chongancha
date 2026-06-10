"""订单模型"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    DECIMAL,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database import Base


class Order(Base):
    """订单表"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_no = Column(String(32), unique=True, nullable=False, comment="商户订单号")
    product_type = Column(
        Enum("single", "monthly", "yearly"),
        nullable=False,
        comment="商品类型：单次查询/月度订阅/年度订阅",
    )
    amount = Column(DECIMAL(10, 2), nullable=False, comment="金额，单位：元")
    status = Column(
        Enum("pending", "paid", "cancelled", "refunded"),
        default="pending",
        nullable=False,
    )
    pay_time = Column(DateTime, nullable=True)
    wx_transaction_id = Column(String(64), nullable=True, comment="微信支付交易号")
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 关联
    user = relationship("User", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, order_no='{self.order_no}', status='{self.status}')>"
