"""症状知识库模型"""

from sqlalchemy import Column, Integer, String, Date, Text, JSON, Enum

from database import Base


class Symptom(Base):
    """症状知识库表"""

    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symptom_id = Column(String(32), unique=True, nullable=False, comment="症状标识，如 'vomiting_cat'")
    symptom_name = Column(String(32), nullable=False, comment="症状名称，如 '猫咪呕吐'")
    applicable_pets = Column(JSON, nullable=False, comment="适用宠物类型，如 ['cat']")
    home_observation = Column(
        JSON,
        nullable=True,
        comment="家庭观察建议，[{action, source, confidence}]",
    )
    absolute_prohibitions = Column(
        JSON,
        nullable=True,
        comment="绝对禁止事项，[{action, source, severity}]",
    )
    red_flags = Column(
        JSON,
        nullable=True,
        comment="危险信号，[{condition, action, priority}]",
    )
    vet_summary_template = Column(Text, nullable=True, comment="兽医摘要模板")
    last_reviewed = Column(Date, nullable=True, comment="最后审核日期")
    reviewer_vet = Column(String(64), nullable=True, comment="审核兽医姓名")
    audit_status = Column(
        Enum('pending', 'reviewing', 'approved', name='audit_status_enum'),
        nullable=False,
        default='pending',
        comment="审核状态: pending=待审核, reviewing=审核中, approved=已审核",
    )

    def __repr__(self):
        return f"<Symptom(id={self.id}, symptom_id='{self.symptom_id}', name='{self.symptom_name}')>"
