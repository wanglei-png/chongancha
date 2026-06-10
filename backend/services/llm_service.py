"""大模型 API 调用服务"""

from typing import Any, Dict, List

import httpx

from config import settings


class LLMService:
    """大模型 API 调用封装"""

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.api_base = settings.LLM_API_BASE
        self.model = settings.LLM_MODEL

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """调用大模型对话接口"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def generate_summary(
        self,
        symptom_name: str,
        pet_info: Dict[str, Any],
        decision_list: Dict[str, Any],
    ) -> str:
        """生成病情摘要"""
        system_prompt = """你是一位专业的宠物医生助手。请根据以下信息生成一份简洁、清晰的病情摘要，
内容包括：症状描述、宠物基本信息、家庭观察建议、需要警惕的危险信号，以及就医建议。
请使用通俗易懂的语言，让宠物主人能够理解并采取适当行动。"""

        user_prompt = f"""
【症状名称】{symptom_name}
【宠物信息】品种：{pet_info.get('breed', '未知')}，年龄阶段：{pet_info.get('age_type', '未知')}，体重：{pet_info.get('weight', '未知')}
【家庭观察建议】{decision_list.get('home_observation', [])}
【危险信号】{decision_list.get('red_flags', [])}
【绝对禁止事项】{decision_list.get('absolute_prohibitions', [])}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = await self.chat(messages)
        return result["choices"][0]["message"]["content"]
