"""
AI 摘要模块
使用 Claude API 生成股票新闻的中文摘要
"""
import time
from datetime import datetime
from typing import Dict, List

from anthropic import Anthropic
from anthropic import APIError, APITimeoutError, RateLimitError, AuthenticationError


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


def _build_prompt(symbol: str, company_name: str, news_list: List[Dict], date: str, language: str = "zh", include_prediction: bool = False) -> str:
    """构建 Claude API 的提示词"""

    news_text = _build_news_list_text(news_list)

    if include_prediction:
        # 包含预测分析的完整版 prompt
        if language == "zh":
            prompt = f"""你是一位专业的股票分析师助手。以下是 {symbol}（{company_name}）在 {date} 的新闻列表：

{news_text}

请用中文生成一份简洁的每日分析报告，包含以下部分：
1. **重要事件**（2-4条，每条一句话）
2. **市场情绪**（正面/中性/负面，并简要说明原因）
3. **需要关注**（1-2个风险点或机会点）
4. **短期走势预测**
   - 预测方向：看涨/看跌/中性
   - 置信度：高/中/低
   - 关键因素：用1-2句话说明支撑此预测的核心因素

要求：
- 基于新闻进行客观分析，不做买卖建议
- 预测仅为技术分析参考，不构成投资建议
- 总字数控制在 300 字以内"""
        else:
            prompt = f"""You are a professional stock analyst assistant. Below is the news list for {symbol} ({company_name}) on {date}:

{news_text}

Please generate a concise daily analysis report in English, including:
1. **Key Events** (2-4 items, one sentence each)
2. **Market Sentiment** (Positive/Neutral/Negative, with brief reason)
3. **Watch List** (1-2 risk points or opportunities)
4. **Short-term Trend Prediction**
   - Direction: Bullish/Bearish/Neutral
   - Confidence: High/Medium/Low
   - Key Factors: 1-2 sentences supporting the prediction

Requirements:
- Objective analysis based on news, no buy/sell recommendations
- Prediction is for technical reference only, not investment advice
- Keep under 300 words"""
    else:
        # 简化版 prompt（原有逻辑）
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
    retry_delay: float = 3.0,
    include_prediction: bool = False,  # 新增：是否包含预测分析
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
        retry_delay: 重试延迟（秒），默认 3 秒
        include_prediction: 是否包含 AI 预测分析

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
    prompt = _build_prompt(symbol, company_name, news_list, date, language, include_prediction)

    # 重试机制
    last_error = None
    for attempt in range(max_retries):
        try:
            # 调用 Claude API
            client = Anthropic(api_key=api_key, base_url=base_url)

            # 根据是否使用代理 API 选择模型
            # 代理 API 通常支持更简单的模型名称
            if base_url and "anthropic.com" not in base_url:
                # 使用代理 API，尝试稳定的模型版本
                models_to_try = [
                    "claude-sonnet-4-20250514",
                    "claude-3-5-sonnet-20241022",
                ]
            else:
                # 官方 API，可以尝试更多版本
                models_to_try = [
                    "claude-sonnet-4-20250514",
                    "claude-sonnet-4-20250513",
                    "claude-3-5-sonnet-20241022",
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
                    # 如果是认证错误，不尝试其他模型
                    if "401" in str(e) or "Unauthorized" in str(e):
                        print(f"    ✗ {symbol} 模型 {model} 认证失败")
                        raise AuthenticationError(str(e))
                    print(f"    ⚠ {symbol} 模型 {model} 不可用，尝试下一个...")
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

        except AuthenticationError as e:
            # 401 错误 - 不再重试，直接失败
            error_detail = str(e)
            print(f"  ✗ {symbol} 认证失败 (401)")
            print(f"     可能原因：API Key 无效、已过期或配额用完")
            print(f"     详细信息：{error_detail[:100]}")
            # 401 错误不重试，直接返回
            return _format_error(symbol, company_name, language, f"认证失败: {error_detail[:80]}")

        except RateLimitError as e:
            last_error = e
            wait_time = retry_delay * (2 ** attempt)  # 指数退避: 2s, 4s, 8s
            print(f"  ⚠ {symbol} 速率限制，等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
            continue

        except APITimeoutError as e:
            last_error = e
            print(f"  ⚠ {symbol} 请求超时，重试 {attempt + 1}/{max_retries}...")
            time.sleep(retry_delay)
            continue

        except APIError as e:
            last_error = e
            error_str = str(e)
            # 检查是否是 401 相关错误
            if "401" in error_str or "Unauthorized" in error_str or "authentication" in error_str.lower():
                print(f"  ✗ {symbol} 认证失败: {error_str[:100]}")
                return _format_error(symbol, company_name, language, f"认证失败: {error_str[:80]}")
            print(f"  ✗ {symbol} API 错误: {error_str[:100]}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue

        except Exception as e:
            last_error = e
            error_str = str(e)
            # 检查是否是 401 相关错误
            if "401" in error_str:
                print(f"  ✗ {symbol} 认证失败: {error_str[:100]}")
                return _format_error(symbol, company_name, language, f"认证失败: {error_str[:80]}")
            print(f"  ✗ {symbol} 未知错误: {error_str[:100]}")
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


def get_stock_prediction(
    symbol: str,
    news_list: List[Dict],
    current_price: float = None,
    change_percent: float = None,
    date: str = None,
    api_key: str = None,
    base_url: str = None,
    language: str = "zh",
) -> str:
    """
    使用 AI 分析股票并给出短期走势预测

    Args:
        symbol: 股票代码
        news_list: 新闻列表
        current_price: 当前价格（可选）
        change_percent: 涨跌幅（可选）
        date: 目标日期
        api_key: Anthropic API 密钥
        base_url: API 基础 URL
        language: 语言 (zh/en)

    Returns:
        预测分析文本
    """
    if not api_key:
        return "⚠️ 缺少 API Key"

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    company_name = _get_company_name(symbol)

    # 构建预测分析 prompt
    news_text = _build_news_list_text(news_list[:10])  # 限制新闻数量

    if language == "zh":
        price_info = ""
        if current_price:
            price_info = f"\n当前价格: ${current_price:.2f}"
        if change_percent is not None:
            trend = "上涨" if change_percent >= 0 else "下跌"
            price_info += f" | 今日{trend}: {abs(change_percent):.2f}%"

        prompt = f"""你是一位专业的股票技术分析师。请分析以下股票的短期走势。

股票：{symbol}（{company_name}）{price_info}
日期：{date}

近期新闻：
{news_text}

请提供一份简洁的短期走势分析，包含以下内容：

**📊 走势预测**
- 方向：看涨 📈 / 看跌 📉 / 中立 ➡️
- 置信度：⭐⭐⭐ (高) / ⭐⭐ (中) / ⭐ (低)

**🔍 关键因素**
- 支撑此预测的 1-2 个核心因素

**⚠️ 风险提示**
- 可能改变走势的风险因素

**免责声明**：此分析仅供参考，不构成任何投资建议。股市有风险，投资需谨慎。

请保持简洁，总字数在 150 字以内。"""
    else:
        price_info = ""
        if current_price:
            price_info = f"\nCurrent Price: ${current_price:.2f}"
        if change_percent is not None:
            trend = "up" if change_percent >= 0 else "down"
            price_info += f" | Today {trend}: {abs(change_percent):.2f}%"

        prompt = f"""You are a professional stock technical analyst. Please analyze the short-term trend of the following stock.

Stock: {symbol} ({company_name}){price_info}
Date: {date}

Recent News:
{news_text}

Please provide a concise short-term trend analysis including:

**📊 Trend Prediction**
- Direction: Bullish 📈 / Bearish 📉 / Neutral ➡️
- Confidence: ⭐⭐⭐ (High) / ⭐⭐ (Medium) / ⭐ (Low)

**🔍 Key Factors**
- 1-2 core factors supporting this prediction

**⚠️ Risk Warning**
- Risk factors that could change the trend

**Disclaimer**: This analysis is for reference only and does not constitute investment advice.

Keep it concise, under 150 words."""

    try:
        client = Anthropic(api_key=api_key, base_url=base_url)

        # 优先使用稳定模型
        models_to_try = ["claude-3-5-sonnet-20241022", "claude-sonnet-4-20250514"]

        for model in models_to_try:
            try:
                message = client.messages.create(
                    model=model,
                    max_tokens=800,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=30.0
                )
                return message.content[0].text
            except APIError:
                continue

        return "预测分析生成失败，请稍后重试。"

    except Exception as e:
        return f"预测分析失败: {str(e)[:50]}"


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
