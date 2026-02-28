"""
报告构建模块
将多只股票的摘要整合成 HTML 邮件报告
"""
from datetime import datetime
from typing import Dict, List
from jinja2 import Template


# HTML 邮件模板
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }
        .header .date {
            margin-top: 10px;
            opacity: 0.9;
            font-size: 14px;
        }
        .header .symbols {
            margin-top: 10px;
            opacity: 0.9;
            font-size: 12px;
        }
        .content {
            padding: 20px;
        }
        .stock-card {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            background-color: #fafafa;
        }
        .stock-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e0e0e0;
        }
        .stock-name {
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }
        .stock-price-info {
            text-align: right;
        }
        .stock-change {
            font-size: 14px;
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        .stock-change.positive {
            background-color: #e8f5e9;
            color: #2e7d32;
        }
        .stock-change.negative {
            background-color: #ffebee;
            color: #c62828;
        }
        .stock-change.neutral {
            background-color: #f5f5f5;
            color: #616161;
        }
        .stock-current-price {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 4px;
        }
        .stock-range-info {
            font-size: 11px;
            color: #666;
            margin-top: 4px;
        }
        .range-high {
            color: #2e7d32;
        }
        .range-low {
            color: #c62828;
        }
        .summary-content {
            font-size: 14px;
            line-height: 1.6;
            color: #555;
        }
        .summary-content h3 {
            color: #333;
            font-size: 14px;
            margin-top: 15px;
            margin-bottom: 8px;
        }
        .summary-content ul {
            margin: 0;
            padding-left: 20px;
        }
        .summary-content li {
            margin-bottom: 5px;
        }
        .news-links {
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
        }
        .news-links h4 {
            font-size: 12px;
            color: #666;
            margin: 0 0 8px 0;
            text-transform: uppercase;
        }
        .news-links a {
            display: block;
            font-size: 12px;
            color: #667eea;
            text-decoration: none;
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .news-links a:hover {
            text-decoration: underline;
        }
        .prediction-box {
            background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-top: 15px;
            border-radius: 4px;
        }
        .prediction-title {
            font-size: 13px;
            font-weight: 600;
            color: #667eea;
            margin: 0 0 10px 0;
            display: flex;
            align-items: center;
        }
        .prediction-content {
            font-size: 13px;
            line-height: 1.5;
            color: #555;
        }
        .prediction-content strong {
            color: #333;
        }
        .trend-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }
        .trend-bullish {
            background-color: #e8f5e9;
            color: #2e7d32;
        }
        .trend-bearish {
            background-color: #ffebee;
            color: #c62828;
        }
        .trend-neutral {
            background-color: #fff3e0;
            color: #e65100;
        }
        .disclaimer {
            font-size: 11px;
            color: #999;
            font-style: italic;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #ddd;
        }
        .footer {
            background-color: #f5f5f5;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #888;
        }
        .no-news {
            text-align: center;
            padding: 40px;
            color: #888;
        }
        @media only screen and (max-width: 480px) {
            .container {
                border-radius: 0;
            }
            .header {
                padding: 20px;
            }
            .header h1 {
                font-size: 20px;
            }
            .stock-card {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="date">{{ date_str }}</div>
            <div class="symbols">覆盖股票：{{ symbols }}</div>
        </div>

        <div class="content">
            {% if stocks %}
                {% for stock in stocks %}
                <div class="stock-card">
                    <div class="stock-header">
                        <div class="stock-name">{{ stock.symbol }}
                            {% if stock.company_name and stock.company_name != stock.symbol %}
                            <span style="font-size: 14px; color: #666; font-weight: normal;">（{{ stock.company_name }}）</span>
                            {% endif %}
                        </div>
                        <div class="stock-change {{ stock.change_class }}">
                            {% if stock.change_percent > 0 %}+{% endif %}{{ stock.change_percent }}%
                        </div>
                    </div>

                    {% if stock.summary %}
                    <div class="summary-content">
                        {{ stock.summary_html }}
                    </div>
                    {% else %}
                    <div class="no-news">暂无新闻</div>
                    {% endif %}

                    {% if stock.prediction %}
                    <div class="prediction-box">
                        <div class="prediction-title">
                            🔮 AI 走势预测
                            {% if stock.trend_badge %}
                            <span class="trend-badge {{ stock.trend_class }}">{{ stock.trend_badge }}</span>
                            {% endif %}
                        </div>
                        <div class="prediction-content">
                            {{ stock.prediction_html }}
                        </div>
                    </div>
                    {% endif %}

                    {% if stock.news_links %}
                    <div class="news-links">
                        <h4>相关新闻 ({{ stock.news_count }} 条)</h4>
                        {% for link in stock.news_links[:5] %}
                        <a href="{{ link.url }}" target="_blank">{{ link.title }}</a>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <div class="no-news">
                    <p>今日没有抓取到任何新闻。</p>
                    <p style="font-size: 12px; margin-top: 10px;">可能是 API 额度已用完或网络问题。</p>
                </div>
            {% endif %}
        </div>

        <div class="footer">
            <p>本简报由 AI 自动生成，仅供参考，不构成投资建议。</p>
            <p style="margin-top: 8px;">{{ generation_time }}</p>
        </div>
    </div>
</body>
</html>
"""


def _markdown_to_html(markdown_text: str) -> str:
    """简单的 Markdown 转 HTML"""
    if not markdown_text:
        return ""

    html = markdown_text

    # 标题转换
    html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", 1)

    # 粗体
    html = html.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
    html = html.replace("**", "<strong>", 1).replace("**", "</strong>", 1)

    # 列表项
    lines = html.split("\n")
    result_lines = []
    in_list = False

    for line in lines:
        line = line.strip()
        if line.startswith("- "):
            if not in_list:
                result_lines.append("<ul>")
                in_list = True
            result_lines.append(f"<li>{line[2:]}</li>")
        elif line.startswith(("* ", "1. ", "2. ", "3. ")):
            if not in_list:
                result_lines.append("<ul>")
                in_list = True
            content = line.split(" ", 1)[1] if " " in line else line
            result_lines.append(f"<li>{content}</li>")
        else:
            if in_list:
                result_lines.append("</ul>")
                in_list = False
            if line:
                result_lines.append(f"<p>{line}</p>")

    if in_list:
        result_lines.append("</ul>")

    return "\n".join(result_lines)


def _get_change_class(change_percent: float) -> str:
    """根据涨跌幅返回 CSS 类名"""
    if change_percent > 0:
        return "positive"
    elif change_percent < 0:
        return "negative"
    return "neutral"


def _extract_trend_badge(prediction_text: str) -> str:
    """从预测文本中提取走势标签"""
    if not prediction_text:
        return None

    text_lower = prediction_text.lower()

    # 中文关键词
    if "看涨" in prediction_text or "📈" in prediction_text:
        return "看涨 📈"
    elif "看跌" in prediction_text or "📉" in prediction_text:
        return "看跌 📉"
    elif "中立" in prediction_text or "➡️" in prediction_text:
        return "中立 ➡️"

    # 英文关键词
    if "bullish" in text_lower:
        return "Bullish 📈"
    elif "bearish" in text_lower:
        return "Bearish 📉"
    elif "neutral" in text_lower:
        return "Neutral ➡️"

    return None


def _extract_trend_class(prediction_text: str) -> str:
    """从预测文本中提取走势 CSS 类名"""
    if not prediction_text:
        return None

    text_lower = prediction_text.lower()

    if "看涨" in prediction_text or "bullish" in text_lower or "📈" in prediction_text:
        return "trend-bullish"
    elif "看跌" in prediction_text or "bearish" in text_lower or "📉" in prediction_text:
        return "trend-bearish"
    elif "中立" in prediction_text or "neutral" in text_lower or "➡️" in prediction_text:
        return "trend-neutral"

    return None


def build_html_report(
    summaries: Dict[str, str],
    stock_info: Dict[str, Dict],
    news_data: Dict[str, List[Dict]],
    predictions: Dict[str, str] = None,
    language: str = "zh",
) -> str:
    """
    构建完整的 HTML 报告

    Args:
        summaries: 股票摘要字典 {symbol: markdown_summary}
        stock_info: 股票信息字典 {symbol: {company_name, change, change_percent}}
        news_data: 新闻数据字典 {symbol: [news_list]}
        predictions: AI 预测分析字典 {symbol: prediction_text} (可选)
        language: 报告语言

    Returns:
        HTML 格式的报告
    """
    now = datetime.now()

    # 格式化日期
    if language == "zh":
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        date_str = now.strftime(f"%Y年%m月%d日（星期{weekdays[now.weekday()]}）")
        title = "📈 每日股票简报"
    else:
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        date_str = now.strftime(f"%B %d, %Y ({weekdays[now.weekday()]})")
        title = "📈 Daily Stock Brief"

    # 准备股票数据
    stocks = []
    for symbol in summaries.keys():
        info = stock_info.get(symbol, {})
        news_list = news_data.get(symbol, [])

        # 准备新闻链接
        news_links = []
        for news in news_list[:10]:
            if news.get("url"):
                news_links.append({
                    "title": news.get("title", "查看详情"),
                    "url": news["url"]
                })

        stocks.append({
            "symbol": symbol,
            "company_name": info.get("company_name", symbol),
            "change_percent": info.get("change_percent", 0),
            "change_class": _get_change_class(info.get("change_percent", 0)),
            "summary_html": _markdown_to_html(summaries.get(symbol, "")),
            "summary": summaries.get(symbol, ""),
            "news_links": news_links,
            "news_count": len(news_list),
            "prediction": predictions.get(symbol) if predictions else None,
            "prediction_html": _markdown_to_html(predictions.get(symbol)) if predictions and predictions.get(symbol) else None,
            "trend_badge": _extract_trend_badge(predictions.get(symbol)) if predictions and predictions.get(symbol) else None,
            "trend_class": _extract_trend_class(predictions.get(symbol)) if predictions and predictions.get(symbol) else None,
        })

    # 准备股票符号列表
    symbols = " | ".join(summaries.keys())

    # 渲染模板
    template = Template(EMAIL_TEMPLATE)
    html = template.render(
        title=title,
        date_str=date_str,
        symbols=symbols,
        stocks=stocks,
        generation_time=now.strftime("%Y-%m-%d %H:%M:%S"),
    )

    return html


if __name__ == "__main__":
    # 测试代码
    test_summaries = {
        "AMD": "## AMD\n\n- 重要事件：AMD 发布新款 AI 芯片\n- 市场情绪：正面，投资者对新产品反应热烈",
        "NVDA": "## NVDA\n\n- 重要事件：英伟达股价创新高",
    }

    test_info = {
        "AMD": {"company_name": "Advanced Micro Devices", "change": 2.5, "change_percent": 3.2},
        "NVDA": {"company_name": "NVIDIA Corporation", "change": -10.5, "change_percent": -1.5},
    }

    test_news = {
        "AMD": [
            {"title": "AMD Announces New AI Chip", "url": "https://example.com/1"},
            {"title": "AMD Stock Rises", "url": "https://example.com/2"},
        ],
        "NVDA": [
            {"title": "NVIDIA Hits Record High", "url": "https://example.com/3"},
        ],
    }

    html = build_html_report(test_summaries, test_info, test_news)
    print(html)
