# chem_assistant/utils/translator.py

import translators as ts
import asyncio

async def translate_cn_to_en_chemical(cn_name: str) -> str | None:
    """
    使用 'translators' 库和【百度翻译】引擎将中文名翻译为英文。
    这是一个健壮且可靠的方法。

    Args:
        cn_name: 中文化学名称.

    Returns:
        翻译后的英文名称，如果失败则返回 None.
    """
    if not cn_name:
        return None
    try:
        # `ts.translate_text` 是一个同步函数，在异步代码中调用它会阻塞事件循环。
        # 我们使用 `asyncio.to_thread` 把它放到一个单独的线程中运行，
        # 这样就不会阻塞我们的GUI。这是现代Python中处理这类混合代码的标准做法。
        translated_text = await asyncio.to_thread(
            ts.translate_text,
            query_text=cn_name,
            translator='baidu',  # <-- 使用百度翻译，稳定可靠！
            from_language='auto',
            to_language='en'
        )
        print(f"DEBUG (Baidu Translate): '{cn_name}' -> '{translated_text}'")
        return translated_text
    except Exception as e:
        # 捕获 `translators` 库可能抛出的任何异常
        print(f"百度翻译时发生错误: {e}")
        return None


