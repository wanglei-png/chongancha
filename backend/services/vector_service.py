import os
import sys
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

# ========== 模型加载配置（国内镜像）==========

# 方案1：HF-Mirror（默认）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HOME'] = os.path.join(os.path.dirname(__file__), '..', 'models_cache')
os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.environ['HF_HOME']

# 确保缓存目录存在
os.makedirs(os.environ['HF_HOME'], exist_ok=True)

# 向量模型
MODEL = None
EMBEDDING_DIM = 1024  # bge-m3 输出1024维向量
_MODEL_READY = False

def _load_model():
    """惰性加载模型，支持多通道"""
    global MODEL, _MODEL_READY
    
    if _MODEL_READY and MODEL is not None:
        return True
    
    print("[VectorService] 正在加载 bge-m3 模型...")
    
    # 通道1：HF-Mirror
    try:
        from sentence_transformers import SentenceTransformer
        MODEL = SentenceTransformer('BAAI/bge-m3')
        _MODEL_READY = True
        print("[VectorService] ✅ 模型加载成功（HF-Mirror）")
        return True
    except Exception as e1:
        print(f"[VectorService] HF-Mirror 失败: {e1}")
    
    # 通道2：ModelScope（备用）
    try:
        print("[VectorService] 尝试 ModelScope 通道...")
        os.system("pip install modelscope -q")
        from modelscope import snapshot_download
        
        model_dir = snapshot_download('BAAI/bge-m3', cache_dir=os.environ['HF_HOME'])
        from sentence_transformers import SentenceTransformer
        MODEL = SentenceTransformer(model_dir)
        _MODEL_READY = True
        print("[VectorService] ✅ 模型加载成功（ModelScope）")
        return True
    except Exception as e2:
        print(f"[VectorService] ModelScope 失败: {e2}")
    
    # 通道3：本地缓存检查
    try:
        from sentence_transformers import SentenceTransformer
        cache_dir = os.environ['HF_HOME']
        possible_paths = [
            os.path.join(cache_dir, 'models--BAAI--bge-m3'),
            os.path.join(cache_dir, 'BAAI', 'bge-m3'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                MODEL = SentenceTransformer(path)
                _MODEL_READY = True
                print(f"[VectorService] ✅ 模型加载成功（本地缓存: {path}）")
                return True
    except Exception as e3:
        print(f"[VectorService] 本地缓存失败: {e3}")
    
    print("[VectorService] ❌ 所有通道失败，模型未加载")
    _MODEL_READY = False
    return False


# Milvus Lite（本地文件存储，无需额外服务）
from pymilvus import MilvusClient, DataType

# Milvus Lite 数据文件路径
MILVUS_DB_PATH = os.getenv("MILVUS_DB_PATH", "./milvus_pet_health.db")
COLLECTION_NAME = "symptom_vectors"


class VectorService:
    """
    Milvus Lite 向量检索服务
    负责：症状文本向量化、索引构建、相似度检索
    """
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 Milvus Lite 客户端"""
        try:
            self.client = MilvusClient(uri=MILVUS_DB_PATH)
            print(f"[VectorService] Milvus Lite 初始化成功: {MILVUS_DB_PATH}")
            
            # 检查集合是否存在
            collections = self.client.list_collections()
            if COLLECTION_NAME not in collections:
                self._create_collection()
                
        except Exception as e:
            print(f"[VectorService] 初始化失败: {e}")
            raise
    
    def _create_collection(self):
        """创建向量集合"""
        schema = MilvusClient.create_schema(
            auto_id=True,
            enable_dynamic_field=True,
        )
        
        # 添加字段
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
        schema.add_field(field_name="symptom_id", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="symptom_name", datatype=DataType.VARCHAR, max_length=128)
        schema.add_field(field_name="description", datatype=DataType.VARCHAR, max_length=512)
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
        schema.add_field(field_name="created_at", datatype=DataType.VARCHAR, max_length=32)
        
        # 创建集合
        self.client.create_collection(
            collection_name=COLLECTION_NAME,
            schema=schema,
        )
        
        # 创建索引（IVF_FLAT，适合小规模数据）
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 128}
        )
        
        self.client.create_index(
            collection_name=COLLECTION_NAME,
            index_params=index_params,
        )
        
        print(f"[VectorService] 集合 {COLLECTION_NAME} 创建成功")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量表示
        """
        global _MODEL_READY
        
        # 惰性加载模型
        if not _MODEL_READY:
            _load_model()
        
        if not _MODEL_READY or MODEL is None:
            # 模型未加载时返回零向量（降级处理）
            print("[VectorService] 警告: 模型未加载，返回零向量")
            return [0.0] * EMBEDDING_DIM
        
        # bge-m3 编码，启用归一化
        embedding = MODEL.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    
    def index_symptom(self, symptom_id: str, symptom_name: str, description: str = "") -> bool:
        """
        将单个症状索引到向量库
        """
        try:
            text = f"{symptom_name}。{description}".strip()
            vector = self.get_embedding(text)
            
            data = [{
                "symptom_id": symptom_id,
                "symptom_name": symptom_name,
                "description": description,
                "vector": vector,
                "created_at": datetime.now().isoformat()
            }]
            
            self.client.insert(
                collection_name=COLLECTION_NAME,
                data=data
            )
            
            return True
            
        except Exception as e:
            print(f"[VectorService] 索引症状失败 {symptom_id}: {e}")
            return False
    
    def batch_index_symptoms(self, symptoms: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        批量索引症状（初始化时使用）
        symptoms: [{"symptom_id": "xxx", "symptom_name": "xxx", "description": "xxx"}, ...]
        """
        try:
            data = []
            for symptom in symptoms:
                text = f"{symptom['symptom_name']}。{symptom.get('description', '')}".strip()
                vector = self.get_embedding(text)
                
                data.append({
                    "symptom_id": symptom["symptom_id"],
                    "symptom_name": symptom["symptom_name"],
                    "description": symptom.get("description", ""),
                    "vector": vector,
                    "created_at": datetime.now().isoformat()
                })
            
            self.client.insert(
                collection_name=COLLECTION_NAME,
                data=data
            )
            
            # 刷新索引
            self.client.flush(collection_name=COLLECTION_NAME)
            
            return {
                "success": True,
                "count": len(data),
                "message": f"成功索引 {len(data)} 条症状"
            }
            
        except Exception as e:
            print(f"[VectorService] 批量索引失败: {e}")
            return {
                "success": False,
                "count": 0,
                "message": str(e)
            }
    
    def search(self, query: str, top_k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        向量检索：根据用户输入匹配最相似的症状
        
        Args:
            query: 用户输入的查询文本
            top_k: 返回结果数量
            threshold: 相似度阈值，低于此值的结果过滤掉
        
        Returns:
            [{"symptom_id": "xxx", "symptom_name": "xxx", "similarity": 0.92}, ...]
        """
        try:
            query_vector = self.get_embedding(query)
            
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                data=[query_vector],
                limit=top_k,
                output_fields=["symptom_id", "symptom_name", "description"],
                search_params={"metric_type": "COSINE", "params": {"nprobe": 10}}
            )
            
            # 解析结果
            matches = []
            for result in results[0]:  # results[0] 是第一条查询的结果
                similarity = result.get("distance", 0)
                
                # 过滤低相似度结果
                if similarity < threshold:
                    continue
                    
                matches.append({
                    "symptom_id": result["entity"]["symptom_id"],
                    "symptom_name": result["entity"]["symptom_name"],
                    "description": result["entity"].get("description", ""),
                    "similarity": round(float(similarity), 4)
                })
            
            # 按相似度降序排序
            matches.sort(key=lambda x: x["similarity"], reverse=True)
            return matches
            
        except Exception as e:
            print(f"[VectorService] 检索失败: {e}")
            return []
    
    def get_similar_symptoms(self, symptom_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        获取与指定症状相似的其他症状（用于"您可能还想了解"）
        """
        try:
            # 先获取该症状的向量
            results = self.client.query(
                collection_name=COLLECTION_NAME,
                filter=f'symptom_id == "{symptom_id}"',
                output_fields=["vector", "symptom_name"],
                limit=1
            )
            
            if not results:
                return []
            
            symptom_vector = results[0]["vector"]
            symptom_name = results[0]["symptom_name"]
            
            # 用该症状的向量搜索相似症状（排除自己）
            similar = self.client.search(
                collection_name=COLLECTION_NAME,
                data=[symptom_vector],
                limit=top_k + 1,  # +1 因为会包含自己
                output_fields=["symptom_id", "symptom_name", "description"],
                search_params={"metric_type": "COSINE", "params": {"nprobe": 10}}
            )
            
            matches = []
            for result in similar[0]:
                if result["entity"]["symptom_id"] == symptom_id:
                    continue  # 排除自己
                
                matches.append({
                    "symptom_id": result["entity"]["symptom_id"],
                    "symptom_name": result["entity"]["symptom_name"],
                    "description": result["entity"].get("description", ""),
                    "similarity": round(float(result.get("distance", 0)), 4)
                })
                
                if len(matches) >= top_k:
                    break
            
            return matches
            
        except Exception as e:
            print(f"[VectorService] 获取相似症状失败: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取向量库统计信息"""
        try:
            stats = self.client.get_collection_stats(COLLECTION_NAME)
            return {
                "total_vectors": stats.get("row_count", 0),
                "collection_name": COLLECTION_NAME,
                "embedding_dim": EMBEDDING_DIM,
                "model_ready": _MODEL_READY,
                "db_path": MILVUS_DB_PATH
            }
        except Exception as e:
            return {
                "error": str(e),
                "model_ready": _MODEL_READY
            }
    
    def clear_all(self) -> bool:
        """清空所有向量数据（谨慎使用）"""
        try:
            self.client.drop_collection(COLLECTION_NAME)
            self._create_collection()
            return True
        except Exception as e:
            print(f"[VectorService] 清空失败: {e}")
            return False


# 全局单例
_vector_service: Optional[VectorService] = None

def get_vector_service() -> VectorService:
    """获取 VectorService 单例"""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
