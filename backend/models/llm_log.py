from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from database import Base
from datetime import datetime

class LLMLog(Base):
    __tablename__ = "llm_logs"
    __table_args__ = {"comment": "LLM调用审计日志表"}
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="日志ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    query_id = Column(Integer, nullable=True, comment="关联查询记录ID")
    model_name = Column(String(32), nullable=False, comment="模型名称，如deepseek-chat")
    prompt = Column(Text, nullable=False, comment="完整Prompt输入")
    response = Column(Text, nullable=True, comment="模型输出")
    is_filtered = Column(Boolean, default=False, comment="是否触发敏感词过滤")
    filter_reason = Column(String(255), nullable=True, comment="过滤原因")
    latency_ms = Column(Integer, nullable=True, comment="调用耗时（毫秒）")
    cost_cny = Column(Float, nullable=True, comment="本次调用成本（元）")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
