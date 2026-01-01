#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI助手修复效果的脚本
"""

import sys
import time
from core.ai.silicon_flow_api import SiliconFlowAPI
from core.config import config_manager

print("测试AI助手修复效果...")
print("=" * 50)

# 初始化API客户端
ai_api = SiliconFlowAPI()

# 获取API密钥
api_key = config_manager.get("ai.api_key", "")
if not api_key:
    print("错误: API密钥未配置")
    sys.exit(1)

print(f"API密钥: {api_key[:10]}...")

# 设置API密钥
ai_api.set_api_key(api_key)

# 测试API连接
print("测试API连接...")
start_time = time.time()

# 构建简单的请求消息
messages = [
    {
        "role": "system",
        "content": "你是一个专业的化学助手，帮助用户解决化学相关的问题。"
    },
    {
        "role": "user",
        "content": "请简单介绍一下水的化学性质。"
    }
]

try:
    # 调用AI API
    response = ai_api.chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
    
    end_time = time.time()
    print(f"API请求耗时: {end_time - start_time:.2f}秒")
    
    if response:
        if "error" in response:
            error_msg = response["error"].get("message", "未知错误")
            print(f"API错误: {error_msg}")
        elif "choices" in response and len(response["choices"]) > 0:
            ai_response = response["choices"][0]["message"]["content"]
            print(f"AI响应: {ai_response[:100]}...")
            print("\n✅ 修复成功: API调用正常，没有出现卡死问题")
        else:
            print("API响应结构异常")
    else:
        print("API请求失败，未收到响应")
        print("\n⚠️  修复可能未完全成功: API请求超时")
        
except Exception as e:
    end_time = time.time()
    print(f"API请求耗时: {end_time - start_time:.2f}秒")
    print(f"API请求失败: {e}")
    print("\n⚠️  修复可能未完全成功: API请求出现异常")

print("=" * 50)
print("测试完成")
