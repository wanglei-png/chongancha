"""查询记录模型"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database import Base


class QueryRecord(Base):
    """症状查询记录表"""

    __tablename__ = "query_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True)
    symptom_id = Column(String(32), nullable=False, comment="症状标识")
    result_data = Column(JSON, nullable=True, comment="完整的决策清单结果")
    is_paid = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 关联
    user = relationship("User", back_populates="query_records")
    pet = relationship("Pet", back_populates="query_records")

    def __repr__(self):
        return f"<QueryRecord(id={self.id}, symptom_id='{self.symptom_id}')>"
