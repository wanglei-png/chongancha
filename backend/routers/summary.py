"""病情摘要生成路由"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from models.query_record import QueryRecord
from models.symptom import Symptom
from utils.jwt_utils import get_current_user_optional

router = APIRouter(prefix="/api/v1/summary", tags=["病情摘要"])


# ============================================================
# Pydantic 请求/响应模型
# ============================================================


class SummaryGenerateRequest(BaseModel):
    """病情摘要生成请求"""

    symptom_id: str = Field(..., description="症状标识，如 vomiting_cat")
    pet_name: str = Field(default="", description="宠物名称")
    breed: str = Field(default="", description="品种")
    age: str = Field(default="", description="年龄描述，如幼年/成年/老年")
    weight: str = Field(default="", description="体重，如 3.5kg")
    duration: str = Field(default="", description="病情持续时长")
    actions_taken: List[str] = Field(
        default_factory=list, description="已采取的措施列表"
    )
    observations: str = Field(default="", description="观察描述")
    other_symptoms: str = Field(default="", description="伴随症状")
    status: str = Field(default="", description="当前精神状态")


class SummaryGenerateResponse(BaseModel):
    """病情摘要生成响应"""

    summary: str
    generated_at: str


# ============================================================
# API 接口
# ============================================================


@router.post("/generate", response_model=SummaryGenerateResponse)
def generate_summary(
    request: SummaryGenerateRequest,
    db: Session = Depends(get_db),
):
    """生成病情摘要（可选 JWT 认证，未登录也可使用）

    从 symptoms 表查询 vet_summary_template，
    用请求体中的字段替换模板占位符，生成摘要文本。
    """
    user_id = None

    # 查询症状知识库，获取摘要模板
    symptom = (
        db.query(Symptom)
        .filter(Symptom.symptom_id == request.symptom_id)
        .first()
    )
    if not symptom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"症状 '{request.symptom_id}' 不存在",
        )

    # 获取模板，如果没有模板则使用默认模板
    template = symptom.vet_summary_template or (
        "宠物{pet_name}，{breed}，{age}。"
        "于{time}出现{symptom_name}症状，"
        "已采取{actions}。"
        "目前精神状态{status}。"
    )

    # 生成当前时间字符串
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M")

    def safe_text(value: Any, fallback: str = "未提供") -> str:
        if value is None:
            return fallback
        if isinstance(value, list):
            return "、".join([str(item).strip() for item in value if str(item).strip()]) or fallback
        text = str(value).strip()
        return text or fallback

    # 构建替换映射，兼容数据库旧模板与新模板
    replacements = {
        "{pet_name}": safe_text(request.pet_name, "未命名宠物"),
        "{breed}": safe_text(request.breed),
        "{age}": safe_text(request.age),
        "{weight}": safe_text(request.weight),
        "{time}": time_str,
        "{actions}": safe_text(request.actions_taken, "未提供"),
        "{observations}": safe_text(request.observations),
        "{other_symptoms}": safe_text(request.other_symptoms),
        "{duration}": safe_text(request.duration),
        "{status}": safe_text(request.status, "未提供"),
        "{symptom}": safe_text(symptom.symptom_name),
        "{symptom_name}": safe_text(symptom.symptom_name),
    }

    # 先替换已知占位符，再做兜底清理，避免残留 {xxx}
    summary = re.sub(r"\{[^{}]+\}", lambda m: replacements.get(m.group(0), ""), template)
    summary = re.sub(r"\{[^{}]+\}", lambda m: "", summary)

    # 构建 result_data（包含完整摘要和原始参数）
    result_data = {
        "summary": summary,
        "generated_at": now.isoformat(),
        "symptom_name": symptom.symptom_name,
        "request_params": {
            "symptom_id": request.symptom_id,
            "pet_name": request.pet_name,
            "breed": request.breed,
            "age": request.age,
            "weight": request.weight,
            "duration": request.duration,
            "actions_taken": request.actions_taken,
            "observations": request.observations,
            "other_symptoms": request.other_symptoms,
            "status": request.status,
        },
    }

    # 保存查询记录
    record = QueryRecord(
        user_id=user_id,
        pet_id=None,  # 摘要生成不关联具体宠物档案 ID
        symptom_id=request.symptom_id,
        result_data=result_data,
        is_paid=True,
    )
    db.add(record)
    db.commit()

    return SummaryGenerateResponse(
        summary=summary,
        generated_at=now.isoformat(),
    )
