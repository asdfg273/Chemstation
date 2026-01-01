# src/api/ollama_client.py

import ollama
import json
from src.core.settings import settings

class OllamaClient:
    """
    一个用于与本地Ollama服务交互的API客户端。
    """
    def __init__(self, api_base=None, api_key=None): # api_key 在这里是可选的，为了接口统一
        # 从设置中获取Ollama的基础URL，如果不存在则使用默认值
        self.api_base = settings.get('Ollama/api_base', 'http://localhost:11434')
        
        # 使用官方的 ollama Python 库来创建一个客户端实例
        try:
            self.client = ollama.Client(host=self.api_base)
            # 尝试列出模型以验证连接
            self.client.list() 
            print(f"Ollama 客户端成功连接到: {self.api_base}")
        except Exception as e:
            print(f"!!! 连接 Ollama 服务失败: {e}")
            print("!!! 请确保 Ollama 正在运行，并且 API Base URL 配置正确。")
            self.client = None

    def list_models(self) -> dict | None:
        """从Ollama服务获取可用的模型列表。"""
        if not self.client: return None
        try:
            models_data = self.client.list().get('models', [])
            processed_models = {}
            for model in models_data:
                model_id = model.get('name')
                if model_id:
                    # Ollama模型通常都支持工具调用（取决于具体模型）和视觉（如果模型是多模态的）
                    # 我们可以根据模型ID中的关键字来做一个简单的判断
                    supports_tools = "instruct" in model_id.lower() or "function" in model_id.lower()
                    is_vision = "llava" in model_id.lower() or "bakllava" in model_id.lower()
                    
                    display_name = model_id.replace(":", " ").title()
                    if supports_tools: display_name += " 🛠️"
                    if is_vision: display_name += " 🖼️"
                    
                    processed_models[display_name] = {
                        "id": model_id,
                        "supports_tools": supports_tools,
                        "is_vision": is_vision
                    }
            return processed_models
        except Exception as e:
            print(f"从Ollama获取模型列表失败: {e}")
            return None

    def get_chat_response_stream(self, messages: list, model_name: str, **kwargs):
        """
        从Ollama获取聊天回复的流式生成器。
        注意：Ollama的 'tools' 参数格式与OpenAI API不同，我们暂时只支持纯文本。
        """
        if not self.client:
            # 返回一个空的生成器
            yield {}
            return

        try:
            # Ollama 客户端的 stream 方法直接返回一个生成器
            stream = self.client.chat(
                model=model_name,
                messages=messages,
                stream=True
            )
            
            # 我们需要将Ollama的响应格式，包装成我们程序期望的OpenAI兼容格式
            for chunk in stream:
                delta_content = chunk.get('message', {}).get('content', '')
                if delta_content:
                    yield {
                        "choices": [{
                            "delta": {"content": delta_content}
                        }]
                    }
        except Exception as e:
            print(f"调用Ollama模型时出错: {e}")
            yield {
                "choices": [{
                    "delta": {"content": f"\n\n[Ollama Error]: {e}"}
                }]
            }
