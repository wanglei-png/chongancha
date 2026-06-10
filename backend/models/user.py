"""用户模型"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(64), unique=True, index=True, nullable=False)
    unionid = Column(String(64), nullable=True)
    nickname = Column(String(64), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    subscription_status = Column(
        Enum("none", "monthly", "yearly"),
        default="none",
        nullable=False,
    )
    subscription_expire_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )

    # 关联
    pets = relationship("Pet", back_populates="owner")
    query_records = relationship("QueryRecord", back_populates="user")
    orders = relationship("Order", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, openid='{self.openid}')>"
