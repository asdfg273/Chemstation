# chem_assistant/core/advisors/safety_advisor.py

# 一个简单的化学品知识库
# 键：化学式（大小写不敏感）
# 值：一个包含“条件建议”和“废弃物处理”的字典
KNOWLEDGE_BASE = {
    # 强酸
    "H2SO4": {
        "condition": "【高危】浓硫酸具有强腐蚀性和脱水性！\n- 操作时必须佩戴耐酸手套和护目镜。\n- 稀释时必须将浓硫酸沿容器壁缓慢注入水中，严禁反向操作！\n- 反应放热剧烈，建议在冰水浴中进行。",
        "waste": "【危险废弃物】废酸液不可直接倒入下水道！\n- 应在搅拌和冷却下，用碱（如碳酸氢钠）缓慢中和至中性。\n- 中和后的废液按当地规定处理。"
    },
    "HCL": {
        "condition": "【高危】浓盐酸易挥发，产生刺激性气体！\n- 必须在通风橱中操作！\n- 佩戴耐酸手套和护目镜。",
        "waste": "【危险废弃物】废酸液处理方法同硫酸。"
    },
    # 强碱
    "NAOH": {
        "condition": "【高危】氢氧化钠是强腐蚀性固体，溶解时大量放热！\n- 避免皮肤直接接触，佩戴手套和护目镜。\n- 溶解时建议在冰水浴中进行，并使用耐热容器。",
        "waste": "【危险废弃物】废碱液不可直接倒入下水道！\n- 应在搅拌和冷却下，用稀酸（如稀盐酸）缓慢中和至中性。\n- 中和后的废液按当地规定处理。"
    },
    # 易燃有机物
    "C2H5OH": { # 乙醇
        "condition": "【易燃】乙醇蒸汽与空气可形成爆炸性混合物。\n- 操作区域严禁明火和电火花！\n- 保持良好通风。",
        "waste": "【有机废液】应收集在指定的有机废液桶中，不可倒入下水道。"
    },
    "CH3COCH3": { # 丙酮
        "condition": "【易燃】丙酮极易挥发和燃烧。\n- 严禁明火！确保良好通风。\n- 对塑料和橡胶有溶解性，请选择合适的容器。",
        "waste": "【有机废液】应收集在指定的有机废液桶中，与其他废液分开存放。"
    },
    # 氧化剂
    "H2O2": {
        "condition": "【强氧化性】高浓度过氧化氢不稳定，遇杂质、热或光照易分解爆炸！\n- 避免接触金属粉末、有机物等还原剂。\n- 操作需轻柔，避免剧烈摇晃。",
        "waste": "【危险废弃物】可在大量水中稀释后，用还原剂（如亚硫酸钠）缓慢分解，确认无气泡产生后再处理。"
    }
}

def generate_advice(reactants, products):
    """
    根据反应物和产物生成实验建议。
    :param reactants: 反应物列表 (e.g., ['H2SO4', 'NaOH'])
    :param products: 产物列表 (e.g., ['Na2SO4', 'H2O'])
    :return: 格式化后的建议字符串
    """
    advice_sections = {
        "反应条件建议": set(),
        "废弃物处理指南": set()
    }
    
    all_chemicals = reactants + products
    
    for chemical in all_chemicals:
        # 统一将化学式转为大写以匹配知识库
        # 并移除可能的系数和空格，例如 "2 H2SO4" -> "H2SO4"
        formula = ''.join(filter(str.isalpha, chemical.upper()))

        if formula in KNOWLEDGE_BASE:
            info = KNOWLEDGE_BASE[formula]
            if "condition" in info:
                advice_sections["反应条件建议"].add(info["condition"])
            if "waste" in info:
                advice_sections["废弃物处理指南"].add(info["waste"])

    if not any(advice_sections.values()):
        return "未找到针对该反应的特定建议。\n请始终遵循标准实验室安全规程(SLP)。"

    # 构建最终的报告
    report = []
    for title, advices in advice_sections.items():
        if advices:
            report.append(f"--- {title} ---")
            for i, advice in enumerate(advices, 1):
                report.append(f"{i}. {advice}\n")
    
    return "\n".join(report)

