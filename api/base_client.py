# src/api/base_client.py
from abc import ABC, abstractmethod

class BaseApiClient(ABC):
    """所有API客户端必须遵守的抽象基类（接口）。"""
    
    @abstractmethod
    def get_chat_response_stream(self, messages: list, model_name: str, **kwargs):
        """获取聊天回复的流式生成器。"""
        pass

    @abstractmethod
    def get_embeddings(self, texts: list[str], model: str):
        """获取文本的Embedding向量。"""
        pass

    @abstractmethod
    def list_models(self) -> dict:
        """获取可用的模型列表。"""
        pass
