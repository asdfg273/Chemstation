# src/api/search_client.py (终极兼容版 - 自动适配)

import os
from src.core.settings import settings

# --- 智能导入，依次尝试所有已知的客户端类名 ---
try:
    # 方案1：尝试最新版
    from serpapi import SerpApiClient
    CLIENT_CLASS = SerpApiClient
    CLIENT_TYPE = "SerpApiClient"
    print("[Search Client] 检测到 SerpApi 新版接口 (SerpApiClient)。")
except ImportError:
    try:
        # 方案2：尝试中间版本
        from serpapi import GoogleSearch
        CLIENT_CLASS = GoogleSearch
        CLIENT_TYPE = "GoogleSearch"
        print("[Search Client] 检测到 SerpApi 旧版接口 (GoogleSearch)。")
    except ImportError:
        try:
            # 方案3：尝试更旧的版本
            from serpapi import Client
            CLIENT_CLASS = Client
            CLIENT_TYPE = "Client"
            print("[Search Client] 检测到 SerpApi 更旧的接口 (Client)。")
        except ImportError:
            # 如果都失败，设置一个哨兵值
            CLIENT_CLASS = None
            CLIENT_TYPE = "Unknown"
            print("!!! [Search Client] 警告: 无法从已安装的 serpapi 库中找到任何可用的客户端类。")


def perform_search(query: str, max_results: int = 3) -> str:
    """
    使用 SerpApi 进行 Google 搜索并返回增强的摘要。
    此版本能自动适配 SerpApi 的多个主要版本。
    """
    if not CLIENT_CLASS:
        return "联网搜索失败：无法从已安装的 serpapi 库中找到可用的客户端。"

    SERPAPI_API_KEY = settings.get('API/serpapi_api_key')
    if not SERPAPI_API_KEY:
        return "联网搜索失败：请在“设置”中配置SerpApi API Key。"

    print(f"--- [Search Client] 正在使用 {CLIENT_TYPE} 搜索: '{query}' ---")
    
    try:
        # --- 根据不同的客户端类型，使用不同的调用方式 ---
        if CLIENT_TYPE == "SerpApiClient":
            params = {"q": query, "engine": "google", "hl": "zh-cn", "gl": "cn", "api_key": SERPAPI_API_KEY}
            client = CLIENT_CLASS(params)
            results = client.get_dict()
        elif CLIENT_TYPE == "Client":
            client = CLIENT_CLASS(SERPAPI_API_KEY)
            params = {"q": query, "engine": "google", "hl": "zh-cn", "gl": "cn"}
            results = client.search(params)
        elif CLIENT_TYPE == "GoogleSearch":
            params = {"q": query, "api_key": SERPAPI_API_KEY, "engine": "google", "hl": "zh-cn", "gl": "cn"}
            search = CLIENT_CLASS(params)
            results = search.get_dict()
        else:
            raise Exception("未知的SerpApi客户端类型。")

        if "error" in results:
            raise Exception(results["error"])

        # --- 后续的解析逻辑，与版本无关，保持不变 ---
        summary_parts = []

        if "answer_box" in results:
            answer_box = results["answer_box"]
            title = answer_box.get("title", "")
            snippet = answer_box.get("snippet") or answer_box.get("answer")
            if snippet:
                summary_parts.append(f"直接答案 ({title}):\n{snippet}")

        if not summary_parts and "knowledge_graph" in results:
            kg = results["knowledge_graph"]
            title = kg.get("title", "")
            description = kg.get("description")
            if description:
                source = kg.get("source", {}).get("name", "未知来源")
                summary_parts.append(f"知识图谱 ({title}):\n{description} (来源: {source})")

        if "organic_results" in results:
            organic_results = results["organic_results"]
            for i, res in enumerate(organic_results[:max_results]):
                if len(summary_parts) >= max_results: break
                title = res.get("title", "无标题")
                snippet = res.get("snippet", "无摘要")
                link = res.get("link", "#")
                summary_parts.append(f"{i+1}. {title}\n摘要: {snippet}\n链接: {link}")
        
        if not summary_parts:
            return f"关于“{query}”的搜索没有找到明确的结果。"

        return "根据网络搜索结果：\n\n" + "\n\n".join(summary_parts)

    except Exception as e:
        print(f"!!! [Search Client] SerpApi 请求或解析失败: {e}")
        return f"联网搜索功能暂时无法使用，错误: {e}"


# --- 用于独立测试此模块的函数 ---
if __name__ == '__main__':
    # 在终端直接运行 python src/api/search_client.py 来测试
    print("--- 测试 SerpApi 客户端 ---")
    
    # 请确保你在 config.ini 中已经配置了 serpapi_api_key
    
    test_query = "今天北京天气怎么样"
    print(f"\n正在搜索: '{test_query}'")
    search_summary = perform_search(test_query)
    print("\n--- 搜索结果摘要 ---")
    print(search_summary)
    print("----------------------\n")