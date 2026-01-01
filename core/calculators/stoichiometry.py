# 文件路径: chem_assistant/core/calculators/stoichiometry.py
# 版本: v2.2 - 智能系数处理

import re
from chempy import Substance
from chempy.util import periodic
from collections import defaultdict
import pyparsing

# --- 全新的、智能化的式量解析函数 ---
def analyze_formula(formula_string: str):
    """
    智能解析化学式字符串，自动处理前面的系数。
    例如: "2H2O", "C6H12O6", "FeSO4·7H2O"
    返回: (总质量, 详细分析字典, 系数) 或 (None, 错误信息, None)
    """
    formula_string = formula_string.strip()
    if not formula_string:
        return None, "错误：输入不能为空！", 1

    # 使用正则表达式分离系数和化学式
    # 匹配模式: (可选的数字系数)(可选的空格)(剩下的所有字符作为化学式)
    match = re.match(r"(\d+\.?\d*)\s*(.*)", formula_string)
    
    coefficient = 1.0
    actual_formula = formula_string

    if match:
        try:
            # 如果匹配成功，且化学式部分不为空
            if match.group(2):
                coeff_str, formula_part = match.groups()
                coefficient = float(coeff_str)
                actual_formula = formula_part
        except (ValueError, IndexError):
            # 如果转换失败，则认为没有系数
            pass

    try:
        substance = Substance.from_formula(actual_formula)
        # chempy有时返回整数，统一转为float
        total_mass = float(substance.mass)
        
        analysis = defaultdict(lambda: {'count': 0, 'mass': 0.0})
        
        # substance.composition 是一个 {element_id: count} 的字典
        for element_id, count in substance.composition.items():
            element_symbol = periodic.symbols[element_id - 1]
            element_mass = periodic.mass_from_composition({element_id: 1})
            
            analysis[element_symbol]['symbol'] = element_symbol
            analysis[element_symbol]['count'] += count
            analysis[element_symbol]['mass'] += count * element_mass
            
        final_analysis = {}
        for symbol, data in analysis.items():
            percentage = (data['mass'] / total_mass) * 100 if total_mass > 0 else 0
            final_analysis[symbol] = {
                'symbol': symbol,
                # 将最终结果乘以系数
                'count': data['count'] * coefficient,
                'mass': data['mass'] * coefficient,
                'percentage': percentage # 百分比不应乘以系数
            }
        
        # 总质量也要乘以系数
        final_total_mass = total_mass * coefficient
        
        return final_total_mass, final_analysis, coefficient

    except (pyparsing.exceptions.ParseException, ValueError, TypeError) as e:
        error_msg = f"无法解析化学式 '{actual_formula}'。\n\n"
        error_msg += "请检查:\n- 元素符号是否正确 (区分大小写, e.g., 'Co' vs 'CO').\n"
        error_msg += "- 括号是否匹配 (e.g., C(CH3)4 ).\n"
        error_msg += "- 结晶水格式是否正确 (e.g., CuSO4·5H2O).\n\n"
        error_msg += f"底层错误: {e}"
        return None, error_msg, None
    except Exception as e:
        return None, f"发生未知错误: {e}", None


def balance_chemical_equation(reactants_str: str, products_str: str):
    """配平化学方程式"""
    try:
        # 使用正则表达式分割物质，支持 '+' 和 ','
        reac_list = [r.strip() for r in re.split(r'\s*[+,]\s*', reactants_str) if r.strip()]
        prod_list = [p.strip() for p in re.split(r'\s*[+,]\s*', products_str) if p.strip()]

        if not reac_list or not prod_list:
            return None, None, "错误: 反应物和产物均不能为空。"

        from chempy.equilibria import Equation
        reac, prod = Equation.balance(set(reac_list), set(prod_list))
        
        # 格式化输出字符串
        reac_str = ' + '.join(f"{v}{k}" for k, v in reac.items())
        prod_str = ' + '.join(f"{v}{k}" for k, v in prod.items())
        balanced_eq_str = f"{reac_str} -> {prod_str}"
        
        return reac, prod, f"配平成功: {balanced_eq_str}"
    except Exception as e:
        return None, None, f"配平失败: {e}. 请检查化学式是否有效。"


def calculate_stoichiometry(reac_coeffs, prod_coeffs, known_formula, known_mass):
    """根据配平的方程式进行化学计量计算"""
    all_formulas = {**reac_coeffs, **prod_coeffs}
    
    if known_formula not in all_formulas:
        return None, f"错误: 已知物质 '{known_formula}' 不在方程式中。"
    
    try:
        known_sub = Substance.from_formula(known_formula)
        known_moles = known_mass / known_sub.mass
        
        # 找到已知物在方程式中的计量系数
        known_coeff = all_formulas[known_formula]
        
        base_moles = known_moles / known_coeff
        
        header = f"基于 {known_mass:.2f}g {known_formula} (计量数 {known_coeff}) 计算:\n"
        header += "★" * 40 + "\n"
        header += f"{'分类':<10}{'物质':<20}{'计量数':<10}{'摩尔数(mol)':<15}{'理论质量(g)':<15}\n"
        header += "-" * 70 + "\n"
        
        result_text = header
        
        # 计算反应物
        for formula, coeff in reac_coeffs.items():
            sub = Substance.from_formula(formula)
            moles_needed = base_moles * coeff
            mass_needed = moles_needed * sub.mass
            result_text += f"{'反应物':<10}{formula:<20}{coeff:<10}{moles_needed:<15.4f}{mass_needed:<15.4f}\n"

        # 计算产物
        for formula, coeff in prod_coeffs.items():
            sub = Substance.from_formula(formula)
            moles_produced = base_moles * coeff
            mass_produced = moles_produced * sub.mass
            result_text += f"{'产物':<10}{formula:<20}{coeff:<10}{moles_produced:<15.4f}{mass_produced:<15.4f}\n"
            
        return result_text, None
        
    except Exception as e:
        return None, f"计算出错: {e}"

def calculate_yield(actual_mass, theoretical_mass):
    """计算产率"""
    if theoretical_mass <= 0:
        return None, "理论产量必须大于0！"
    
    yield_percent = (actual_mass / theoretical_mass) * 100
    return yield_percent, None
