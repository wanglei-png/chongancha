from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from database import Base
from datetime import datetime

class Promotion(Base):
    __tablename__ = "promotions"
    __table_args__ = {"comment": "优惠券/活动配置表"}
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="活动ID")
    code = Column(String(32), unique=True, nullable=False, comment="兑换码，如CAT2026")
    name = Column(String(64), nullable=False, comment="活动名称")
    discount_type = Column(String(20), nullable=False, comment="优惠类型：percent-折扣/fixed-固定减免/free-免费体验")
    discount_value = Column(Float, nullable=False, comment="优惠值（折扣率或减免金额）")
    valid_days = Column(Integer, default=7, comment="兑换后有效天数")
    max_uses = Column(Integer, default=100, comment="最大使用次数")
    used_count = Column(Integer, default=0, comment="已使用次数")
    is_active = Column(Boolean, default=True, comment="是否生效")
    start_at = Column(DateTime, nullable=True, comment="活动开始时间")
    end_at = Column(DateTime, nullable=True, comment="活动结束时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
