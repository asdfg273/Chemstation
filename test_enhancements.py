#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：测试增强后的化学式解析器和API日志功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import alternative_formula_parser
from utils.logger import api_logger
from core.ai.silicon_flow_api import SiliconFlowAPI
from utils.network.search_engine import SearchEngineFactory

def test_formula_parser():
    """测试增强后的化学式解析器"""
    print("=== 测试增强后的化学式解析器 ===")
    
    test_cases = [
        # 简单化学式
        "H2O",
        "CO2",
        "NaCl",
        "O2",
        "N2",
        
        # 带括号的化学式
        "(NH4)2SO4",
        "Al2(SO4)3",
        "Ca(OH)2",
        "Fe(NO3)3",
        
        # 带方括号的化学式
        "[Cu(NH3)4]SO4",
        "[Fe(CN)6]4-",
        "[Ag(NH3)2]Cl",
        "[Co(NH3)6]Cl3",
        
        # 带电荷的化学式
        "Na+",
        "Cl-",
        "SO42-",
        "PO43-",
        
        # 复杂嵌套化学式
        "K4[Fe(CN)6]",
        "(NH4)3[Fe(C2O4)3]·3H2O",
        "Na2[B4O5(OH)4]·8H2O"
    ]
    
    for formula in test_cases:
        result = alternative_formula_parser(formula)
        print(f"化学式: {formula}")
        print(f"解析结果: {result}")
        print("-")
    
    print("化学式解析器测试完成！\n")

def test_api_logger():
    """测试API调用日志功能"""
    print("=== 测试API调用日志功能 ===")
    
    # 测试手动记录日志
    print("测试手动记录API日志...")
    api_logger.log_api_call(
        endpoint="https://example.com/api/test",
        method="GET",
        params={"test": "value"},
        headers={"Authorization": "Bearer test_token"},
        status_code=200,
        response_time=0.5,
        api_type="test"
    )
    print("手动日志记录完成！")
    
    # 测试AI API日志
    print("测试AI API日志...")
    ai_api = SiliconFlowAPI()
    # 这里不会实际调用API，因为没有配置有效的API密钥，但会记录错误日志
    ai_api.get_models()
    print("AI API日志测试完成！")
    
    # 测试搜索API日志
    print("测试搜索API日志...")
    search_engine = SearchEngineFactory.get_search_engine("pubchem")
    # 这里不会实际调用API，因为PubChem API需要特定的请求格式，但会记录请求
    search_engine.search("water")
    print("搜索API日志测试完成！")
    
    print("API日志功能测试完成！\n")

def test_log_file_creation():
    """测试日志文件是否创建"""
    print("=== 测试日志文件创建 ===")
    
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = os.listdir(log_dir)
        api_log_files = [f for f in log_files if f.startswith("api_log_")]
        
        if api_log_files:
            print(f"找到API日志文件: {api_log_files}")
            # 显示最新日志文件的内容
            latest_log = max(api_log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
            latest_log_path = os.path.join(log_dir, latest_log)
            print(f"最新日志文件内容预览 (前5行):")
            with open(latest_log_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i < 5:
                        print(f"  {line.strip()}")
                    else:
                        break
        else:
            print("没有找到API日志文件")
    else:
        print("日志目录不存在")
    
    print("日志文件测试完成！")

if __name__ == "__main__":
    print("开始测试增强功能...\n")
    
    test_formula_parser()
    test_api_logger()
    test_log_file_creation()
    
    print("\n所有测试完成！")
