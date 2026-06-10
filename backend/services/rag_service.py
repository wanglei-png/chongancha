"""RAG 知识库检索服务"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.symptom import Symptom


class RAGService:
    """基于 SQL 的知识库检索服务（后续可扩展为向量检索）"""

    def __init__(self, db: Session):
        self.db = db

    def get_symptom_by_id(self, symptom_id: str) -> Optional[Symptom]:
        """根据 symptom_id 获取症状知识条目"""
        return (
            self.db.query(Symptom)
            .filter(Symptom.symptom_id == symptom_id)
            .first()
        )

    def search_symptoms(self, keyword: str, species: Optional[str] = None) -> List[Symptom]:
        """搜索症状知识库"""
        query = self.db.query(Symptom).filter(
            Symptom.symptom_name.contains(keyword)
        )
        if species:
            query = query.filter(
                Symptom.applicable_pets.contains(species)
            )
        return query.all()

    def get_decision_list(self, symptom_id: str) -> Optional[Dict[str, Any]]:
        """获取完整决策清单"""
        symptom = self.get_symptom_by_id(symptom_id)
        if not symptom:
            return None
        return {
            "symptom_id": symptom.symptom_id,
            "symptom_name": symptom.symptom_name,
            "applicable_pets": symptom.applicable_pets,
            "home_observation": symptom.home_observation or [],
            "absolute_prohibitions": symptom.absolute_prohibitions or [],
            "red_flags": symptom.red_flags or [],
            "vet_summary_template": symptom.vet_summary_template,
        }
