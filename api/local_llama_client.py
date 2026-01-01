# src/api/local_llama_client.py

import os
from llama_cpp import Llama
from src.core.settings import settings
import threading 
class LocalLlamaClient:
    """
    一个直接加载本地GGUF模型文件进行推理的客户端。
    """
    def __init__(self, api_base=None, api_key=None):
        self.model_path = settings.get('LocalModel/model_path', '')
        self.llm = None
        self.is_initialized = False
        self.load_error = None
        self.loading_thread = None

        if os.path.exists(self.model_path):
            # 不再在 __init__ 中直接加载，而是启动一个后台线程
            print("--- [LocalLlamaClient] 配置路径有效，准备在后台加载模型... ---")
            self.loading_thread = threading.Thread(target=self._load_model)
            self.loading_thread.daemon = True
            self.loading_thread.start()
        else:
            self.load_error = f"未找到本地模型文件: {self.model_path}"
            print(f"!!! [LocalLlamaClient] 警告: {self.load_error}")

    def _load_model(self):
        """这个方法会在一个独立的后台线程中执行。"""
        try:
            print(f"--- [BG Thread] 开始从路径加载GGUF模型: {self.model_path} ---")
            # 在这里执行耗时的加载操作
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=4096,
                n_gpu_layers=0,
                verbose=True
            )
            self.is_initialized = True
            print("--- [BG Thread] GGUF模型加载成功！ ---")
        except Exception as e:
            self.load_error = e
            print(f"!!! [BG Thread] 加载本地GGUF模型失败: {e}")

    def list_models(self) -> dict | None:
        # 这个方法可能会在模型还在加载时被调用，需要处理这种情况
        if not self.model_path: return {"(未配置路径)": {"id": ""}}
        
        model_name = os.path.basename(self.model_path)
        status = ""
        if self.loading_thread and self.loading_thread.is_alive():
            status = "(正在加载...)"
        elif self.is_initialized:
            status = "(本地, 已就绪)"
        elif self.load_error:
            status = "(加载失败!)"
        
        display_name = f"{model_name.replace('.gguf', '').replace('-', ' ').title()} {status}"
        return {display_name: {"id": model_name, "supports_tools": False, "is_vision": False}}

    def get_chat_response_stream(self, messages: list, model_name: str, **kwargs):
        # 检查模型是否正在加载中
        if self.loading_thread and self.loading_thread.is_alive():
            error_msg = "[Local Model Error]: 模型仍在后台加载中，请稍候..."
            yield {"choices": [{"delta": {"content": error_msg}}]}
            return
        
        # 检查是否加载失败或未初始化
        if not self.is_initialized or not self.llm:
            error_msg = f"[Local Model Error]: 本地模型未加载或初始化失败。错误: {self.load_error}"
            yield {"choices": [{"delta": {"content": error_msg}}]}
            return

        try:
            # llama-cpp-python 的 create_chat_completion 方法与OpenAI API非常兼容
            stream = self.llm.create_chat_completion(
                messages=messages,
                stream=True,
                max_tokens=1024, # 可以设置一些默认参数
            )
            
            # 直接迭代并返回与OpenAI格式兼容的块
            for chunk in stream:
                yield chunk

        except Exception as e:
            print(f"!!! [LocalLlamaClient] 本地模型推理时出错: {e}")
            error_msg = f"\n\n[Local Model Error]: {e}"
            yield {"choices": [{"delta": {"content": error_msg}}]}
