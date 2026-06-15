"""数据库初始化脚本
创建所有表并插入症状知识库种子数据
用法: python init_db.py
"""

from database import SessionLocal, init_db

# 导入所有模型类，确保 Base.metadata 注册所有表
from models.user import User
from models.pet import Pet
from models.symptom import Symptom
from models.order import Order
from models.query_record import QueryRecord

# 从数据文件导入症状种子数据
from symptom_seeds import SYMPTOM_SEEDS


def main():
    print("=" * 50)
    print("宠急查 - 数据库初始化")
    print("=" * 50)

    # 创建所有表
    print("\n[1/3] 创建数据库表...")
    init_db()
    print("✅ 数据库表创建完成")

    # 插入种子数据
    print("\n[2/3] 插入症状知识库种子数据...")
    db = SessionLocal()
    try:
        # 清空现有症状数据
        deleted = db.query(Symptom).delete()
        print(f"   已清空 {deleted} 条现有症状数据")

        # 批量插入
        for idx, seed in enumerate(SYMPTOM_SEEDS, 1):
            # 确保所有种子数据 audit_status 为 approved
            seed['audit_status'] = 'approved'
            symptom = Symptom(**seed)
            db.add(symptom)

        db.commit()
        print(f"✅ 成功插入 {len(SYMPTOM_SEEDS)} 条症状知识库数据")
    except Exception as e:
        db.rollback()
        print(f"❌ 插入数据失败: {e}")
        raise
    finally:
        db.close()

    print("\n[3/3] 验证数据...")
    db = SessionLocal()
    try:
        count = db.query(Symptom).count()
        print(f"   symptoms 表中共 {count} 条记录")
        for s in db.query(Symptom).order_by(Symptom.symptom_id).all():
            print(f"   - {s.symptom_id}: {s.symptom_name}")
    finally:
        db.close()

    print("\n" + "=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
