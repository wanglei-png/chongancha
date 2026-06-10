"""症状查询 & 决策清单路由"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database import get_db
from models.symptom import Symptom

router = APIRouter(prefix="/api/v1/symptoms", tags=["症状查询"])


# ============================================================
# Pydantic 请求/响应模型
# ============================================================


class SymptomListItem(BaseModel):
    """症状列表项（用于前端症状选择器）"""

    symptom_id: str
    symptom_name: str
    applicable_pets: List[str]
    icon_emoji: str = ""
    audit_status: str = "approved"

    class Config:
        from_attributes = True

    @field_validator("applicable_pets", mode="before")
    @classmethod
    def parse_applicable_pets(cls, v):
        """自动将 JSON 字符串解析为 Python 列表"""
        if isinstance(v, str):
            return json.loads(v)
        return v


class SymptomQueryRequest(BaseModel):
    """症状查询请求"""

    symptom_id: str = Field(..., description="症状标识，如 vomiting_cat")
    species: str = Field(..., description="宠物物种，cat 或 dog")
    breed: str = Field(default="", description="品种")
    age_type: str = Field(default="", description="年龄阶段")
    weight: Optional[float] = Field(default=None, description="体重")


class ObservationItem(BaseModel):
    """观察建议项"""

    action: str
    source: str
    confidence: str


class ProhibitionItem(BaseModel):
    """禁止行为项"""

    action: str
    source: str
    severity: str


class RedFlagItem(BaseModel):
    """就医触发条件项"""

    condition: str
    action: str
    priority: str


class SymptomQueryResponse(BaseModel):
    """完整决策清单响应"""

    symptom_name: str
    home_observation: List[Dict[str, Any]]
    absolute_prohibitions: List[Dict[str, Any]]
    red_flags: List[Dict[str, Any]]
    vet_summary_template: Optional[str] = None
    audit_status: str = "approved"


class SymptomFreeQueryResponse(BaseModel):
    """免费查询响应（居家观察仅返回前2条）"""

    symptom_name: str
    home_observation: List[Dict[str, Any]]
    home_observation_total: int = 0
    absolute_prohibitions: List[Dict[str, Any]]
    red_flags: List[Dict[str, Any]]
    is_paid: bool = False
    vet_summary_template: Optional[str] = None
    audit_status: str = "approved"


# ============================================================
# 辅助函数
# ============================================================


def _get_symptom_or_404(db: Session, symptom_id: str) -> Symptom:
    """根据 symptom_id 查询症状，不存在则抛出 404"""
    symptom = (
        db.query(Symptom)
        .filter(Symptom.symptom_id == symptom_id)
        .first()
    )
    if not symptom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"症状 '{symptom_id}' 不存在",
        )
    return symptom


def _validate_species_match(symptom: Symptom, species: str):
    """校验症状适用的宠物物种是否匹配，不匹配则抛出 400"""
    applicable_pets = symptom.applicable_pets
    # 兼容数据库存储为 JSON 字符串的情况
    if isinstance(applicable_pets, str):
        applicable_pets = json.loads(applicable_pets)
    if species not in applicable_pets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"症状 '{symptom.symptom_name}' 不适用于 {species}，"
            f"仅适用于: {'/'.join(applicable_pets)}",
        )


def parse_json_field(field):
    """将 JSON 字符串解析为 Python 对象，如果已经是列表/字典则直接返回"""
    if isinstance(field, str):
        return json.loads(field)
    return field


def _normalize_red_flags(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """补齐 red_flags 的来源信息，避免前端缺少 source/priority 显示标签。"""
    normalized = []
    for item in items or []:
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        entry = dict(item)
        entry.setdefault("source", "兽医临床指南")
        entry.setdefault("priority", "urgent")
        normalized.append(entry)
    return normalized


# ============================================================
# API 接口
# ============================================================


@router.get("", response_model=List[SymptomListItem])
def list_symptoms(db: Session = Depends(get_db)):
    """获取所有症状列表（用于前端症状选择器）"""
    symptoms = db.query(Symptom).all()
    return [
        SymptomListItem(
            symptom_id=s.symptom_id,
            symptom_name=s.symptom_name,
            applicable_pets=s.applicable_pets,
            icon_emoji=_get_icon_emoji(s.symptom_id),
            audit_status=s.audit_status or "approved",
        )
        for s in symptoms
    ]


@router.post("/query", response_model=SymptomQueryResponse)
def query_symptom(
    request: SymptomQueryRequest,
    db: Session = Depends(get_db),
):
    """付费查询：返回完整决策清单"""
    symptom = _get_symptom_or_404(db, request.symptom_id)
    _validate_species_match(symptom, request.species)

    return SymptomQueryResponse(
        symptom_name=symptom.symptom_name,
        home_observation=parse_json_field(symptom.home_observation) or [],
        absolute_prohibitions=parse_json_field(symptom.absolute_prohibitions) or [],
        red_flags=_normalize_red_flags(parse_json_field(symptom.red_flags) or []),
        vet_summary_template=symptom.vet_summary_template,
        audit_status=symptom.audit_status or "approved",
    )


@router.post("/query-free", response_model=SymptomFreeQueryResponse)
def query_symptom_free(
    request: SymptomQueryRequest,
    db: Session = Depends(get_db),
):
    """免费查询：居家观察仅返回前2条，禁止行为和就医条件全部返回"""
    symptom = _get_symptom_or_404(db, request.symptom_id)
    _validate_species_match(symptom, request.species)

    home_obs = parse_json_field(symptom.home_observation) or []
    # 免费版只返回前2条居家观察建议
    truncated_home_obs = home_obs[:2]

    return SymptomFreeQueryResponse(
        symptom_name=symptom.symptom_name,
        home_observation=truncated_home_obs,
        home_observation_total=len(home_obs),
        absolute_prohibitions=parse_json_field(symptom.absolute_prohibitions) or [],
        red_flags=_normalize_red_flags(parse_json_field(symptom.red_flags) or []),
        is_paid=False,
        vet_summary_template=symptom.vet_summary_template,
        audit_status=symptom.audit_status or "approved",
    )


# ============================================================
# 内部工具函数
# ============================================================


def _get_icon_emoji(symptom_id: str) -> str:
    """根据 symptom_id 返回对应的 emoji 图标"""
    icon_map = {
        "vomiting": "🤮",
        "diarrhea": "💩",
        "skin": "🐾",
        "eye": "👁️",
        "appetite": "🍽️",
    }
    for key, emoji in icon_map.items():
        if key in symptom_id:
            return emoji
    return "🩺"
