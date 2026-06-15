import os
import requests
from typing import Dict, Any

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

if not LLM_API_BASE.endswith("/chat/completions"):
    LLM_API_URL = f"{LLM_API_BASE.rstrip('/')}/chat/completions"
else:
    LLM_API_URL = LLM_API_BASE

def generate_xiaohongshu_content(symptom_name: str, pet_type: str = "猫") -> Dict[str, str]:
    """
    生成小红书文案
    """
    prompt = f"""你是一个资深宠物领域小红书博主，擅长写爆款笔记。
请为以下症状写一篇小红书文案：

症状：{pet_type}{symptom_name}
目标受众：新手养{pet_type}主人
风格：亲切、实用、略带焦虑感（但提供解决方案）

要求：
1. 标题要吸引人，带emoji，不超过20字
2. 正文分3-4段，每段不超过3行
3. 包含具体场景（如"凌晨2点"）
4. 结尾引导使用"宠急查"工具
5. 添加5-8个相关话题标签
6. 不要出现"诊断""治疗"等医疗词汇

输出格式：
标题：[标题]
正文：[正文]
标签：[标签]
"""

    try:
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 800
        }
        
        resp = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        
        content = resp.json()["choices"][0]["message"]["content"]
        
        # 解析输出
        lines = content.split("\n")
        title = ""
        body = ""
        tags = ""
        
        for line in lines:
            if line.startswith("标题："):
                title = line.replace("标题：", "").strip()
            elif line.startswith("正文："):
                body = line.replace("正文：", "").strip()
            elif line.startswith("标签："):
                tags = line.replace("标签：", "").strip()
        
        return {
            "title": title,
            "body": body,
            "tags": tags,
            "platform": "xiaohongshu",
            "raw": content
        }
        
    except Exception as e:
        return {
            "title": f"{pet_type}{symptom_name}怎么办？",
            "body": f"我家{pet_type}最近{symptom_name}，查了很多资料还是不确定该怎么办。后来用了宠急查，1分钟理清思路。",
            "tags": "#养宠日常 #宠物健康",
            "platform": "xiaohongshu",
            "raw": str(e)
        }

def generate_douyin_script(symptom_name: str, pet_type: str = "猫") -> Dict[str, str]:
    """
    生成抖音视频脚本
    """
    prompt = f"""你是一个资深宠物领域短视频编导，擅长写抖音爆款脚本。
请为以下症状写一个30秒的抖音视频脚本：

症状：{pet_type}{symptom_name}
目标受众：新手养{pet_type}主人
风格：快节奏、有悬念、提供实用价值

要求：
1. 开头3秒必须有钩子（制造焦虑或好奇）
2. 中间15秒讲清楚核心信息
3. 结尾5秒引导使用"宠急查"工具
4. 标注画面描述和口播文案
5. 不要出现"诊断""治疗"等医疗词汇

输出格式：
标题：[视频标题]
钩子：[前3秒画面+口播]
正文：[中间画面+口播]
结尾：[结尾画面+口播]
"""

    try:
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 600
        }
        
        resp = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        
        content = resp.json()["choices"][0]["message"]["content"]
        
        return {
            "title": f"{pet_type}{symptom_name}怎么办？",
            "script": content,
            "platform": "douyin",
            "raw": content
        }
        
    except Exception as e:
        return {
            "title": f"{pet_type}{symptom_name}怎么办？",
            "script": f"【钩子】凌晨2点，我家{pet_type}突然{symptom_name}...\n【正文】我当时慌了，不知道该怎么办。后来用了宠急查，1分钟得到决策清单。\n【结尾】养宠不焦虑，搜索宠急查。",
            "platform": "douyin",
            "raw": str(e)
        }
