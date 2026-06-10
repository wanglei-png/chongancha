"""症状知识库种子数据（35条）
更完整的家庭观察/禁止行为/危险信号模板版本
"""
from datetime import date

CAT, DOG, DERM, EYE, ORAL = "《猫病学》", "《犬病学》", "《小动物皮肤病学》", "《小动物眼科学》", "《小动物口腔医学》"
EMER, NUTR, VET, DRUG, GUIDE = "《小动物临床急诊医学》", "《小动物营养学》", "兽医临床指南", "兽药基础数据库", "中国兽医协会科普指南"

def _normalize_red_flags(items):
    """补齐 red_flags 的 source/priority 字段，避免前端缺少来源标签。"""
    normalized = []
    for item in items or []:
        if isinstance(item, dict):
            entry = dict(item)
            entry.setdefault("source", "兽医临床指南")
            entry.setdefault("priority", "urgent")
            normalized.append(entry)
        else:
            normalized.append(item)
    return normalized


def s(sid, name, pets, home_obs, pros, reds, template):
    return {
        "symptom_id": sid, "symptom_name": name, "applicable_pets": pets,
        "home_observation": home_obs, "absolute_prohibitions": pros,
        "red_flags": _normalize_red_flags(reds), "vet_summary_template": template,
        "last_reviewed": date(2026, 6, 5), "reviewer_vet": "待审核",
    }

def a(text, source, conf):
    return {"action": text, "source": source, "confidence": conf}

def p(text, source, sev):
    return {"action": text, "source": source, "severity": sev}

def r(cond, action, pri, source="兽医临床指南"):
    return {"condition": cond, "action": action, "priority": pri, "source": source}

T = "{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。"
T2 = "{pet_name}，{breed}，{age}。从{time}开始{symptom_name}，已持续{duration}。伴随症状{other_symptoms}。已尝试{actions}。"

SYMPTOM_SEEDS = []

SYMPTOM_SEEDS.append(s("vomiting_cat", "猫咪呕吐", ['cat'], [{'action': '记录呕吐次数、颜色、是否带血或泡沫，并拍照留存', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '暂时禁食4-6小时，期间只提供少量清水并观察是否继续呕吐', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '检查是否误食异物、换粮、吃到有毒植物或人类食物', 'source': '兽医临床指南', 'confidence': 'high'}, {'action': '保持环境安静，减少应激，避免剧烈运动', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止自行服用布洛芬、阿司匹林或人用止吐药，对猫可能致死', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要强行灌食或灌水，避免误吸引发肺炎', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要用大蒜、洋葱、酒精等偏方处理', 'source': '中国兽医协会科普指南', 'severity': 'fatal'}, {'action': '不要给猫喂牛奶或乳制品来安抚胃部', 'source': '《猫病学》', 'severity': 'high'}], [{'condition': '24小时内呕吐超过3次或呕吐物带血/咖啡渣样', 'action': '建议立即就医', 'priority': 'emergency'}, {'condition': '伴随精神萎靡、嗜睡、拒绝饮水超过12小时', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '腹部明显胀气或疼痛、出现抗拒触腹', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '幼猫/老年猫出现呕吐或怀疑误食异物', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("vomiting_dog", "狗狗呕吐", ['dog'], [{'action': '记录呕吐次数、颜色、是否伴随泡沫、异物或血液', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '暂时禁食12-24小时，期间提供少量清水并观察是否继续呕吐', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '检查是否误食袜子、玩具、骨头、植物或腐败食物', 'source': '兽医临床指南', 'confidence': 'high'}, {'action': '恢复饮食后喂少量清淡易消化食物', 'source': '《小动物营养学》', 'confidence': 'high'}], [{'action': '禁止自行给犬服用布洛芬、对乙酰氨基酚或人用止吐药', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要强行灌水或喂食，避免误吸', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要用大蒜、洋葱、酒精、巧克力等偏方或有毒食物处理', 'source': '中国兽医协会科普指南', 'severity': 'fatal'}, {'action': '不要让犬继续剧烈运动或大量饮水', 'source': '兽医临床指南', 'severity': 'high'}], [{'condition': '24小时内呕吐超过4次或呕吐物为鲜红/咖啡渣样', 'action': '建议立即就医', 'priority': 'emergency'}, {'condition': '伴随精神萎靡、嗜睡、拒绝饮水超过12小时', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '腹部明显胀气、疼痛或可能胃扭转', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '幼犬/老年犬出现呕吐或有误食异物史', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("diarrhea_cat", "猫咪腹泻", ['cat'], [{'action': '记录腹泻次数、便便颜色、是否带血或黏液，并拍照留存', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '暂时禁食6-8小时，提供充足清洁饮水', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '检查是否换粮、喂人类食物、喂生肉或有寄生虫迹象', 'source': '兽医临床指南', 'confidence': 'high'}, {'action': '恢复后给少量易消化食物，并观察是否恶化', 'source': '《小动物营养学》', 'confidence': 'high'}], [{'action': '禁止自行给猫用止泻药、抗生素或人用胃药', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要喂牛奶、乳制品或油腻人食', 'source': '《猫病学》', 'severity': 'high'}, {'action': '不要使用大蒜、洋葱等偏方', 'source': '中国兽医协会科普指南', 'severity': 'fatal'}, {'action': '不要忽视高频腹泻或持续超过48小时', 'source': '兽医临床指南', 'severity': 'high'}], [{'condition': '腹泻带血、柏油样便、或严重水样便', 'action': '建议立即就医', 'priority': 'emergency'}, {'condition': '伴随呕吐、食欲废绝、精神萎靡或脱水', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '幼猫/老年猫出现腹泻或持续超过48小时', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '腹部明显疼痛、胀气或排便困难', 'action': '需立即送医', 'priority': 'emergency'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("diarrhea_dog", "狗狗腹泻", ['dog'], [{'action': '记录腹泻次数、形状、是否带血、黏液或异物', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '暂时禁食12-24小时并提供清洁饮水', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '检查是否捡食路边食品、换粮、误食有毒食物', 'source': '兽医临床指南', 'confidence': 'high'}, {'action': '恢复饮食时喂清淡食物并观察脱水程度', 'source': '《小动物营养学》', 'confidence': 'high'}], [{'action': '禁止自行给犬服用人用止泻药或抗生素', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要喂巧克力、葡萄、洋葱、木糖醇等有毒食物', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要喂高脂肪油炸食物或生肉', 'source': '《小动物营养学》', 'severity': 'medium'}, {'action': '不要忽视持续超过48小时或伴随呕吐', 'source': '兽医临床指南', 'severity': 'high'}], [{'condition': '腹泻带血、严重水样便或频繁超过5次/24h', 'action': '建议立即就医', 'priority': 'emergency'}, {'condition': '伴随呕吐、精神萎靡、拒绝饮水或明显脱水', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '幼犬/老年犬出现腹泻或怀疑中毒', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '腹部疼痛、胀气或停止排便', 'action': '需立即送医', 'priority': 'emergency'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("skin_cat", "猫咪皮肤瘙痒红斑", ['cat'], [{'action': '拍照记录红斑、丘疹、结痂、脱毛或溃烂位置与范围', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '使用跳蚤梳检查背部、尾部和颈部是否有跳蚤或螨虫', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '观察瘙痒程度是否影响进食、睡眠或抓挠行为', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '检查是否近期更换猫粮、猫砂、洗涤用品或环境', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止用人用皮炎平、达克宁或含菊酯驱虫产品处理猫皮肤', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要随意口服抗过敏药或给猫洗澡过于频繁', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要用酒精、碘伏或偏方涂抹大面积破损皮肤', 'source': '兽医临床指南', 'severity': 'high'}, {'action': '不要让猫继续抓挠加重皮肤损伤', 'source': '《小动物皮肤病学》', 'severity': 'medium'}], [{'condition': '皮肤出现大面积溃烂、渗液、化脓或恶臭', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随食欲下降、精神萎靡或发热', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '出现圆形脱毛、边界清晰或面部肿胀', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '瘙痒导致自残或24小时内迅速扩散', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("skin_dog", "狗狗皮肤瘙痒红斑", ['dog'], [{'action': '拍照记录病变范围、红斑、硬结、脱毛或渗液', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '检查耳部、腹部、尾部和四肢是否有跳蚤、蜱虫或螨虫', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '观察是否因抓挠造成皮肤破损或感染', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '检查是否更换狗粮、洗护用品或环境刺激源', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止用人用皮肤药膏或猫用驱虫产品处理', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要随意口服抗过敏药或频繁洗澡', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要用酒精、双氧水或偏方直接处理破损皮肤', 'source': '兽医临床指南', 'severity': 'high'}, {'action': '不要让犬继续抓挠、舔舐加重炎症', 'source': '《小动物皮肤病学》', 'severity': 'medium'}], [{'condition': '皮肤出现大面积渗液、化脓或恶臭', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随食欲下降、精神萎靡或发热', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '出现圆形脱毛、耳部异味或面部肿胀', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '瘙痒导致自残或短期内快速扩散', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("eye_cat", "猫咪眼睛红肿流泪", ['cat'], [{'action': '观察是否红肿、流泪、分泌物、畏光或频繁眨眼', 'source': '《小动物眼科学》', 'confidence': 'high'}, {'action': '用干净棉球轻轻擦拭分泌物，每只眼用不同棉球', 'source': '《小动物眼科学》', 'confidence': 'high'}, {'action': '检查是否有灰尘、毛发、植物芒刺或刺激性气味', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '留意是否伴随打喷嚏、流鼻涕或精神萎靡', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止使用人用眼药水、类固醇眼药水或抗生素滴眼液', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要强行掰眼睛、冲洗或用茶水、盐水等自制液体', 'source': '《小动物眼科学》', 'severity': 'high'}, {'action': '不要给猫口服人用抗炎药或抗生素', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要让猫继续抓挠眼睛', 'source': '兽医临床指南', 'severity': 'high'}], [{'condition': '眼睛明显肿胀、无法睁开或角膜浑浊', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '出现脓性分泌物、带血分泌物或眼球表面溃疡', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随打喷嚏、流鼻涕、精神萎靡、食欲下降', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '第三眼睑明显突出或眼部症状持续超过24小时', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("eye_dog", "狗狗眼睛红肿流泪", ['dog'], [{'action': '观察是否红肿、流泪、分泌物、畏光或频繁眨眼', 'source': '《小动物眼科学》', 'confidence': 'high'}, {'action': '用干净棉球擦拭眼部分泌物，每只眼使用不同棉球', 'source': '《小动物眼科学》', 'confidence': 'high'}, {'action': '检查眼周毛发是否刺激眼球或有异物进入', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '留意是否伴随打喷嚏、流鼻涕或呼吸道症状', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止使用人用眼药水、类固醇眼药水或随意口服抗生素', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要强行掰眼睛、冲洗或用茶水、盐水等自制液体', 'source': '《小动物眼科学》', 'severity': 'high'}, {'action': '不要让犬继续抓挠眼睛加重损伤', 'source': '兽医临床指南', 'severity': 'high'}, {'action': '不要忽视短鼻犬种眼球突出和眼部异常', 'source': '《小动物眼科学》', 'severity': 'medium'}], [{'condition': '眼睛明显肿胀、无法睁开或角膜浑浊', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '出现脓性分泌物、眼球突出或眼压异常', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '症状持续超过24小时、加重或伴随眼球划伤', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '短鼻犬种出现眼部症状尤其要尽早处理', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("appetite_cat", "猫咪突然不吃东西", ['cat'], [{'action': '记录不吃食物的时长、是否完全拒食或只吃少量', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '检查猫粮是否变质、换了口味或有应激源', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '观察是否伴随呕吐、腹泻、体重下降、抓嘴或流涎', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '检查口腔是否有异味、牙龈红肿、口腔溃疡或牙齿问题', 'source': '《小动物口腔医学》', 'confidence': 'high'}], [{'action': '禁止强行灌食或用人用消食药、食欲刺激剂处理', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要超过24小时不进食不就医，猫可能发生脂肪肝', 'source': '《猫病学》', 'severity': 'fatal'}, {'action': '不要用牛奶或乳制品来诱食', 'source': '《猫病学》', 'severity': 'medium'}, {'action': '不要自行使用抗生素或偏方', 'source': '中国兽医协会科普指南', 'severity': 'high'}], [{'condition': '完全不吃不喝超过24小时，或伴随精神萎靡', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '伴随呕吐、腹泻、体重明显下降或黄疸', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '口腔有明显异味、流涎、牙龈红肿或口腔溃疡', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '幼猫超过12小时不进食', 'action': '建议立即就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。从{time}开始{symptom_name}，已持续{duration}。伴随症状{other_symptoms}。已尝试{actions}。'))

SYMPTOM_SEEDS.append(s("appetite_dog", "狗狗突然不吃东西", ['dog'], [{'action': '记录不吃食物的时长、是否完全拒食或只吃少量', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '检查狗粮是否变质、换了口味或有应激源', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '观察是否伴随呕吐、腹泻、体重下降、口臭或流涎', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '检查口腔是否有牙龈红肿、牙结石或口腔溃疡', 'source': '《小动物口腔医学》', 'confidence': 'high'}], [{'action': '禁止强行灌食或用人用消食药、食欲刺激剂处理', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要超过48小时不进食不就医', 'source': '《犬病学》', 'severity': 'high'}, {'action': '不要喂巧克力、葡萄、洋葱等有毒食物来诱食', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要自行使用抗生素或偏方', 'source': '中国兽医协会科普指南', 'severity': 'high'}], [{'condition': '完全不吃不喝超过48小时', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '伴随呕吐、腹泻、精神萎靡、体温异常', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '口腔有明显异味、牙龈严重红肿或口腔溃疡', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '幼犬超过24小时不进食', 'action': '建议立即就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。从{time}开始{symptom_name}，已持续{duration}。伴随症状{other_symptoms}。已尝试{actions}。'))

SYMPTOM_SEEDS.append(s("constipation_cat", "猫咪便秘", ['cat'], [{'action': '记录上次排便时间、排便频率及是否用力努责', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '检查是否有干硬粪便、便球或排便时惨叫', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '增加水分摄入并观察是否因毛球导致便秘', 'source': '《小动物营养学》', 'confidence': 'high'}, {'action': '观察是否伴随腹胀、食欲下降或精神状态变化', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止使用人用开塞露、灌肠剂或泻药处理', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要强行从肛门掏粪，可能导致损伤或穿孔', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要用牛奶来通便', 'source': '《猫病学》', 'severity': 'medium'}, {'action': '不要忽视超过72小时未排便', 'source': '《猫病学》', 'severity': 'high'}], [{'condition': '超过72小时未排便或完全停止排便', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '频繁进出猫砂盆、痛苦嚎叫或腹部坚硬', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随呕吐、食欲废绝或精神萎靡', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '幼猫/老年猫出现便秘风险更高', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。从{time}开始{symptom_name}，已持续{duration}。伴随症状{other_symptoms}。已尝试{actions}。'))

SYMPTOM_SEEDS.append(s("constipation_dog", "狗狗便秘", ['dog'], [{'action': '记录上次排便时间、是否频繁做排便姿势', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '检查是否有干硬粪便、带血便或腹部胀气', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '增加水分摄入、运动和易消化饮食', 'source': '《小动物营养学》', 'confidence': 'high'}, {'action': '检查是否误食石头、玩具、布料等异物', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止自行用人用泻药、开塞露或灌肠剂', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要强行掏取粪便，可能造成直肠损伤', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要喂大量油脂或辛辣食物通便', 'source': '兽医临床指南', 'severity': 'medium'}, {'action': '不要忽视超过72小时未排便', 'source': '《犬病学》', 'severity': 'high'}], [{'condition': '超过72小时未排便或完全停止排便', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '多次做排便姿势但排不出、痛苦嚎叫', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随呕吐、腹部胀大或明显疼痛', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '怀疑误食异物或幼犬/老年犬便秘', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。从{time}开始{symptom_name}，已持续{duration}。伴随症状{other_symptoms}。已尝试{actions}。'))

SYMPTOM_SEEDS.append(s("pica_cat", "猫咪异食癖", ['cat'], [{'action': '记录吞食的异物类型（塑料袋、纸箱、墙皮、毛线等）', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '检查家中是否有易吞食物品、线绳、橡皮筋、小玩具', 'source': '兽医临床指南', 'confidence': 'high'}, {'action': '评估饮食是否均衡、是否缺乏某些微量元素', 'source': '《小动物营养学》', 'confidence': 'medium'}, {'action': '观察是否伴随食欲变化、体重下降、呕吐或腹泻', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止打骂惩罚或把猫关在狭小空间作为惩罚', 'source': '中国兽医协会科普指南', 'severity': 'high'}, {'action': '不要忽视吞食线绳、塑料袋等异物', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要自行补充微量元素或用偏方处理', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要让猫继续接触危险物品', 'source': '兽医临床指南', 'severity': 'high'}], [{'condition': '已吞食明显异物、怀疑肠梗阻或排便困难', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '伴随呕吐、食欲废绝、精神萎靡或腹痛', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '异食行为突然出现且频繁，或伴随体重下降', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '幼猫/老年猫出现异常采食行为', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("pica_dog", "狗狗异食癖", ['dog'], [{'action': '记录吞食的异物类型（石头、泥土、布料、塑料袋、袜子等）', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '检查家中是否有易吞食物品、电线、袜子、玩具', 'source': '兽医临床指南', 'confidence': 'high'}, {'action': '评估饮食是否均衡，并增加运动和游戏时间', 'source': '《小动物营养学》', 'confidence': 'medium'}, {'action': '观察是否伴随食欲变化、体重下降、呕吐或腹泻', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止打骂惩罚或通过隔离来惩罚异食行为', 'source': '中国兽医协会科普指南', 'severity': 'high'}, {'action': '不要忽视吞食异物，可能导致肠梗阻或穿孔', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要让犬啃骨头、塑料或布料来磨牙', 'source': '兽医临床指南', 'severity': 'high'}, {'action': '不要自行补充微量元素或高剂量营养品', 'source': '兽药基础数据库', 'severity': 'high'}], [{'condition': '已吞食明显异物或怀疑肠梗阻', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '伴随呕吐、食欲废绝、腹痛或排便困难', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '异食行为突然增加且伴随体重下降', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '幼犬/老年犬出现异常采食行为', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("bad_breath_cat", "猫咪口臭", ['cat'], [{'action': '检查口腔是否有牙龈红肿、牙结石、牙齿松动或口腔溃疡', 'source': '《小动物口腔医学》', 'confidence': 'high'}, {'action': '闻气味类型，区分酸臭味、烂苹果味或氨味', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '观察是否伴随流涎、进食困难、抓嘴或体重下降', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '检查是否有口腔异物、鱼刺、线绳或牙齿问题', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止使用人用漱口水、喷雾或氟牙膏处理猫口腔', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要强行掰开猫嘴检查', 'source': '兽医临床指南', 'severity': 'medium'}, {'action': '不要忽视长期口臭可能提示全身性疾病', 'source': '《猫病学》', 'severity': 'high'}, {'action': '不要自行给猫口服人用消炎药或抗菌药', 'source': '兽药基础数据库', 'severity': 'high'}], [{'condition': '口臭伴随流涎、进食困难、明显口腔疼痛', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '口臭呈烂苹果味且伴随多饮多尿或体重下降', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '口臭呈氨味/尿味且伴随精神萎靡、食欲下降', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '牙龈严重红肿、出血或有明显溃疡', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("bad_breath_dog", "狗狗口臭", ['dog'], [{'action': '检查口腔是否有牙龈红肿、牙结石、牙齿松动或口腔溃疡', 'source': '《小动物口腔医学》', 'confidence': 'high'}, {'action': '闻气味类型，区分酸臭味、烂苹果味或氨味', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '观察是否伴随流涎、进食困难、抓嘴或体重下降', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '检查是否有骨头碎片、木棍、线绳等口腔异物', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '禁止使用人用漱口水、喷雾或含氟牙膏处理犬口腔', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要强行掰开狗嘴检查', 'source': '兽医临床指南', 'severity': 'medium'}, {'action': '不要忽视长期口臭可能提示肾衰竭或糖尿病', 'source': '《犬病学》', 'severity': 'high'}, {'action': '不要自行给犬口服人用消炎药或抗菌药', 'source': '兽药基础数据库', 'severity': 'high'}], [{'condition': '口臭伴随流涎、进食困难、明显口腔疼痛', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '口臭呈烂苹果味且伴随多饮多尿或体重下降', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '口臭呈氨味/尿味且伴随精神萎靡、食欲下降', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '牙龈严重红肿、出血或牙齿松动', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("drooling_cat", "猫咪流口水", ['cat'], [{'action': '观察是否伴随口腔异味、进食困难、抓嘴或牙龈红肿', 'source': '《小动物口腔医学》', 'confidence': 'high'}, {'action': '记录流口水的量、是否持续、是否伴随呕吐', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '检查是否误食有毒植物、口腔异物或牙齿疾病', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '保持口鼻周围清洁，防止刺激和感染', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要用人用口腔喷雾、漱口水处理猫', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要强行掰开猫嘴检查', 'source': '兽医临床指南', 'severity': 'medium'}, {'action': '不要自行使用止吐药或抗炎药', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要忽视持续流涎可能提示口腔疾病', 'source': '《小动物口腔医学》', 'severity': 'high'}], [{'condition': '流口水伴随食欲废绝、精神萎靡或呕吐', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '口腔有明显溃疡、牙龈红肿或异物', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '幼猫出现持续流涎或口腔疼痛', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '流涎伴随口臭、体重下降或发热', 'action': '建议立即就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("drooling_dog", "狗狗流口水", ['dog'], [{'action': '观察是否伴随口腔异味、进食困难、抓嘴或牙龈红肿', 'source': '《小动物口腔医学》', 'confidence': 'high'}, {'action': '记录流口水的量、是否持续及是否伴随呕吐', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '检查是否误食骨头碎片、木棍或口腔异物', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '保持口鼻周围清洁，防止刺激和感染', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要用人用口腔喷雾、漱口水处理犬', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要强行掰开狗嘴检查', 'source': '兽医临床指南', 'severity': 'medium'}, {'action': '不要自行使用止吐药或抗炎药', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要忽视持续流涎可能提示口腔疾病', 'source': '《小动物口腔医学》', 'severity': 'high'}], [{'condition': '流口水伴随食欲废绝、精神萎靡或呕吐', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '口腔有明显溃疡、牙龈红肿或异物', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '幼犬出现持续流涎或口腔疼痛', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '流涎伴随口臭、体重下降或发热', 'action': '建议立即就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("bloating_cat", "猫咪腹胀", ['cat'], [{'action': '观察腹部是否明显膨大、触诊是否坚硬', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '记录是否伴随呕吐、便秘、食欲下降或排便异常', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '检查是否进食过快、吞食毛球或异物', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '减少剧烈运动，避免加重腹部不适', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要按摩或按压腹部', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要在未诊断前喂食、喂水或用胃药', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要忽视腹部突然胀大', 'source': '《猫病学》', 'severity': 'high'}, {'action': '不要自行使用消化药或偏方', 'source': '兽药基础数据库', 'severity': 'high'}], [{'condition': '腹部迅速胀大、触诊坚硬或宠物明显疼痛', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '伴随呕吐、精神萎靡、食欲废绝或呼吸困难', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '超过48小时未排便或排便困难', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '幼猫或老年猫出现腹胀风险更高', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。从{time}开始{symptom_name}，已持续{duration}。伴随症状{other_symptoms}。已尝试{actions}。'))

SYMPTOM_SEEDS.append(s("bloating_dog", "狗狗腹胀", ['dog'], [{'action': '观察腹部是否明显膨大、触诊是否坚硬', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '记录是否伴随呕吐、便秘、食欲下降或排便异常', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '检查是否进食过快、饮水后剧烈运动或胃扩张史', 'source': '兽医临床指南', 'confidence': 'high'}, {'action': '减少剧烈运动，避免加重腹部不适', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要按摩或按压腹部', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要在未诊断前喂食、喂水或用胃药', 'source': '《小动物临床急诊医学》', 'severity': 'fatal'}, {'action': '不要忽视腹部突然胀大', 'source': '《犬病学》', 'severity': 'high'}, {'action': '不要自行使用消化药或偏方', 'source': '兽药基础数据库', 'severity': 'high'}], [{'condition': '腹部迅速胀大、触诊坚硬或宠物明显疼痛', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '伴随频繁呕吐、流涎、呼吸困难或站立不稳', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '大型深胸犬出现腹胀尤其危险', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随停止排便、食欲废绝或精神萎靡', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。从{time}开始{symptom_name}，已持续{duration}。伴随症状{other_symptoms}。已尝试{actions}。'))

SYMPTOM_SEEDS.append(s("itching_cat", "猫咪瘙痒/频繁抓挠", ['cat'], [{'action': '拍照记录瘙痒部位、是否有红斑、丘疹、结痂或脱毛', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '检查背部、尾部和颈部是否有跳蚤、螨虫或皮肤感染', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '观察是否影响睡眠、进食或出现自残行为', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '记录近期换粮、换猫砂、洗涤用品或环境变化', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要使用人用皮炎平、达克宁或狗用驱虫滴剂', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要随意口服抗过敏药', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要用酒精、碘伏或偏方处理破损皮肤', 'source': '兽医临床指南', 'severity': 'high'}, {'action': '不要让猫继续抓挠加重损伤', 'source': '《小动物皮肤病学》', 'severity': 'medium'}], [{'condition': '皮肤出现大面积溃烂、渗液、化脓或恶臭', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随精神萎靡、食欲下降或发热', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '瘙痒导致频繁抓挠、出血或自残', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '面部、耳周或口鼻周围出现肿胀', 'action': '需立即送医', 'priority': 'emergency'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("itching_dog", "狗狗瘙痒/频繁抓挠", ['dog'], [{'action': '拍照记录瘙痒部位、红斑、丘疹、结痂或脱毛', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '检查耳部、腹部、尾部和四肢是否有寄生虫', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '观察是否影响睡眠、进食或出现自残行为', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '检查是否更换狗粮、零食、洗涤用品或环境', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要用人用皮肤药膏或猫用驱虫产品', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要随意口服抗过敏药', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要用酒精、双氧水或偏方处理皮肤', 'source': '兽医临床指南', 'severity': 'high'}, {'action': '不要让狗继续抓挠、舔舐加重损伤', 'source': '《小动物皮肤病学》', 'severity': 'medium'}], [{'condition': '皮肤出现大面积溃烂、渗液、化脓或恶臭', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随精神萎靡、食欲下降或发热', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '瘙痒导致频繁抓挠、出血或自残', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '耳部感染伴随异味或头部倾斜', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("hair_loss_cat", "猫咪脱毛/斑秃", ['cat'], [{'action': '拍照记录脱毛范围、是否对称、是否伴随结痂或皮肤红斑', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '检查是否有跳蚤、螨虫、真菌感染或皮肤炎症', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '观察是否伴随食欲变化、体重下降或过度舔毛', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '检查饮食是否均衡，是否缺乏必需脂肪酸', 'source': '《小动物营养学》', 'confidence': 'medium'}], [{'action': '不要自行用抗真菌药、激素药或偏方处理', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要打骂惩罚或增加应激', 'source': '中国兽医协会科普指南', 'severity': 'high'}, {'action': '不要忽视脱毛迅速加重', 'source': '《小动物皮肤病学》', 'severity': 'medium'}, {'action': '不要让猫继续舔舐破损皮肤', 'source': '兽医临床指南', 'severity': 'medium'}], [{'condition': '脱毛区域迅速扩大、伴随渗液、化脓或明显疼痛', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随体重下降、食欲变化或多饮多尿', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '脱毛呈圆形边界清晰且可传染人', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '皮肤破损严重或出现自残', 'action': '建议立即就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("hair_loss_dog", "狗狗脱毛/斑秃", ['dog'], [{'action': '拍照记录脱毛范围、是否对称、是否伴随结痂或皮肤红斑', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '检查是否有跳蚤、螨虫、真菌感染或皮肤炎症', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '观察是否伴随食欲变化、体重下降或过度舔毛', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '检查饮食是否均衡，是否缺乏必需脂肪酸', 'source': '《小动物营养学》', 'confidence': 'medium'}], [{'action': '不要自行用抗真菌药、激素药或偏方处理', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要打骂惩罚或增加应激', 'source': '中国兽医协会科普指南', 'severity': 'high'}, {'action': '不要忽视脱毛迅速加重', 'source': '《小动物皮肤病学》', 'severity': 'medium'}, {'action': '不要让犬继续舔舐破损皮肤', 'source': '兽医临床指南', 'severity': 'medium'}], [{'condition': '脱毛区域迅速扩大、伴随渗液、化脓或明显疼痛', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随体重下降、食欲变化或多饮多尿', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '脱毛呈圆形边界清晰且可传染人', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '皮肤破损严重或出现自残', 'action': '建议立即就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("ear_mites_cat", "猫咪耳螨/耳部异味", ['cat'], [{'action': '观察耳道是否有黑褐色分泌物、异味或红肿', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '观察是否频繁摇头、抓耳或耳朵下垂', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '用宠物专用洗耳液清洁耳道，不要深挖', 'source': '兽医临床指南', 'confidence': 'high'}, {'action': '检查是否伴随皮肤瘙痒、脱毛或精神萎靡', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要用棉签深入耳道掏取', 'source': '兽医临床指南', 'severity': 'high'}, {'action': '不要用酒精、双氧水或人用滴耳液处理', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要忽视耳道持续异味或红肿', 'source': '《小动物皮肤病学》', 'severity': 'medium'}, {'action': '不要让猫继续抓挠耳朵加重损伤', 'source': '兽医临床指南', 'severity': 'high'}], [{'condition': '耳道严重红肿、流脓、有恶臭或频繁摇头导致血肿', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随精神萎靡、食欲下降或发热', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '头部倾斜、走路不稳或眼球震颤', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '耳部问题反复超过2周', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("ear_mites_dog", "狗狗耳螨/耳部异味", ['dog'], [{'action': '观察耳道是否有黑褐色或黄褐色分泌物、异味', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '观察是否频繁摇头、抓耳、耳朵下垂', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '用宠物专用洗耳液清洁耳道，不要深挖', 'source': '兽医临床指南', 'confidence': 'high'}, {'action': '检查是否伴随皮肤瘙痒、脱毛或精神萎靡', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要用棉签深入耳道掏取', 'source': '兽医临床指南', 'severity': 'high'}, {'action': '不要用酒精、双氧水或人用滴耳液处理', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要忽视耳道持续异味或红肿', 'source': '《小动物皮肤病学》', 'severity': 'medium'}, {'action': '不要让犬继续抓挠耳朵加重损伤', 'source': '兽医临床指南', 'severity': 'high'}], [{'condition': '耳道严重红肿、流脓、有恶臭或频繁摇头导致血肿', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随精神萎靡、食欲下降或发热', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '头部倾斜、走路不稳或眼球震颤', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '耳部问题反复超过2周', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("chin_acne_cat", "猫咪黑下巴/毛囊炎", ['cat'], [{'action': '观察下巴、颏部是否红、黑、糜烂或有脓疱', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '检查是否伴随抓挠下巴、舔嘴、过度舔毛', 'source': '《小动物皮肤病学》', 'confidence': 'high'}, {'action': '检查是否饮食不稳、换粮或日常清洁不足', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '保持下巴区域清洁，避免刺激和反复摩擦', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要用人用去屑洗剂或刺激性消毒液清洁下巴', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要反复揉搓或挤压脓疱', 'source': '兽医临床指南', 'severity': 'high'}, {'action': '不要自行使用激素类软膏', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要忽视长期不愈的毛囊炎', 'source': '《小动物皮肤病学》', 'severity': 'medium'}], [{'condition': '下巴出现明显溃烂、流脓、疼痛或肿胀', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随食欲下降、精神萎靡或发热', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '病灶迅速扩大或反复发作超过2周', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '面部周围出现明显肿胀或感染扩散', 'action': '需立即送医', 'priority': 'emergency'}], '{pet_name}，{breed}，{age}。于{time}出现{symptom_name}，已采取{actions}。目前精神状态{status}。'))

SYMPTOM_SEEDS.append(s("sneezing_cat", "猫咪打喷嚏", ['cat'], [{'action': '观察分泌物性状：清水样、脓性或带血', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '记录是否伴随流鼻涕、眼红、畏光或精神萎靡', 'source': '《猫病学》', 'confidence': 'high'}, {'action': '保持空气湿润、减少烟味和刺激性气味', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '用温湿棉球轻拭鼻周分泌物', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要用人用感冒药、伪麻黄碱滴鼻剂处理', 'source': '兽药基础数据库', 'severity': 'fatal'}, {'action': '不要强行灌药或使用大蒜、洋葱等偏方', 'source': '中国兽医协会科普指南', 'severity': 'fatal'}, {'action': '不要忽视持续超过3天不改善', 'source': '《猫病学》', 'severity': 'high'}, {'action': '不要让猫长期暴露于烟雾、香水或洗涤剂味道', 'source': '兽医临床指南', 'severity': 'medium'}], [{'condition': '脓性鼻涕伴随发热、精神萎靡或完全不吃不喝', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随眼睛红肿、角膜溃疡或频繁眨眼', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '出现呼吸困难、张口呼吸或嘴唇发紫', 'action': '需立即送医', 'priority': 'emergency'}, {'condition': '幼猫/老年猫出现明显打喷嚏或鼻涕', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。从{time}开始{symptom_name}，已持续{duration}。伴随症状{other_symptoms}。已尝试{actions}。'))

SYMPTOM_SEEDS.append(s("sneezing_dog", "狗狗打喷嚏", ['dog'], [{'action': '观察分泌物性状：清水样、脓性或带血', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '记录是否伴随咳嗽、流鼻涕、精神萎靡或食欲下降', 'source': '《犬病学》', 'confidence': 'high'}, {'action': '保持空气湿润、减少烟味和刺激性气味', 'source': '兽医临床指南', 'confidence': 'medium'}, {'action': '用温湿棉球轻拭鼻周分泌物', 'source': '兽医临床指南', 'confidence': 'medium'}], [{'action': '不要用人用感冒药或伪麻黄碱滴鼻剂处理', 'source': '兽药基础数据库', 'severity': 'high'}, {'action': '不要强行灌药或使用偏方', 'source': '中国兽医协会科普指南', 'severity': 'high'}, {'action': '不要忽视持续超过3天不改善', 'source': '《犬病学》', 'severity': 'high'}, {'action': '不要让犬暴露在烟雾或刺激性气味环境', 'source': '兽医临床指南', 'severity': 'medium'}], [{'condition': '脓性鼻涕伴随发热、精神萎靡或完全不吃不喝', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '伴随剧烈咳嗽、呼吸困难或嘴唇发紫', 'action': '建议立即就医', 'priority': 'urgent'}, {'condition': '鼻涕带血或单侧鼻孔持续流脓', 'action': '建议尽早就医', 'priority': 'urgent'}, {'condition': '短鼻犬种呼吸道症状更需尽快处理', 'action': '建议尽早就医', 'priority': 'urgent'}], '{pet_name}，{breed}，{age}。从{time}开始{symptom_name}，已持续{duration}。伴随症状{other_symptoms}。已尝试{actions}。'))


SYMPTOM_SEEDS.append(s("cough_cat", "猫咪咳嗽", ["cat"], [
    a("记录咳嗽频率、是否干咳或湿咳、是否伴随打喷嚏和流鼻涕", "《猫病学》", "high"),
    a("检查是否有异物卡喉、吸入粉尘、烟雾或新环境刺激", "兽医临床指南", "high"),
    a("观察呼吸是否急促、张口呼吸或嘴唇发紫", "《小动物临床急诊医学》", "high"),
    a("保持空气清洁、减少烟味、香水和粉尘刺激", "兽医临床指南", "medium"),
], [
    p("禁止自行给猫用人用止咳药、可待因或含麻黄碱药物", "兽药基础数据库", "high"),
    p("不要强行灌食或灌水，防止误吸", "《小动物临床急诊医学》", "fatal"),
    p("不要忽视持续咳嗽，可能是哮喘或呼吸道感染", "《猫病学》", "high"),
], [
    r("咳嗽伴随呼吸困难、张口呼吸或嘴唇发紫", "需立即送医", "emergency"),
    r("咳嗽伴随发热、食欲废绝、精神萎靡", "建议立即就医", "urgent"),
    r("咳嗽带血、泡沫痰或持续超过3天无改善", "建议尽早就医", "urgent"),
    r("怀疑异物卡喉或突然剧烈咳嗽", "需立即送医", "emergency"),
], T2))

SYMPTOM_SEEDS.append(s("cough_dog", "狗狗咳嗽", ["dog"], [
    a("记录咳嗽频率、是否干咳或湿咳、是否伴随流鼻涕", "《犬病学》", "high"),
    a("检查是否有吸入灰尘、烟雾、异物、运动后咳嗽或犬舍环境刺激", "兽医临床指南", "high"),
    a("观察是否伴随呼吸急促、喘气或口唇发紫", "《小动物临床急诊医学》", "high"),
    a("保持空气清洁、减少烟味和粉尘刺激", "兽医临床指南", "medium"),
], [
    p("禁止自行给犬用人用止咳药、含麻黄碱制剂或镇静药", "兽药基础数据库", "high"),
    p("不要让犬剧烈运动，防止加重呼吸负担", "《小动物临床急诊医学》", "high"),
    p("不要忽视持续咳嗽，可能是肺炎、心衰或气管塌陷", "《犬病学》", "high"),
], [
    r("咳嗽伴随呼吸困难、喘鸣或嘴唇发紫", "需立即送医", "emergency"),
    r("咳嗽伴随发热、食欲废绝、精神萎靡", "建议立即就医", "urgent"),
    r("咳嗽带血、持续超过3天无改善或老年犬明显喘气", "建议尽早就医", "urgent"),
    r("突然出现剧烈咳嗽、抓嘴、流涎或怀疑异物卡喉", "需立即送医", "emergency"),
], T2))

SYMPTOM_SEEDS.append(s("lethargy_cat", "猫咪精神萎靡嗜睡", ["cat"], [
    a("评估是否对呼唤、玩具、食物无反应或行动迟缓", "《猫病学》", "high"),
    a("测量体温并观察是否发热、体温过低或四肢冰凉", "兽医临床指南", "high"),
    a("检查是否伴随呕吐、腹泻、不吃不喝或体重下降", "《猫病学》", "high"),
    a("回忆最近饮食、活动、排泄和接触有毒环境是否异常", "兽医临床指南", "medium"),
], [
    p("禁止强行喂食或灌水，避免误吸", "《小动物临床急诊医学》", "fatal"),
    p("不要自行用提神药、兴奋剂或人用安眠药", "兽药基础数据库", "high"),
    p("不要忽视精神萎靡，猫往往会隐匿疼痛", "《猫病学》", "high"),
], [
    r("完全不动、对外界刺激无反应或呼吸困难", "需立即送医", "emergency"),
    r("伴随发热、体温异常、食欲废绝或黄疸", "建议立即就医", "urgent"),
    r("怀疑接触百合花、灭鼠药、酒精等有毒物", "需立即送医", "emergency"),
    r("幼猫或老年猫出现明显嗜睡或昏迷", "建议尽早就医", "urgent"),
], T2))

SYMPTOM_SEEDS.append(s("lethargy_dog", "狗狗精神萎靡嗜睡", ["dog"], [
    a("评估是否对呼唤、食物、玩具无反应或行动迟缓", "《犬病学》", "high"),
    a("测量体温并观察是否发热、体温过低或四肢冰凉", "兽医临床指南", "high"),
    a("检查是否伴随呕吐、腹泻、咳嗽、跛行或明显疼痛", "《犬病学》", "high"),
    a("回忆最近饮食、运动、排便和是否接触中毒物质", "兽医临床指南", "medium"),
], [
    p("禁止强行喂食或灌水，避免误吸", "《小动物临床急诊医学》", "fatal"),
    p("不要自行用提神药、兴奋剂或人用安眠药", "兽药基础数据库", "high"),
    p("不要忽视精神萎靡，可能是严重疾病的早期信号", "《犬病学》", "high"),
], [
    r("完全不动、对外界刺激无反应或呼吸困难", "需立即送医", "emergency"),
    r("伴随发热、体温异常、食欲废绝或明显脱水", "建议立即就医", "urgent"),
    r("怀疑接触巧克力、葡萄、灭鼠药等有毒物", "需立即送医", "emergency"),
    r("幼犬或老年犬出现明显嗜睡或昏迷", "建议尽早就医", "urgent"),
], T2))

SYMPTOM_SEEDS.append(s("vomit_diarrhea_cat", "猫咪呕吐腹泻同时发生", ["cat"], [
    a("记录呕吐和腹泻次数、颜色、黏液或血液量", "《猫病学》", "high"),
    a("暂时禁食6-8小时并提供少量清水，观察是否继续呕吐", "《猫病学》", "high"),
    a("检查是否换粮、误食人类食物、生肉或有寄生虫史", "兽医临床指南", "high"),
    a("观察是否伴随脱水、精神萎靡或食欲废绝", "兽医临床指南", "high"),
], [
    p("禁止自行服用人用止吐止泻药或抗生素", "兽药基础数据库", "high"),
    p("不要强行灌水或喂食，防止误吸", "《小动物临床急诊医学》", "fatal"),
    p("不要喂牛奶、乳制品或油腻人食", "《猫病学》", "high"),
], [
    r("24小时内呕吐超过3次、腹泻超过5次或带血", "建议立即就医", "urgent"),
    r("伴随明显脱水、精神萎靡或食欲废绝", "建议立即就医", "urgent"),
    r("幼猫或老年猫出现症状且持续超过24小时", "建议尽早就医", "urgent"),
    r("出现呼吸困难、腹痛或牙龈发干", "需立即送医", "emergency"),
], T2))

SYMPTOM_SEEDS.append(s("vomit_diarrhea_dog", "狗狗呕吐腹泻同时发生", ["dog"], [
    a("记录呕吐和腹泻次数、颜色、黏液或血液量", "《犬病学》", "high"),
    a("暂时禁食12-24小时并提供少量清水，观察是否继续呕吐", "《犬病学》", "high"),
    a("检查是否换粮、误食人类食物、骨头或有毒食物", "兽医临床指南", "high"),
    a("观察是否伴随脱水、精神萎靡或食欲废绝", "兽医临床指南", "high"),
], [
    p("禁止自行服用人用止吐止泻药或抗生素", "兽药基础数据库", "high"),
    p("不要强行灌水或喂食，防止误吸", "《小动物临床急诊医学》", "fatal"),
    p("不要喂巧克力、葡萄、洋葱或油炸食物", "兽药基础数据库", "fatal"),
], [
    r("24小时内呕吐超过4次、腹泻超过5次或带血", "建议立即就医", "urgent"),
    r("伴随明显脱水、精神萎靡或食欲废绝", "建议立即就医", "urgent"),
    r("幼犬或老年犬出现症状且持续超过24小时", "建议尽早就医", "urgent"),
    r("出现呼吸困难、腹痛或牙龈发干", "需立即送医", "emergency"),
], T2))
