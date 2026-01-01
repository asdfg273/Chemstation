from core.ai.silicon_flow_api import SiliconFlowAPI
from core.config import config_manager

# 初始化API客户端
aio_api = SiliconFlowAPI()

# 获取API密钥
api_key = config_manager.get("ai.api_key", "")
if not api_key:
    print("错误: API密钥未配置")
    exit(1)

# 设置API密钥
aio_api.set_api_key(api_key)

# 构建请求消息
messages = [
    {
        "role": "system",
        "content": "你是一个专业的化学助手，帮助用户解决化学相关的问题。"
    },
    {
        "role": "user",
        "content": "请简要介绍一下三草酸合铁酸钾的制备方法。"
    }
]

# 调用AI API
response = aio_api.chat_completion(
    messages=messages,
    temperature=0.7,
    max_tokens=1000
)

# 处理API响应
if response:
    print(f"API响应: {response}")
    
    # 检查是否有错误信息
    if "error" in response:
        error_msg = response["error"].get("message", "未知错误")
        print(f"API错误: {error_msg}")
    elif "choices" in response and len(response["choices"]) > 0:
        # 检查choices[0]的结构
        if isinstance(response["choices"][0], dict):
            if "message" in response["choices"][0]:
                ai_response = response["choices"][0]["message"]["content"]
                print(f"AI响应: {ai_response}")
            elif "text" in response["choices"][0]:
                # 处理一些API可能返回的text字段
                ai_response = response["choices"][0]["text"]
                print(f"AI响应: {ai_response}")
            else:
                print(f"API响应结构异常: {response}")
        else:
            print(f"API响应结构异常: {response}")
    else:
        print(f"API响应不包含有效的choices: {response}")
else:
    print("API请求失败，未收到响应")
