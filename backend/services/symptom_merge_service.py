from typing import List, Dict, Any

def merge_symptoms(symptoms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    合并多个症状的决策清单
    规则：
    1. 居家观察：取并集，相同建议去重
    2. 禁止行为：取并集，相同行为去重
    3. 就医条件：取并集，按 priority 排序（emergency > urgent > warning）
    4. 冲突建议：以严重级别高的为准
    """
    if not symptoms:
        return {}
    
    if len(symptoms) == 1:
        return symptoms[0]
    
    merged = {
        "symptom_name": " + ".join([s.get("symptom_name", "") for s in symptoms]),
        "home_observation": [],
        "absolute_prohibitions": [],
        "red_flags": []
    }
    
    # 合并居家观察（去重）
    seen_obs = set()
    for s in symptoms:
        for obs in s.get("home_observation", []):
            key = obs.get("action", "")
            if key and key not in seen_obs:
                seen_obs.add(key)
                merged["home_observation"].append(obs)
    
    # 合并禁止行为（去重）
    seen_proh = set()
    for s in symptoms:
        for proh in s.get("absolute_prohibitions", []):
            key = proh.get("action", "")
            if key and key not in seen_proh:
                seen_proh.add(key)
                merged["absolute_prohibitions"].append(proh)
    
    # 合并就医条件（去重 + 按优先级排序）
    priority_order = {"emergency": 0, "urgent": 1, "warning": 2}
    seen_flags = set()
    all_flags = []
    for s in symptoms:
        for flag in s.get("red_flags", []):
            key = flag.get("condition", "")
            if key and key not in seen_flags:
                seen_flags.add(key)
                all_flags.append(flag)
    
    # 按优先级排序
    merged["red_flags"] = sorted(
        all_flags,
        key=lambda x: priority_order.get(x.get("priority", "warning"), 99)
    )
    
    return merged
