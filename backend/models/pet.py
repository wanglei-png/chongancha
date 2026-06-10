"""宠物档案模型"""

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


class Pet(Base):
    """宠物档案表"""

    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(32), default="宠物", nullable=False)
    species = Column(Enum("cat", "dog"), nullable=False)
    breed = Column(String(64), nullable=False)
    age_type = Column(Enum("baby", "adult", "senior"), nullable=False)
    age_months = Column(Integer, nullable=True)
    weight = Column(DECIMAL(5, 2), nullable=True)
    weight_unit = Column(Enum("kg", "jin"), default="kg", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 关联
    owner = relationship("User", back_populates="pets")
    query_records = relationship("QueryRecord", back_populates="pet")

    def __repr__(self):
        return f"<Pet(id={self.id}, name='{self.name}', species='{self.species}')>"
