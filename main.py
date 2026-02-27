#!/usr/bin/env python3
"""
股票每日新闻简报系统 - 主入口
每天定时运行，抓取股票新闻，生成 AI 摘要，发送邮件报告
"""
import sys
from datetime import datetime, timedelta
from typing import Dict, List

from config import config
from modules.news_fetcher import fetch_news, get_stock_info
from modules.ai_summarizer import summarize_stock_news
from modules.report_builder import build_html_report
from modules.email_sender import send_email


def get_target_date() -> str:
    """获取目标日期（昨天）"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def run_digest(is_test: bool = False, test_symbol: str = None) -> Dict:
    """
    执行完整的简报生成流程

    Args:
        is_test: 是否为测试模式（只处理第一只股票）
        test_symbol: 测试模式下指定的股票代码

    Returns:
        执行结果字典
    """
    print("=" * 60)
    print("📈 股票每日新闻简报系统")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 验证配置
    try:
        config.validate()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置错误: {e}")
        return {"success": False, "error": str(e)}

    # 确定要处理的股票列表
    if is_test and test_symbol:
        symbols = [test_symbol.upper()]
        print(f"🧪 测试模式：只处理 {test_symbol}")
    elif is_test and config.STOCK_SYMBOLS:
        symbols = [config.STOCK_SYMBOLS[0]]
        print(f"🧪 测试模式：只处理 {symbols[0]}")
    else:
        symbols = config.STOCK_SYMBOLS
        print(f"📊 处理股票: {', '.join(symbols)}")

    print()

    # 步骤 1: 抓取新闻
    print("📡 步骤 1/5: 抓取股票新闻...")
    target_date = get_target_date()
    print(f"目标日期: {target_date}")

    try:
        news_data = fetch_news(
            symbols=symbols,
            days_back=config.NEWS_LOOKBACK_DAYS,
            finnhub_api_key=config.FINNHUB_API_KEY
        )

        total_news = sum(len(news) for news in news_data.values())
        print(f"✓ 抓取完成，共 {total_news} 条新闻")
    except Exception as e:
        print(f"✗ 新闻抓取失败: {e}")
        return {"success": False, "error": f"新闻抓取失败: {e}"}

    print()

    # 步骤 2: 获取股票信息
    print("📈 步骤 2/5: 获取股票信息...")
    stock_info = {}

    for symbol in symbols:
        try:
            info = get_stock_info(symbol)
            stock_info[symbol] = info
            print(f"  {symbol}: {info['company_name']} ({info['change_percent']:+.2f}%)")
        except Exception as e:
            print(f"  {symbol}: 信息获取失败 - {e}")
            stock_info[symbol] = {
                "company_name": symbol,
                "change": 0,
                "change_percent": 0,
            }

    print("✓ 股票信息获取完成")
    print()

    # 步骤 3: 生成 AI 摘要
    print("🤖 步骤 3/5: 生成 AI 摘要...")
    summaries = {}

    for symbol in symbols:
        news_list = news_data.get(symbol, [])
        print(f"  正在生成 {symbol} 的摘要...")

        try:
            summary = summarize_stock_news(
                symbol=symbol,
                news_list=news_list,
                date=target_date,
                api_key=config.ANTHROPIC_API_KEY,
                base_url=config.ANTHROPIC_BASE_URL,
                language=config.REPORT_LANGUAGE
            )
            summaries[symbol] = summary
            print(f"    ✓ {symbol} 摘要生成完成")
        except Exception as e:
            print(f"    ✗ {symbol} 摘要生成失败: {e}")
            # 添加一个错误占位符
            if config.REPORT_LANGUAGE == "zh":
                summaries[symbol] = f"## {symbol}\n\n摘要生成失败: {str(e)}"
            else:
                summaries[symbol] = f"## {symbol}\n\nSummary generation failed: {str(e)}"

    print("✓ AI 摘要生成完成")
    print()

    # 步骤 4: 构建 HTML 报告
    print("📄 步骤 4/5: 构建 HTML 报告...")

    try:
        html_report = build_html_report(
            summaries=summaries,
            stock_info=stock_info,
            news_data=news_data,
            language=config.REPORT_LANGUAGE
        )
        print("✓ HTML 报告构建完成")
    except Exception as e:
        print(f"✗ 报告构建失败: {e}")
        return {"success": False, "error": f"报告构建失败: {e}"}

    print()

    # 步骤 5: 发送邮件
    print("📧 步骤 5/5: 发送邮件...")

    # 邮件主题
    if config.REPORT_LANGUAGE == "zh":
        subject = f"📈 每日股票简报 | {target_date}"
        if is_test:
            subject = f"[TEST] {subject}"
    else:
        subject = f"📈 Daily Stock Brief | {target_date}"
        if is_test:
            subject = f"[TEST] {subject}"

    try:
        email_sent = send_email(
            subject=subject,
            html_content=html_report,
            recipients=config.RECIPIENT_EMAILS,
            sender=config.GMAIL_USER,
            app_password=config.GMAIL_APP_PASSWORD
        )

        if email_sent:
            print("✓ 邮件发送成功")
        else:
            print("✗ 邮件发送失败")
            return {"success": False, "error": "邮件发送失败"}

    except Exception as e:
        print(f"✗ 邮件发送异常: {e}")
        return {"success": False, "error": f"邮件发送异常: {e}"}

    print()
    print("=" * 60)
    print("✅ 简报生成完成！")
    print("=" * 60)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"处理股票: {', '.join(symbols)}")
    print(f"新闻总数: {total_news}")
    print(f"收件人: {', '.join(config.RECIPIENT_EMAILS)}")

    return {
        "success": True,
        "symbols": symbols,
        "total_news": total_news,
        "recipients": config.RECIPIENT_EMAILS,
    }


def main():
    """主入口函数"""
    is_test = "--test" in sys.argv

    if is_test:
        print("⚠️  测试模式：只处理第一只股票")
        print()

    result = run_digest(is_test=is_test)

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
