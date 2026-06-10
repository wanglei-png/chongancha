"""事件埋点模型"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey

from database import Base


class Event(Base):
    """事件埋点表"""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID")
    event_type = Column(
        String(32),
        nullable=False,
        comment="事件类型: symptom_select, pay_modal_show, pay_click, pay_success, summary_generate, share_click",
    )
    event_data = Column(JSON, nullable=True, comment="事件附加数据")
    created_at = Column(DateTime, default=datetime.now, comment="事件发生时间")

    def __repr__(self):
        return f"<Event(id={self.id}, type='{self.event_type}', time='{self.created_at}')>"
