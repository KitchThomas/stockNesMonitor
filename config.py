"""
配置加载模块
从环境变量加载所有配置项
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """配置类，集中管理所有环境变量"""

    # Anthropic Claude API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

    # Finnhub API
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

    # Gmail 配置
    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

    # 收件人列表
    RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "").split(",")
    RECIPIENT_EMAILS = [email.strip() for email in RECIPIENT_EMAILS if email.strip()]

    # 股票代码列表
    STOCK_SYMBOLS = os.getenv("STOCK_SYMBOLS", "").split(",")
    STOCK_SYMBOLS = [symbol.strip().upper() for symbol in STOCK_SYMBOLS if symbol.strip()]

    # 推送时间配置（UTC）
    DIGEST_HOUR_UTC = int(os.getenv("DIGEST_HOUR_UTC", "23"))

    # 简报语言
    REPORT_LANGUAGE = os.getenv("REPORT_LANGUAGE", "zh")

    # 新闻抓取天数
    NEWS_LOOKBACK_DAYS = int(os.getenv("NEWS_LOOKBACK_DAYS", "1"))

    # 是否启用 AI 预测分析
    ENABLE_PREDICTION = os.getenv("ENABLE_PREDICTION", "true").lower() == "true"

    @classmethod
    def validate(cls):
        """验证必要的配置项是否存在"""
        errors = []

        if not cls.ANTHROPIC_API_KEY:
            errors.append("缺少 ANTHROPIC_API_KEY")
        if not cls.FINNHUB_API_KEY:
            errors.append("缺少 FINNHUB_API_KEY")
        if not cls.GMAIL_USER:
            errors.append("缺少 GMAIL_USER")
        if not cls.GMAIL_APP_PASSWORD:
            errors.append("缺少 GMAIL_APP_PASSWORD")
        if not cls.RECIPIENT_EMAILS:
            errors.append("缺少 RECIPIENT_EMAILS")
        if not cls.STOCK_SYMBOLS:
            errors.append("缺少 STOCK_SYMBOLS")

        if errors:
            raise ValueError(f"配置验证失败：\n" + "\n".join(f"  - {e}" for e in errors))

        return True


# 导出配置实例
config = Config()
