from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from database import get_db
from services.llm_service import generate_summary
from services.vector_service import get_vector_service
from utils.jwt_utils import get_current_user_optional

router = APIRouter(prefix="/api/v1/summary", tags=["病情摘要"])

class SummaryRequest(BaseModel):
    symptom_id: str
    symptom_name: Optional[str] = None
    pet_name: Optional[str] = Field(default="宠物", max_length=32)
    breed: str
    age_type: str = Field(pattern="^(baby|adult|senior)$")
    weight: Optional[float] = None
    weight_unit: str = Field(default="kg", pattern="^(kg|jin)$")
    actions_taken: str = Field(default="", max_length=500)
    use_llm: bool = Field(default=False, description="是否使用LLM生成")
    query_id: Optional[int] = None

class SummaryResponse(BaseModel):
    summary: str
    is_llm_generated: bool
    is_filtered: bool
    cost: float = 0.0
    latency: int = 0
    similar_symptoms: List[Dict[str, Any]] = []


@router.post("/generate", response_model=SummaryResponse)
def create_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """
    生成病情摘要
    - use_llm=False: 使用模板生成（免费/默认）
    - use_llm=True: 调用LLM生成（需付费权限，V2.0默认关闭）
    - 返回相似症状推荐（V2.1）
    """
    
    # 获取症状数据
    from models.symptom import Symptom
    symptom = db.query(Symptom).filter(Symptom.symptom_id == request.symptom_id).first()
    
    if not symptom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="症状不存在"
        )
    
    symptom_data = {
        "symptom_name": symptom.symptom_name,
        "home_observation": symptom.home_observation,
        "absolute_prohibitions": symptom.absolute_prohibitions,
        "red_flags": symptom.red_flags
    }
    
    pet_info = {
        "name": request.pet_name,
        "breed": request.breed,
        "age_type": request.age_type,
        "weight": request.weight,
        "weight_unit": request.weight_unit
    }
    
    # V2.0 默认关闭 LLM，即使 use_llm=True 也先走模板
    FORCE_TEMPLATE = True  # 开关：True=强制模板，False=允许LLM
    
    summary_result = None
    
    if request.use_llm and not FORCE_TEMPLATE:
        summary_result = generate_summary(
            pet_info=pet_info,
            symptom_data=symptom_data,
            actions_taken=request.actions_taken,
            db=db,
            user_id=current_user.get("user_id") if current_user else None,
            query_id=request.query_id
        )
    else:
        # 模板生成（V1.x 默认）
        template = (
            f"{request.pet_name}，{request.breed}，{request.age_type}，"
            f"体重{request.weight}{request.weight_unit}。宠物出现{symptom.symptom_name}症状，"
            f"主人已采取措施：{request.actions_taken}。"
            f"建议持续观察宠物精神状态、食欲和排泄情况，"
            f"如出现就医触发条件中的任何一项，请立即前往正规动物医院就诊。"
            f"以上信息仅供参考，不能替代专业兽医诊断。"
        )
        
        summary_result = {
            "summary": template,
            "is_llm": False,
            "is_filtered": False,
            "cost": 0.0,
            "latency": 0
        }
    
    # V2.1 获取相似症状推荐
    similar_symptoms = []
    try:
        vs = get_vector_service()
        similar = vs.get_similar_symptoms(request.symptom_id, top_k=3)
        similar_symptoms = similar
    except Exception as e:
        print(f"[Summary] 获取相似症状失败: {e}")
        similar_symptoms = []
    
    return SummaryResponse(
        summary=summary_result["summary"],
        is_llm_generated=summary_result["is_llm"],
        is_filtered=summary_result["is_filtered"],
        cost=summary_result["cost"],
        latency=summary_result["latency"],
        similar_symptoms=similar_symptoms
    )
