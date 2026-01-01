import requests
import json
import time
from core.config import config_manager
from utils.logger import api_logger

class SiliconFlowAPI:
    """硅基流动AI API封装"""
    
    def __init__(self):
        self.api_key = config_manager.get("ai.api_key", "")
        self.base_url = config_manager.get("ai.base_url", "https://api.siliconflow.cn/v1")
        self.timeout = config_manager.get("ai.timeout", 120)  # 增加超时时间到120秒
        
        # 从配置中读取模型名称，如果没有指定则使用默认值
        self.default_model = config_manager.get("ai.model", "Qwen/QwQ-32B")
        
        # 请求头
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def set_api_key(self, api_key):
        """设置API密钥"""
        self.api_key = api_key
        config_manager.set("ai.api_key", api_key)
        self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def get_models(self):
        """获取可用模型列表"""
        url = f"{self.base_url}/models"
        start_time = time.time()
        response = None
        error = None
        
        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # 记录API调用日志
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="GET",
                headers=safe_headers,
                response=result,
                status_code=response.status_code,
                response_time=response_time,
                api_type="ai"
            )
            
            return result
        except requests.exceptions.RequestException as e:
            error = e
            print(f"获取模型列表失败: {e}")
            
            # 记录错误日志
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="GET",
                headers=safe_headers,
                error=error,
                response_time=response_time,
                api_type="ai"
            )
            
            return None
    
    def chat_completion(self, messages, model=None, temperature=0.7, max_tokens=1000):
        """生成聊天完成"""
        if not model:
            model = self.default_model
        
        url = f"{self.base_url}/chat/completions"
        start_time = time.time()
        response = None
        error = None
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        try:
            response = requests.post(
                url=url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # 记录API调用日志
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="POST",
                params={"json": payload},
                headers=safe_headers,
                response=result,
                status_code=response.status_code,
                response_time=response_time,
                api_type="ai"
            )
            
            return result
        except requests.exceptions.RequestException as e:
            error = e
            print(f"聊天完成请求失败: {e}")
            
            # 记录错误日志
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="POST",
                params={"json": payload},
                headers=safe_headers,
                error=error,
                response_time=response_time,
                api_type="ai"
            )
            
            return None
        except json.JSONDecodeError as e:
            error = e
            print(f"解析聊天完成响应失败: {e}")
            
            # 记录错误日志
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="POST",
                params={"json": payload},
                headers=safe_headers,
                error=error,
                response_time=response_time,
                api_type="ai"
            )
            
            return None
    
    def chat_completion_stream(self, messages, model=None, temperature=0.7, max_tokens=1000):
        """生成聊天完成（流式）"""
        if not model:
            model = self.default_model
        
        url = f"{self.base_url}/chat/completions"
        start_time = time.time()
        response = None
        error = None
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": True
        }
        
        try:
            response = requests.post(
                url=url,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 记录API调用日志（开始）
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="POST",
                params={"json": payload},
                headers=safe_headers,
                status_code=response.status_code,
                response_time=response_time,
                api_type="ai"
            )
            
            # 流式响应处理
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        json_str = decoded_line[len('data: '):].strip()
                        if json_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(json_str)
                            yield chunk
                        except json.JSONDecodeError as e:
                            print(f"解析流式响应失败: {e}")
                            continue
        except requests.exceptions.RequestException as e:
            error = e
            print(f"聊天完成请求失败: {e}")
            
            # 记录错误日志
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="POST",
                params={"json": payload},
                headers=safe_headers,
                error=error,
                response_time=response_time,
                api_type="ai"
            )
            
            yield None
        except Exception as e:
            error = e
            print(f"流式处理异常: {e}")
            
            # 记录错误日志
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="POST",
                params={"json": payload},
                headers=safe_headers,
                error=error,
                response_time=response_time,
                api_type="ai"
            )
            
            yield None
    
    def generate_text(self, prompt, model=None, temperature=0.7, max_tokens=1000):
        """生成文本"""
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的化学助手，帮助用户解决化学相关的问题。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = self.chat_completion(messages, model, temperature, max_tokens)
        if response and "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        else:
            return None
    
    def get_usage(self):
        """获取API使用情况"""
        url = f"{self.base_url}/usage"
        start_time = time.time()
        response = None
        error = None
        
        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # 记录API调用日志
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="GET",
                headers=safe_headers,
                response=result,
                status_code=response.status_code,
                response_time=response_time,
                api_type="ai"
            )
            
            return result
        except requests.exceptions.RequestException as e:
            error = e
            print(f"获取API使用情况失败: {e}")
            
            # 记录错误日志
            end_time = time.time()
            response_time = end_time - start_time
            
            # 隐藏敏感信息
            safe_headers = self.headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method="GET",
                headers=safe_headers,
                error=error,
                response_time=response_time,
                api_type="ai"
            )
            
            return None
    
    def is_api_key_valid(self):
        """验证API密钥是否有效"""
        # 尝试获取模型列表来验证API密钥
        models = self.get_models()
        return models is not None and "data" in models
    
    def get_api_status(self):
        """获取API状态"""
        url = f"{self.base_url}/status"
        start_time = time.time()
        response = None
        error = None
        
        try:
            response = requests.get(
                url=url,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # 记录API调用日志
            end_time = time.time()
            response_time = end_time - start_time
            
            api_logger.log_api_call(
                endpoint=url,
                method="GET",
                response=result,
                status_code=response.status_code,
                response_time=response_time,
                api_type="ai"
            )
            
            return result
        except requests.exceptions.RequestException as e:
            error = e
            print(f"获取API状态失败: {e}")
            
            # 记录错误日志
            end_time = time.time()
            response_time = end_time - start_time
            
            api_logger.log_api_call(
                endpoint=url,
                method="GET",
                error=error,
                response_time=response_time,
                api_type="ai"
            )
            
            return None