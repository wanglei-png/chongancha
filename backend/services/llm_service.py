import os
import re
import time
import requests
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from models.llm_log import LLMLog

# LLM API 配置（兼容 OpenAI 格式，支持 DeepSeek/通义千问等）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# 自动补全 chat completions 路径
if not LLM_API_BASE.endswith("/chat/completions"):
    LLM_API_URL = f"{LLM_API_BASE.rstrip('/')}/chat/completions"
else:
    LLM_API_URL = LLM_API_BASE

# 敏感词过滤列表（合规防火墙）
SENSITIVE_WORDS = [
    "诊断", "确诊", "治疗", "药方", "处方", "用药方案", "治愈率", "预后",
    "诊断结果", "疾病名称", "开药", "打针", "手术建议"
]

def check_sensitive_words(text: str) -> tuple[bool, Optional[str]]:
    """
    检查文本是否包含敏感词
    返回: (是否安全, 触发的敏感词)
    """
    for word in SENSITIVE_WORDS:
        if word in text:
            return False, word
    return True, None

def generate_summary(
    pet_info: Dict[str, Any],
    symptom_data: Dict[str, Any],
    actions_taken: str,
    db: Session,
    user_id: Optional[int] = None,
    query_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    调用 LLM 生成病情摘要
    返回: {"summary": str, "is_llm": bool, "is_filtered": bool, "cost": float, "latency": int}
    """
    
    # 构建 Prompt（硬约束）
    prompt = f"""【角色设定】
你是一个宠物健康信息整理助手，不是兽医，不提供诊断和治疗建议。
你只能基于下方【知识库片段】整理信息，禁止自由发挥医学知识。

【知识库片段】
症状：{symptom_data.get('symptom_name', '未知症状')}
居家观察：{symptom_data.get('home_observation', [])}
禁止行为：{symptom_data.get('absolute_prohibitions', [])}
就医条件：{symptom_data.get('red_flags', [])}

【宠物信息】
名称：{pet_info.get('name', '宠物')}
品种：{pet_info.get('breed', '未知')}
年龄：{pet_info.get('age_type', '未知')}
体重：{pet_info.get('weight', '未知')} {pet_info.get('weight_unit', 'kg')}
已采取措施：{actions_taken}

【任务】
请用温暖、专业的口吻，生成一段200字左右的病情摘要。
摘要应包含：宠物基本信息、症状描述、已采取措施、当前状态评估。
不要给出诊断结论，不要建议具体药物，不要预测疾病。
结尾必须包含："以上信息仅供参考，不能替代专业兽医诊断。"

【输出格式】
直接输出摘要文本，不要加任何标题或标记。
"""

    start_time = time.time()
    cost = 0.0
    response_text = ""
    is_filtered = False
    filter_reason = None
    
    try:
        # 调用 LLM API（兼容 OpenAI 格式）
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,  # 低温度，减少幻觉
            "max_tokens": 500,
            "stream": False
        }
        
        resp = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        
        result = resp.json()
        response_text = result["choices"][0]["message"]["content"]
        
        # 计算成本（根据模型不同调整）
        prompt_tokens = result["usage"]["prompt_tokens"]
        completion_tokens = result["usage"]["completion_tokens"]
        
        # 成本估算（元）
        if "deepseek" in LLM_MODEL.lower():
            # DeepSeek: 输入0.001元/1K, 输出0.002元/1K
            cost = (prompt_tokens * 0.001 + completion_tokens * 0.002) / 1000
        else:
            # 其他模型按通用估算
            cost = (prompt_tokens + completion_tokens) * 0.003 / 1000
        
        # 敏感词过滤（合规防火墙）
        is_safe, hit_word = check_sensitive_words(response_text)
        if not is_safe:
            is_filtered = True
            filter_reason = f"触发敏感词: {hit_word}"
            # 降级为模板生成
            response_text = _fallback_template(pet_info, symptom_data, actions_taken)
        
    except Exception as e:
        # API 调用失败，降级为模板
        response_text = _fallback_template(pet_info, symptom_data, actions_taken)
        filter_reason = f"API调用失败: {str(e)}"
    
    latency = int((time.time() - start_time) * 1000)
    
    # 记录审计日志
    log = LLMLog(
        user_id=user_id,
        query_id=query_id,
        model_name=LLM_MODEL,
        prompt=prompt,
        response=response_text,
        is_filtered=is_filtered,
        filter_reason=filter_reason,
        latency_ms=latency,
        cost_cny=round(cost, 6),
    )
    db.add(log)
    db.commit()
    
    return {
        "summary": response_text,
        "is_llm": not is_filtered and cost > 0,
        "is_filtered": is_filtered,
        "cost": round(cost, 6),
        "latency": latency
    }

def _fallback_template(pet_info: Dict, symptom_data: Dict, actions_taken: str) -> str:
    """模板降级生成（V1.x 的原有逻辑）"""
    name = pet_info.get("name", "宠物")
    breed = pet_info.get("breed", "")
    age = pet_info.get("age_type", "")
    weight = pet_info.get("weight", "")
    unit = pet_info.get("weight_unit", "kg")
    symptom = symptom_data.get("symptom_name", "出现不适")
    
    return f"{name}，{breed}，{age}，体重{weight}{unit}。宠物出现{symptom}症状，主人已采取以下措施：{actions_taken}。建议持续观察宠物精神状态、食欲和排泄情况，如出现就医触发条件中的任何一项，请立即前往正规动物医院就诊。以上信息仅供参考，不能替代专业兽医诊断。"
