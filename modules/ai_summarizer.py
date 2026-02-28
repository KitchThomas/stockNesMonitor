"""
AI 摘要模块
使用 Claude API 生成股票新闻的中文摘要
"""
import time
from datetime import datetime
from typing import Dict, List

from anthropic import Anthropic
from anthropic import APIError, APITimeoutError, RateLimitError


def _build_news_list_text(news_list: List[Dict], max_items: int = 15) -> str:
    """将新闻列表格式化为文本"""
    if not news_list:
        return "今日无相关新闻。"

    news_items = []
    for i, news in enumerate(news_list[:max_items], 1):
        news_items.append(f"{i}. 标题：{news.get('title', '')}")
        if news.get('summary'):
            news_items.append(f"   摘要：{news.get('summary', '')}")
        news_items.append(f"   来源：{news.get('source', '')} | 时间：{news.get('published_at', '')}")
        news_items.append("")

    return "\n".join(news_items)


def _get_company_name(symbol: str) -> str:
    """获取公司名称（简化版）"""
    # 可以从 yfinance 获取，这里先返回股票代码
    return symbol


def _build_prompt(symbol: str, company_name: str, news_list: List[Dict], date: str, language: str = "zh") -> str:
    """构建 Claude API 的提示词"""

    news_text = _build_news_list_text(news_list)

    if language == "zh":
        prompt = f"""你是一位专业的股票分析师助手。以下是 {symbol}（{company_name}）在 {date} 的新闻列表：

{news_text}

请用中文生成一份简洁的每日简报，包含以下部分：
1. **重要事件**（2-4条，每条一句话）
2. **市场情绪**（正面/中性/负面，并简要说明原因）
3. **需要关注**（1-2个风险点或机会点）

要求：
- 简洁客观，不做投资建议
- 如果新闻较少或不重要，直接说明"今日无重大事件"
- 总字数控制在 200 字以内"""
    else:
        prompt = f"""You are a professional stock analyst assistant. Below is the news list for {symbol} ({company_name}) on {date}:

{news_text}

Please generate a concise daily brief in English, including:
1. **Key Events** (2-4 items, one sentence each)
2. **Market Sentiment** (Positive/Neutral/Negative, with brief reason)
3. **Watch List** (1-2 risk points or opportunities)

Requirements:
- Concise and objective, no investment advice
- If news is limited or insignificant, state "No major events today"
- Keep under 200 words"""

    return prompt


def summarize_stock_news(
    symbol: str,
    news_list: List[Dict],
    date: str = None,
    api_key: str = None,
    base_url: str = None,
    language: str = "zh",
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> str:
    """
    使用 Claude API 生成股票新闻摘要

    Args:
        symbol: 股票代码
        news_list: 新闻列表
        date: 目标日期，格式 YYYY-MM-DD
        api_key: Anthropic API 密钥
        base_url: API 基础 URL
        language: 摘要语言 (zh/en)
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）

    Returns:
        Markdown 格式的摘要字符串
    """
    if not api_key:
        error_msg = "缺少 Anthropic API Key"
        print(f"  ✗ {symbol}: {error_msg}")
        return _format_error(symbol, symbol, language, error_msg)

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    company_name = _get_company_name(symbol)

    # 如果没有新闻，返回预设消息
    if not news_list:
        if language == "zh":
            return f"## {symbol}（{company_name}）\n\n今日无重大新闻事件。"
        else:
            return f"## {symbol} ({company_name})\n\nNo major news events today."

    # 构建 Prompt
    prompt = _build_prompt(symbol, company_name, news_list, date, language)

    # 重试机制
    last_error = None
    for attempt in range(max_retries):
        try:
            # 调用 Claude API
            client = Anthropic(api_key=api_key, base_url=base_url)

            # 尝试多个可能的模型名称
            models_to_try = [
                "claude-sonnet-4-20250514",  # 尝试新版本
                "claude-sonnet-4-20250513",  # 备选版本
                "claude-3-5-sonnet-20241022",  # 稳定版本
                "claude-3-5-sonnet-20240620",  # 较旧稳定版本
            ]

            message = None
            model_error = None

            for model in models_to_try:
                try:
                    message = client.messages.create(
                        model=model,
                        max_tokens=1000,
                        temperature=0.3,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }],
                        timeout=30.0
                    )
                    print(f"    ✓ {symbol} 使用模型 {model} 成功")
                    break
                except APIError as e:
                    model_error = e
                    print(f"    ⚠ {symbol} 模型 {model} 失败: {str(e)[:50]}...")
                    continue

            if message is None:
                raise model_error or Exception("所有模型尝试失败")

            # 提取回复内容
            summary = message.content[0].text

            # 添加标题
            if language == "zh":
                title = f"## {symbol}（{company_name}）"
            else:
                title = f"## {symbol} ({company_name})"

            # API 调用之间添加延迟，避免速率限制
            time.sleep(retry_delay)

            return f"{title}\n\n{summary}"

        except RateLimitError as e:
            last_error = e
            print(f"  ⚠ {symbol} 速率限制，等待 {retry_delay * (attempt + 1)} 秒后重试...")
            time.sleep(retry_delay * (attempt + 1))
            continue

        except APITimeoutError as e:
            last_error = e
            print(f"  ⚠ {symbol} 请求超时，重试 {attempt + 1}/{max_retries}...")
            time.sleep(retry_delay)
            continue

        except APIError as e:
            last_error = e
            print(f"  ✗ {symbol} API 错误: {str(e)[:100]}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue

        except Exception as e:
            last_error = e
            print(f"  ✗ {symbol} 未知错误: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
            break

    # 所有重试都失败
    error_msg = f"API 调用失败: {type(last_error).__name__}: {str(last_error)[:100] if last_error else 'Unknown error'}"
    print(f"  ✗ {symbol} {error_msg}")
    return _format_error(symbol, company_name, language, error_msg)


def _format_error(symbol: str, company_name: str, language: str, error_msg: str) -> str:
    """格式化错误消息"""
    if language == "zh":
        return f"## {symbol}（{company_name}）\n\n⚠️ 摘要生成失败\n\n错误信息：{error_msg}\n\n请稍后重试。"
    else:
        return f"## {symbol} ({company_name})\n\n⚠️ Summary generation failed\n\nError: {error_msg}\n\nPlease try again later."


if __name__ == "__main__":
    # 测试代码
    import os
    test_news = [
        {
            "title": "AMD Announces New AI Chip",
            "summary": "Advanced Micro Devices unveiled its latest AI accelerator chip.",
            "source": "Reuters",
            "published_at": "2024-01-15 10:30",
            "url": "https://example.com/1"
        },
        {
            "title": "AMD Stock Rises on Positive Analyst Report",
            "summary": "Several analysts upgraded AMD's price target.",
            "source": "Bloomberg",
            "published_at": "2024-01-15 14:00",
            "url": "https://example.com/2"
        }
    ]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    if api_key:
        summary = summarize_stock_news(
            "AMD",
            test_news,
            date="2024-01-15",
            api_key=api_key,
            base_url=base_url
        )
        print(summary)
