#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试硅基流动API调用
"""

import requests
import json
from core.config import config_manager

def test_silicon_flow_api():
    """测试硅基流动API调用"""
    print("=== 测试硅基流动API调用 ===")
    
    # 获取API配置
    api_key = config_manager.get("ai.api_key", "")
    api_base = config_manager.get("ai.base_url", "https://api.siliconflow.cn/v1")
    
    if not api_key:
        print("错误: 未配置API密钥")
        return
    
    print(f"使用API基础URL: {api_base}")
    print(f"使用API密钥: {api_key[:4]}...{api_key[-4:]}")
    
    # 构建请求
    endpoint = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 使用正确的硅基流动模型名称格式
    payload = {
        "model": "Qwen/QwQ-32B",
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的化学助手，帮助用户解决化学相关的问题。"
            },
            {
                "role": "user",
                "content": "请简要介绍一下三草酸合铁酸钾的制备方法。"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    print("\n发送API请求...")
    print(f"请求URL: {endpoint}")
    print(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(f"\nAI响应: {content}")
            else:
                print(f"\n响应结构异常: {result}")
        else:
            print(f"\nAPI请求失败: {response.text}")
            
    except Exception as e:
        print(f"\n请求异常: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_silicon_flow_api()
