"""
股票新闻简报系统模块包
"""
from .news_fetcher import fetch_news, get_stock_info
from .ai_summarizer import summarize_stock_news, get_stock_prediction
from .email_sender import send_email
from .report_builder import build_html_report

__all__ = [
    "fetch_news",
    "get_stock_info",
    "summarize_stock_news",
    "get_stock_prediction",
    "send_email",
    "build_html_report",
]
