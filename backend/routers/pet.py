"""宠物档案 CRUD 路由"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.pet import Pet
from models.user import User

router = APIRouter(prefix="/api/pets", tags=["宠物档案"])


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


@router.get("/", response_model=List[PetResponse])
def list_pets(
    user_id: int,
    db: Session = Depends(get_db),
):
    """获取用户的所有宠物档案"""
    pets = db.query(Pet).filter(Pet.user_id == user_id).all()
    return pets


@router.post("/", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
def create_pet(
    pet_data: PetCreate,
    user_id: int,
    db: Session = Depends(get_db),
):
    """创建宠物档案"""
    # 验证用户存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    pet = Pet(
        user_id=user_id,
        name=pet_data.name,
        species=pet_data.species,
        breed=pet_data.breed,
        age_type=pet_data.age_type,
        age_months=pet_data.age_months,
        weight=pet_data.weight,
        weight_unit=pet_data.weight_unit,
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


@router.get("/{pet_id}", response_model=PetResponse)
def get_pet(pet_id: int, db: Session = Depends(get_db)):
    """获取单个宠物档案"""
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="宠物档案不存在",
        )
    return pet


@router.put("/{pet_id}", response_model=PetResponse)
def update_pet(
    pet_id: int,
    pet_data: PetUpdate,
    db: Session = Depends(get_db),
):
    """更新宠物档案"""
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="宠物档案不存在",
        )

    update_data = pet_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pet, field, value)

    db.commit()
    db.refresh(pet)
    return pet


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pet(pet_id: int, db: Session = Depends(get_db)):
    """删除宠物档案"""
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="宠物档案不存在",
        )
    db.delete(pet)
    db.commit()
    return None
