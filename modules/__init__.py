"""
股票新闻简报系统模块包
"""
from .news_fetcher import fetch_news
from .ai_summarizer import summarize_stock_news
from .email_sender import send_email
from .report_builder import build_html_report

__all__ = [
    "fetch_news",
    "summarize_stock_news",
    "send_email",
    "build_html_report",
]
