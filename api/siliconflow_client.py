# src/api/siliconflow_client.py

import requests
import json
from .base_client import BaseApiClient # 确保你已经创建了 base_client.py

class SiliconflowClient(BaseApiClient):
    """硅基流动API的具体实现。"""

    def __init__(self, api_key: str, api_base: str):
        if not api_key:
            raise ValueError("Silicon Flow API Key不能为空。")
        self.api_key = api_key
        self.api_base = api_base
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }

    def get_chat_response_stream(self, messages: list, model_name: str, tools: list = None, tool_choice: str = "auto", **kwargs):
        """
        获取聊天回复的流式生成器，带有究极调试功能。
        """
        endpoint = f"{self.api_base}/chat/completions"
        stream_headers = self.headers.copy()
        stream_headers["Accept"] = "text/event-stream"
        
        payload = {
            "model": model_name, 
            "messages": messages, 
            "stream": True,
            **kwargs
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
        
        # --- 准备打印 Payload ---
        print("\n--- [API Client] 准备发起 POST 请求 ---")
        print(f"[API Client] URL: {endpoint}")
        print(f"[API Client] Headers: Authorization: Bearer ...{self.api_key[-4:]}")
        try:
            payload_to_print = json.loads(json.dumps(payload)) # 深拷贝
            if 'messages' in payload_to_print:
                for msg in payload_to_print['messages']:
                    if isinstance(msg.get('content'), str) and len(msg['content']) > 100:
                        msg['content'] = msg['content'][:100] + '...'
            print(f"[API Client] Payload: {json.dumps(payload_to_print, indent=2, ensure_ascii=False)}")
        except Exception:
            print(f"[API Client] Payload (部分): {str(payload)[:500]}")
        print("------------------------------------")

        # --- 开启 requests 的底层调试日志 ---
        import logging
        import http.client as http_client
        
        http_client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        
        try:
            print("[API Client] 正在执行 requests.post()，请注意下方可能出现的 'send:' 和 'reply:' 日志...")
            
            # 使用更严格的超时设置：5秒连接超时，60秒读取超时
            response = requests.post(
                endpoint, 
                headers=stream_headers, 
                json=payload, 
                stream=True, 
                timeout=(5, 60) 
            )
            
            # --- 请求发出后，立即关闭底层调试日志，避免刷屏 ---
            http_client.HTTPConnection.debuglevel = 0
            
            print(f"[API Client] requests.post() 执行完毕。服务器响应状态码: {response.status_code}")
            response.raise_for_status() # 如果状态码不是2xx，这里会抛出异常
            
            print("[API Client] 服务器响应成功，开始迭代 response.iter_lines()...")
            buffer = ""
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        json_str = decoded_line[len('data: '):].strip()
                        if json_str == '[DONE]':
                            print("[API Client] 收到 [DONE] 标记。")
                            break
                        try:
                            chunk_obj = json.loads(json_str)
                            yield chunk_obj
                        except json.JSONDecodeError:
                            buffer += json_str
                            try:
                                chunk_obj = json.loads(buffer)
                                yield chunk_obj
                                buffer = ""
                            except json.JSONDecodeError:
                                continue
            
            print("[API Client] response.iter_lines() 迭代结束。")
            
        except requests.exceptions.ConnectTimeout:
            print("!!! [API Client] 致命错误: 连接超时！无法在5秒内连接到服务器。请检查网络、防火墙或代理设置。")
            raise ConnectionError("连接API服务器超时，请检查网络。")
        except requests.exceptions.RequestException as e:
            print(f"!!! [API Client] 网络请求失败: {e}")
            raise e
        finally:
            # --- 确保在任何情况下都关闭调试日志 ---
            http_client.HTTPConnection.debuglevel = 0

    def get_embeddings(self, texts: list[str], model: str = "BAAI/bge-large-zh-v1.5"):
        """获取文本的Embedding向量。"""
        endpoint = f"{self.api_base}/embeddings"
        texts = [text.replace("\n", " ") for text in texts if text.strip()]
        if not texts:
            return []
        
        payload = {"input": texts, "model": model}
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json().get('data', [])
            return [item['embedding'] for item in data]
        except requests.exceptions.RequestException as e:
            print(f"获取Embeddings失败: {e}")
            raise e

    def list_models(self) -> dict | None:
        """
        获取可用的模型列表，并附带模型能力信息。
        返回格式: { "display_name": {"id": "model_id", "supports_tools": True/False, "is_vision": True/False} }
        """
        endpoint = f"{self.api_base}/models"
        try:
            # 1. 首先，执行网络请求
            response = requests.get(endpoint, headers=self.headers, timeout=15)
            response.raise_for_status() # 检查是否有HTTP错误 (如 401, 404, 500)
            
            # 2. 然后，解析响应
            models_data = response.json().get('data', [])
            
            processed_models = {}
            NON_CHAT_KEYWORDS = [
                'stable-diffusion', 'flux', 'embedding', 'bge', 
                'reranker', 'speech', 'so-vits', 'kolors', 
                't2v', 'i2v'
            ]
            
            # 已知支持工具调用的模型关键字 (这是一个示例，需要根据实际情况调整)
            TOOL_SUPPORT_KEYWORDS = ['glm-4', 'deepseek-v2', 'qwen2', 'qwen3']
            
            for model in models_data:
                model_id = model.get('id')
                if not model_id: continue
                
                model_id_lower = model_id.lower()
                
                is_non_chat = any(keyword in model_id_lower for keyword in NON_CHAT_KEYWORDS)
                if is_non_chat:
                    continue

                # 判断模型能力
                supports_tools = any(keyword in model_id_lower for keyword in TOOL_SUPPORT_KEYWORDS)
                is_vision = 'vl' in model_id_lower or 'vision' in model_id_lower
                
                display_name = model_id.replace("/", " / ").replace("-", " ").replace("_", " ").title()
                
                if supports_tools: display_name += " 🛠️"
                if is_vision: display_name += " 🖼️"

                processed_models[display_name] = {
                    "id": model_id,
                    "supports_tools": supports_tools,
                    "is_vision": is_vision
                }
            
            return processed_models if processed_models else None

        except requests.exceptions.RequestException as e:
            # 3. 在这里捕获所有网络相关的错误
            print(f"获取模型列表失败: {e}")
            return None
        except Exception as e:
            # 捕获其他可能的错误，例如 JSON 解析失败
            print(f"处理模型列表时发生未知错误: {e}")
            return None
