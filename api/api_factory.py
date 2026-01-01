# src/api/api_factory.py
from src.core.settings import settings
from .siliconflow_client import SiliconflowClient
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient
from .local_llama_client import LocalLlamaClient

def get_api_client():
    """
    根据配置文件，创建并返回相应的API客户端实例。
    工厂负责读取配置，并将配置作为参数传递给客户端。
    """
    provider = settings.get('API/provider', 'Siliconflow')
    provider_lower = provider.lower()

    try:
        if provider_lower == 'siliconflow':
            # 从 settings 读取 Siliconflow 需要的配置
            api_key = settings.get('API/silicon_flow_api_key')
            api_base = settings.get('API/silicon_flow_api_base', 'https://api.siliconflow.cn/v1')
            
            # 检查关键配置是否存在
            if not api_key:
                raise ValueError("Silicon Flow API Key 未在设置中配置。")
            
            # 将配置作为参数传递
            return SiliconflowClient(api_key=api_key, api_base=api_base)

        elif provider_lower == 'gemini':
            api_key = settings.get('API/gemini_api_key')
            if not api_key:
                raise ValueError("Gemini API Key 未在设置中配置。")
            return GeminiClient(api_key=api_key)

        elif provider_lower == 'ollama':
            # OllamaClient 内部自己读取设置，我们也可以统一到这里
            api_base = settings.get('Ollama/api_base', 'http://localhost:11434')
            return OllamaClient(api_base=api_base)

        elif provider_lower == 'localmodel':
            # LocalLlamaClient 内部也自己读取设置
            return LocalLlamaClient() # 这个可以保持不变，因为它只依赖一个路径

        else:
            raise ValueError(f"不支持的API供应商: {provider}")
    
    except Exception as e:
        # 捕获所有可能的初始化错误（比如缺Key），并重新抛出，以便主窗口捕获并显示
        raise ValueError(f"无法初始化API客户端: {e}")
