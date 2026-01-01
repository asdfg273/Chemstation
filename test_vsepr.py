#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的VSEPR模型
"""

from app import ChemApp

def test_vsepr_models():
    """测试多种分子的VSEPR模型"""
    print("=== 测试优化后的VSEPR模型 ===")
    
    # 创建ChemApp实例
    app = ChemApp()
    
    # 测试分子列表
    test_molecules = [
        'H2O',
        'NH3', 
        'CH4',
        'CO2',
        'SO2',
        'SO3',
        'H3PO4',
        'HNO3',
        'PCl5',
        'SF6',
        'O3',
        'HCl',
        'BeCl2',
        'BCl3',
        'CCl4',
        'SiF4',
        'PF5',
        'BrF5',
        'XeF4'
    ]
    
    # 测试每个分子
    for mol in test_molecules:
        print(f"\n测试 {mol} 的VSEPR模型...")
        try:
            result = app.get_vsepr_shape(mol)
            shape, lone_pairs, composition, center_atom = result
            print(f"  中心原子: {center_atom}")
            print(f"  几何构型: {shape}")
            print(f"  孤对电子对数: {lone_pairs}")
            print(f"  分子组成: {composition}")
            print("  测试通过！")
        except Exception as e:
            print(f"  错误: {e}")
            print("  测试失败！")
    
    print("\n=== 所有测试完成！ ===")

if __name__ == "__main__":
    test_vsepr_models()
