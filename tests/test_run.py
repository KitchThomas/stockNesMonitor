#!/usr/bin/env python3
"""
一键测试脚本
用于验证整个流程是否正常工作

测试模式：
1. 只抓取第一只股票（节省 API 额度）
2. 生成摘要并打印到控制台
3. 发送测试邮件（主题前缀加 [TEST]）

运行方式：
    python tests/test_run.py
    或
    python main.py --test
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from modules.news_fetcher import fetch_news, get_stock_info
from modules.ai_summarizer import summarize_stock_news
from modules.report_builder import build_html_report
from modules.email_sender import send_email


def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("测试 1/5: 配置加载")
    print("=" * 60)

    try:
        config.validate()
        print("✓ 配置验证通过")
        print(f"  - 股票数量: {len(config.STOCK_SYMBOLS)}")
        print(f"  - 股票列表: {', '.join(config.STOCK_SYMBOLS)}")
        print(f"  - 收件人: {', '.join(config.RECIPIENT_EMAILS)}")
        print(f"  - 语言: {config.REPORT_LANGUAGE}")
        return True
    except ValueError as e:
        print(f"✗ 配置错误: {e}")
        return False


def test_news_fetcher():
    """测试新闻抓取"""
    print("\n" + "=" * 60)
    print("测试 2/5: 新闻抓取")
    print("=" * 60)

    if not config.STOCK_SYMBOLS:
        print("✗ 没有配置股票代码")
        return False

    test_symbol = config.STOCK_SYMBOLS[0]
    print(f"测试股票: {test_symbol}")

    try:
        news_data = fetch_news(
            symbols=[test_symbol],
            days_back=1,
            finnhub_api_key=config.FINNHUB_API_KEY
        )

        news_list = news_data.get(test_symbol, [])
        print(f"✓ 抓取到 {len(news_list)} 条新闻")

        for i, news in enumerate(news_list[:3], 1):
            print(f"  {i}. {news.get('title', 'N/A')[:60]}...")

        return news_data

    except Exception as e:
        print(f"✗ 新闻抓取失败: {e}")
        return None


def test_stock_info():
    """测试股票信息获取"""
    print("\n" + "=" * 60)
    print("测试 3/5: 股票信息")
    print("=" * 60)

    if not config.STOCK_SYMBOLS:
        print("✗ 没有配置股票代码")
        return None

    test_symbol = config.STOCK_SYMBOLS[0]
    print(f"测试股票: {test_symbol}")

    try:
        info = get_stock_info(test_symbol)
        print(f"✓ 获取成功")
        print(f"  - 公司名称: {info['company_name']}")
        print(f"  - 涨跌幅: {info['change_percent']:+.2f}%")
        return {test_symbol: info}
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        return None


def test_ai_summarizer(news_data):
    """测试 AI 摘要生成"""
    print("\n" + "=" * 60)
    print("测试 4/5: AI 摘要生成")
    print("=" * 60)

    if not config.STOCK_SYMBOLS:
        print("✗ 没有配置股票代码")
        return None

    test_symbol = config.STOCK_SYMBOLS[0]
    news_list = news_data.get(test_symbol, []) if news_data else []

    print(f"测试股票: {test_symbol}")
    print(f"新闻数量: {len(news_list)}")

    try:
        summary = summarize_stock_news(
            symbol=test_symbol,
            news_list=news_list,
            date=datetime.now().strftime("%Y-%m-%d"),
            api_key=config.ANTHROPIC_API_KEY,
            base_url=config.ANTHROPIC_BASE_URL,
            language=config.REPORT_LANGUAGE
        )

        print("✓ 摘要生成成功:")
        print("-" * 60)
        print(summary)
        print("-" * 60)

        return {test_symbol: summary}

    except Exception as e:
        print(f"✗ 摘要生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_report_builder(summaries, stock_info, news_data):
    """测试报告构建"""
    print("\n" + "=" * 60)
    print("测试 5/5: 报告构建")
    print("=" * 60)

    try:
        html = build_html_report(
            summaries=summaries,
            stock_info=stock_info,
            news_data=news_data,
            language=config.REPORT_LANGUAGE
        )

        print("✓ HTML 报告生成成功")
        print(f"  - 内容长度: {len(html)} 字符")

        # 保存到文件用于调试
        output_file = "tests/test_output.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  - 已保存到: {output_file}")

        return html

    except Exception as e:
        print(f"✗ 报告构建失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_email_sender(html_report):
    """测试邮件发送"""
    print("\n" + "=" * 60)
    print("额外测试: 邮件发送")
    print("=" * 60)

    if not html_report:
        print("✗ 没有可发送的报告")
        return False

    print(f"收件人: {', '.join(config.RECIPIENT_EMAILS)}")

    try:
        subject = f"[TEST] 📈 股票简报测试 | {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        success = send_email(
            subject=subject,
            html_content=html_report,
            recipients=config.RECIPIENT_EMAILS,
            sender=config.GMAIL_USER,
            app_password=config.GMAIL_APP_PASSWORD
        )

        if success:
            print("✓ 测试邮件发送成功")
            print(f"  请检查收件箱: {config.RECIPIENT_EMAILS[0]}")
            return True
        else:
            print("✗ 测试邮件发送失败")
            return False

    except Exception as e:
        print(f"✗ 邮件发送异常: {e}")
        return False


def main():
    """主测试流程"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "股票简报系统测试" + " " * 25 + "║")
    print("╚" + "=" * 58 + "╝")
    print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 运行测试
    results = {}

    results["config"] = test_config()

    if not results["config"]:
        print("\n✗ 配置测试失败，终止后续测试")
        return 1

    news_data = test_news_fetcher()
    results["news"] = news_data is not None

    stock_info = test_stock_info()
    results["info"] = stock_info is not None

    summaries = test_ai_summarizer(news_data)
    results["ai"] = summaries is not None

    html_report = None
    if summaries and stock_info and news_data:
        html_report = test_report_builder(summaries, stock_info, news_data)
        results["report"] = html_report is not None
    else:
        results["report"] = False

    # 邮件发送测试
    email_sent = test_email_sender(html_report)
    results["email"] = email_sent

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name:12s}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！系统可以正常运行。")
    else:
        print("⚠️  部分测试失败，请检查上述错误信息。")
    print("=" * 60)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
