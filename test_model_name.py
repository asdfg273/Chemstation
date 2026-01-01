from core.ai.silicon_flow_api import SiliconFlowAPI

# 创建API实例
api = SiliconFlowAPI()

# 设置API密钥（使用配置文件中的密钥）
api.set_api_key("sk-nzfpdjqfdvbfnkenaxpgejrrsmhevpohtnljolyhqwnduycl")

# 测试chat_completion方法，不传递模型参数
response = api.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    temperature=0.7,
    max_tokens=100
)

print("测试完成")
