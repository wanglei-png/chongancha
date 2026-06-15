"""宠物档案 CRUD 路由"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.pet import Pet
from models.user import User
from utils.jwt_utils import get_current_user_optional

router = APIRouter(prefix="/api/v1/pets", tags=["宠物档案"])


# ============================================================
# Pydantic 请求/响应模型
# ============================================================

class PetCreate(BaseModel):
    name: str = Field(default="宠物", max_length=32)
    species: str = Field(..., pattern="^(cat|dog)$")
    breed: str = Field(..., max_length=64)
    age_type: str = Field(..., pattern="^(baby|adult|senior)$")
    age_months: Optional[int] = None
    weight: Optional[float] = None
    weight_unit: str = Field(default="kg", pattern="^(kg|jin)$")


class PetUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=32)
    species: Optional[str] = Field(None, pattern="^(cat|dog)$")
    breed: Optional[str] = Field(None, max_length=64)
    age_type: Optional[str] = Field(None, pattern="^(baby|adult|senior)$")
    age_months: Optional[int] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = Field(None, pattern="^(kg|jin)$")


class PetResponse(BaseModel):
    id: int
    user_id: int
    name: str
    species: str
    breed: str
    age_type: str
    age_months: Optional[int] = None
    weight: Optional[float] = None
    weight_unit: str
    created_at: str

    class Config:
        from_attributes = True


# ============================================================
# 内存存储（MVP 阶段无数据库时使用）
# ============================================================

MOCK_PETS = []
MOCK_NEXT_ID = 1


def _get_user_id(current_user) -> int:
    """获取用户 ID，未登录返回 0"""
    if current_user and isinstance(current_user, dict) and "user_id" in current_user:
        return current_user["user_id"]
    return 0


# ============================================================
# API 接口
# ============================================================

@router.get("/", response_model=List[PetResponse])
def list_pets(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """获取宠物列表"""
    user_id = _get_user_id(current_user)
    
    # MVP 阶段：返回所有宠物（不区分用户）
    return MOCK_PETS


@router.post("/", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
def create_pet(
    pet_data: PetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """创建宠物档案"""
    global MOCK_NEXT_ID
    
    user_id = _get_user_id(current_user)
    
    pet = {
        "id": MOCK_NEXT_ID,
        "user_id": user_id,
        "name": pet_data.name,
        "species": pet_data.species,
        "breed": pet_data.breed,
        "age_type": pet_data.age_type,
        "age_months": pet_data.age_months,
        "weight": pet_data.weight,
        "weight_unit": pet_data.weight_unit,
        "created_at": "2026-06-15 10:00:00",
    }
    
    MOCK_PETS.append(pet)
    MOCK_NEXT_ID += 1
    
    return pet


@router.get("/{pet_id}", response_model=PetResponse)
def get_pet(
    pet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """获取单个宠物档案"""
    for pet in MOCK_PETS:
        if pet["id"] == pet_id:
            return pet
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="宠物档案不存在",
    )


@router.put("/{pet_id}", response_model=PetResponse)
def update_pet(
    pet_id: int,
    pet_data: PetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """更新宠物档案"""
    for i, pet in enumerate(MOCK_PETS):
        if pet["id"] == pet_id:
            update_data = pet_data.model_dump(exclude_unset=True)
            MOCK_PETS[i].update(update_data)
            return MOCK_PETS[i]
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="宠物档案不存在",
    )


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pet(
    pet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """删除宠物档案"""
    for i, pet in enumerate(MOCK_PETS):
        if pet["id"] == pet_id:
            MOCK_PETS.pop(i)
            return None
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="宠物档案不存在",
    )
