"""
症状向量索引初始化脚本
在应用启动时执行一次，将所有症状数据向量化并索引到 Milvus Lite
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.vector_service import get_vector_service, VectorService
from database import SessionLocal
from models.symptom import Symptom


def init_vector_index():
    """
    从数据库读取所有症状，构建向量索引
    """
    print("=" * 50)
    print("开始初始化症状向量索引...")
    print("=" * 50)

    # 获取向量服务
    vs = get_vector_service()

    # 检查当前索引状态
    stats = vs.get_stats()
    print(f"当前向量库状态: {stats}")

    # 如果已有数据，跳过（避免不必要的模型下载）
    if stats.get("total_vectors", 0) > 0:
        print(f"向量库已有 {stats['total_vectors']} 条数据，跳过索引")
        return

    # 从数据库读取症状
    db = SessionLocal()
    try:
        symptoms = db.query(Symptom).all()
        print(f"从数据库读取到 {len(symptoms)} 条症状")

        if not symptoms:
            print("警告: 数据库中没有症状数据，跳过索引")
            return

        # 准备批量索引数据
        symptom_list = []
        for s in symptoms:
            # 构建描述文本（包含症状名和关键信息）
            description = f"宠物{s.symptom_name}症状"

            symptom_list.append({
                "symptom_id": s.symptom_id,
                "symptom_name": s.symptom_name,
                "description": description
            })

        # 批量索引
        result = vs.batch_index_symptoms(symptom_list)
        print(f"索引结果: {result}")

        # 验证索引
        stats = vs.get_stats()
        print(f"索引后向量库状态: {stats}")

        # 测试检索
        test_queries = [
            "我家猫吐了",
            "狗狗拉肚子",
            "猫咪皮肤发红",
            "小狗不吃东西"
        ]

        print("\n测试检索:")
        for query in test_queries:
            results = vs.search(query, top_k=3, threshold=0.3)
            print(f"\n查询: '{query}'")
            for r in results:
                print(f"  → {r['symptom_name']} (相似度: {r['similarity']})")

        print("\n" + "=" * 50)
        print("向量索引初始化完成!")
        print("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    init_vector_index()
