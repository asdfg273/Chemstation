# src/api/gemini_client.py
import google.generativeai as genai
from .base_client import BaseApiClient

class GeminiClient(BaseApiClient):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Google AI (Gemini) API Key不能为空。")
        genai.configure(api_key=api_key)
        # Gemini的Embedding模型和聊天模型是分开的
        self.embedding_model = "models/embedding-001"
        self.chat_model_id = "gemini-pro" # 默认

    def get_chat_response_stream(self, messages: list, model_name: str, **kwargs):
        # Gemini的messages格式与OpenAI不同，需要转换
        gemini_messages = self._convert_messages_to_gemini(messages)
        model = genai.GenerativeModel(model_name or self.chat_model_id)
        # stream=True 开启流式响应
        response = model.generate_content(gemini_messages, stream=True)
        for chunk in response:
            yield chunk.text

    def get_embeddings(self, texts: list[str], model: str = None):
        # model 参数在这里被忽略，因为Gemini目前主要是用一个固定的Embedding模型
        result = genai.embed_content(model=self.embedding_model, content=texts)
        return result['embedding']

    def list_models(self) -> dict:
        # 返回一些常见的Gemini模型
        # 也可以通过API拉取，但为简单起见先硬编码
        return {
            "Gemini Pro": "gemini-pro",
            "Gemini Pro Vision": "gemini-pro-vision"
        }

    def _convert_messages_to_gemini(self, messages: list) -> list:
        # ... 实现将OpenAI格式的消息列表转换为Gemini格式的逻辑 ...
        # 例如，Gemini不支持 'system' role, 需要合并到第一个 'user' role
        return converted_messages
