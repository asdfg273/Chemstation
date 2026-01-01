# api_client.py

import requests
import json
from src.core.settings import settings

# 注意：我们不再从config导入MODEL_NAME，而是通过函数参数传入
def get_ai_response(messages: list, model_name: str):
    """
    调用硅基流动API获取对话响应。

    Args:
        messages (list): 对话历史。
        model_name (str): 要使用的API模型标识符。

    Returns:
        str: AI的回复内容或错误信息。
    """
    if not API_KEY or "sk-" not in API_KEY:
        raise ValueError("请在 config.py 文件中设置您的 API_KEY。")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_name, # 使用传入的模型名称
        "messages": messages,
        "stream": False
    }

    try:
        # ... (try-except块保持不变) ...
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        response_data = response.json()
        ai_message = response_data['choices'][0]['message']['content']
        return ai_message.strip()

    except requests.exceptions.RequestException as e:
        print(f"API请求错误: {e}")
        return f"网络或API请求出错: {e}"
    except (KeyError, IndexError) as e:
        print(f"解析API响应时出错: {e}")
        print(f"原始响应: {response.text}")
        return f"无法解析API响应: {e}"

def get_ai_response_stream(messages: list[str], model_name: str):
    """
    以流式方式调用API，并逐块产生(yield)AI的回复内容。
    """
    # --- 从 settings 对象加载配置 ---
    API_KEY = settings.get('API/silicon_flow_api_key')
    API_ENDPOINT = settings.get('API/silicon_flow_api_base') + '/chat/completions'

    # --- 严格验证配置 ---
    if not API_KEY:
        raise ValueError("请在“设置”中配置您的硅基流动 API Key。")
    
    # 关键修正：确保API_ENDPOINT有效
    if not API_ENDPOINT or not API_ENDPOINT.startswith(('http://', 'https://')):
        # 如果端点为空，或者不是一个合法的URL，都抛出错误
        default_endpoint = "https://api.siliconflow.cn/v1/chat/completions"
        raise ValueError(
            f"API 端点地址无效: '{API_ENDPOINT}'。\n"
            f"请在“设置”中配置一个有效的URL，例如：\n{default_endpoint}"
        )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    payload = {
        "model": model_name,
        "messages": messages,
        "stream": True
    }

    try:
        # 使用 stream=True，requests不会立即下载全部内容
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, stream=True, timeout=60)
        response.raise_for_status()

        # 逐行迭代响应内容
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                # SSE (Server-Sent Events) 格式通常以 "data: " 开头
                if decoded_line.startswith('data: '):
                    json_str = decoded_line[len('data: '):].strip()
                    
                    # 检查是否是流的结束标志
                    if json_str == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(json_str)
                        # 提取增量内容
                        delta = chunk.get('choices', [{}])[0].get('delta', {})
                        content_chunk = delta.get('content', '')
                        if content_chunk:
                            yield content_chunk  # 产生一小块文本
                    except json.JSONDecodeError:
                        print(f"无法解析的JSON块: {json_str}")
                        continue
    
    except requests.exceptions.RequestException as e:
        print(f"流式API请求错误: {e}")
        # 在发生错误时，也产生一个错误信息，让UI可以显示
        yield f"\n\n[网络或API错误: {e}]"
    except Exception as e:
        print(f"处理流时发生未知错误: {e}")
        yield f"\n\n[未知错误: {e}]"

def fetch_available_models():
    """
    从硅基流动API获取所有可用的模型列表。

    Returns:
        dict: 一个字典，格式为 {"显示名称": "模型ID"}。
              例如：{"通义千问 Qwen2-7B": "Qwen/Qwen2-7B-Instruct"}
              如果请求失败，则返回 None。
    """
    API_KEY = settings.get('API', 'silicon_flow_api_key')
    # 注意：这里的端点是 /v1/models
    LIST_MODELS_ENDPOINT = "https://api.siliconflow.cn/v1/models"

    if not API_KEY:
        print("警告: API Key 未配置，无法获取在线模型列表。")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.get(LIST_MODELS_ENDPOINT, headers=headers, timeout=15)
        response.raise_for_status()
        
        models_data = response.json().get('data', [])
        
        # 将API返回的原始列表处理成我们需要的字典格式
        # 我们可以做一些筛选，比如只保留包含 "instruct" 或 "chat" 的模型
        processed_models = {}
        for model in models_data:
            model_id = model.get('id')
            if model_id and 'deepseek' in model_id.lower() or 'chat' in model_id.lower() or 'instruct' in model_id.lower():
                # 简单地用模型ID作为显示名称，可以进一步美化
                # 例如：将 "Qwen/Qwen2-7B-Instruct" 变为 "Qwen2 7B Instruct"
                display_name = model_id.replace("/", " ").replace("-", " ").replace("Instruct", "").replace("Chat", "").strip()
                processed_models[display_name] = model_id
        
        # 确保字典不为空
        if not processed_models:
            print("警告: 从API获取的模型列表为空或不包含可用的对话模型。")
            return None
            
        return processed_models

    except requests.exceptions.RequestException as e:
        print(f"获取模型列表失败: {e}")
        return None


def get_embeddings(texts: list[str], model: str = "bge-large-zh-v1.5") -> list[list[float]]:
    """
    为一批文本生成Embedding向量。
    
    Args:
        texts (list[str]): 需要处理的文本列表。
        model (str): 使用的Embedding模型ID。
    
    Returns:
        list[list[float]]: 每个文本对应的向量列表。如果失败则返回空列表。
    """
    API_KEY = settings.get('API/silicon_flow_api_key')
    # Embedding API的端点
    EMBEDDING_ENDPOINT = "https://api.siliconflow.cn/v1/embeddings"
    
    if not API_KEY:
        print("警告: API Key 未配置，无法生成Embeddings。")
        return []
        
    # API要求输入不能是空字符串
    texts = [text.replace("\n", " ") for text in texts if text.strip()]
    if not texts:
        return []

    payload = {
        "input": texts,
        "model": model,
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        # --- 新增的调试打印 ---
        import json
        print("--- 发送给 Embedding API 的 Payload ---")
        # 我们只打印前几个字符，避免终端被长文本刷屏
        payload_to_print = payload.copy()
        payload_to_print['input'] = [t[:100] + '...' for t in payload['input']]
        print(json.dumps(payload_to_print, indent=2, ensure_ascii=False))
        print("------------------------------------")
        # --- 结束调试打印 ---

        response = requests.post(EMBEDDING_ENDPOINT, headers=headers, json=payload, timeout=30)
        
        # --- 打印更详细的错误信息 ---
        if not response.ok:
            print(f"!!! Embedding API 错误响应: {response.status_code}")
            try:
                print(response.json()) # 尝试打印服务器返回的错误详情
            except json.JSONDecodeError:
                print(response.text) # 如果不是JSON，就打印原始文本
        # ---
        
        response.raise_for_status()
        
        data = response.json().get('data', [])
        embeddings = [item['embedding'] for item in data]
        return embeddings
        
    except requests.exceptions.RequestException as e:
        # 这个打印语句已经有了，很好
        print(f"获取Embeddings失败: {e}")
        return []
