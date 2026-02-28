"""
新闻抓取模块
支持 Finnhub API 和 yfinance 作为备用数据源
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List
import pytz

import finnhub
import yfinance as yf
from requests.exceptions import RequestException


def _parse_finnhub_date(timestamp: int) -> str:
    """将 Finnhub 时间戳转换为可读日期字符串"""
    dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
    return dt.strftime("%Y-%m-%d %H:%M")


def _is_within_days(published_date: str, days_back: int) -> bool:
    """检查新闻是否在指定的天数范围内"""
    try:
        news_date = datetime.strptime(published_date, "%Y-%m-%d %H:%M")
        news_date = news_date.replace(tzinfo=pytz.UTC)
        now = datetime.now(pytz.UTC)
        cutoff = now - timedelta(days=days_back)
        return news_date >= cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
    except Exception:
        return True  # 如果解析失败，保留新闻


def fetch_from_finnhub(symbol: str, api_key: str, max_news: int = 20) -> List[Dict]:
    """
    从 Finnhub API 抓取股票新闻

    Args:
        symbol: 股票代码
        api_key: Finnhub API 密钥
        max_news: 最多返回的新闻条数

    Returns:
        新闻列表，每条新闻包含 title, source, published_at, summary, url
    """
    client = finnhub.Client(api_key=api_key)

    try:
        # 获取一般新闻（category: general）
        news_data = client.company_news(symbol, _from="2024-01-01", to="2030-01-01")

        if not news_data:
            return []

        news_list = []
        for item in news_data[:max_news]:
            news_list.append({
                "title": item.get("headline", ""),
                "source": item.get("source", ""),
                "published_at": _parse_finnhub_date(item.get("datetime", 0)),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
            })

        return news_list

    except Exception as e:
        print(f"Finnhub API 请求失败 ({symbol}): {e}")
        return []


def fetch_from_yfinance(symbol: str, max_news: int = 20) -> List[Dict]:
    """
    从 yfinance 抓取股票新闻（备用数据源）

    Args:
        symbol: 股票代码
        max_news: 最多返回的新闻条数

    Returns:
        新闻列表
    """
    try:
        ticker = yf.Ticker(symbol)
        news_data = ticker.news

        if not news_data:
            return []

        news_list = []
        for item in news_data[:max_news]:
            # yfinance 的新闻字段结构不同
            published = item.get("providerPublishTime", 0)
            if published:
                published_str = datetime.fromtimestamp(published, tz=pytz.UTC).strftime("%Y-%m-%d %H:%M")
            else:
                published_str = ""

            news_list.append({
                "title": item.get("title", ""),
                "source": item.get("publisher", ""),
                "published_at": published_str,
                "summary": "",
                "url": item.get("link", ""),
            })

        return news_list

    except Exception as e:
        print(f"yfinance 请求失败 ({symbol}): {e}")
        return []


def get_stock_info(symbol: str) -> Dict:
    """
    获取股票基本信息（公司名称、当前价格、涨跌幅、8周高低价等）

    Args:
        symbol: 股票代码

    Returns:
        包含 company_name, current_price, change, change_percent, week_8_low, week_8_high 的字典
    """
    try:
        import pandas as pd
        from datetime import datetime, timedelta

        ticker = yf.Ticker(symbol)
        info = ticker.info

        company_name = info.get("longName", symbol)
        previous_close = info.get("previousClose", 0)
        current_price = info.get("currentPrice", previous_close)

        if previous_close and previous_close > 0:
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
        else:
            change = 0
            change_percent = 0
            current_price = 0

        # 获取8周（约56个交易日）的历史数据来计算高低价
        week_8_low = None
        week_8_high = None
        try:
            # 获取过去3个月的历史数据以确保覆盖8周
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

            hist = ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))

            if not hist.empty:
                # 取最近约56个交易日（8周）
                recent_hist = hist.tail(56)
                week_8_low = round(float(recent_hist['Low'].min()), 2)
                week_8_high = round(float(recent_hist['High'].max()), 2)
        except Exception as e:
            print(f"  获取历史数据失败 ({symbol}): {e}")

        return {
            "company_name": company_name,
            "current_price": round(current_price, 2) if current_price else None,
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "week_8_low": week_8_low,
            "week_8_high": week_8_high,
        }

    except Exception as e:
        print(f"获取股票信息失败 ({symbol}): {e}")
        return {
            "company_name": symbol,
            "current_price": None,
            "change": 0,
            "change_percent": 0,
            "week_8_low": None,
            "week_8_high": None,
        }


def fetch_news(symbols: List[str], days_back: int = 1, finnhub_api_key: str = None) -> Dict[str, List[Dict]]:
    """
    抓取多只股票的新闻

    Args:
        symbols: 股票代码列表
        days_back: 抓取最近几天的新闻
        finnhub_api_key: Finnhub API 密钥

    Returns:
        字典，键为股票代码，值为新闻列表
        {
            "AAPL": [
                {
                    "title": "Apple announces...",
                    "source": "Reuters",
                    "published_at": "2024-01-15 14:30",
                    "summary": "...",
                    "url": "https://..."
                }
            ],
            "TSLA": [...]
        }
    """
    result = {}

    for i, symbol in enumerate(symbols):
        symbol = symbol.strip().upper()
        print(f"正在抓取 {symbol} 的新闻...")

        news_list = []

        # 优先使用 Finnhub
        if finnhub_api_key:
            news_list = fetch_from_finnhub(symbol, finnhub_api_key)

            # Finnhub 免费版限速，添加延迟
            if i < len(symbols) - 1:
                time.sleep(1.1)

        # 如果 Finnhub 无数据，尝试 yfinance
        if not news_list:
            print(f"  Finnhub 无数据，尝试 yfinance...")
            news_list = fetch_from_yfinance(symbol)

        # 按日期过滤新闻
        if days_back > 0:
            news_list = [n for n in news_list if _is_within_days(n["published_at"], days_back)]

        result[symbol] = news_list
        print(f"  找到 {len(news_list)} 条新闻")

    return result


if __name__ == "__main__":
    # 测试代码
    import os
    api_key = os.getenv("FINNHUB_API_KEY")
    if api_key:
        news = fetch_news(["AMD", "NVDA"], days_back=1, finnhub_api_key=api_key)
        for symbol, news_list in news.items():
            print(f"\n{symbol}: {len(news_list)} 条新闻")
            for n in news_list[:3]:
                print(f"  - {n['title'][:50]}...")
