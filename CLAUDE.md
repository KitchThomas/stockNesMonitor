# 股票每日新闻简报系统 — 完整需求说明
> 本文档可直接放入 Claude Code 项目根目录，作为 CLAUDE.md 使用，或作为初始 Prompt 提交。

---

## 项目概述

构建一个自动化的股票新闻监控与推送系统。每天早晨定时运行，自动抓取指定股票的前一天新闻，通过 Claude API 生成中文摘要简报，并发送到指定邮箱（Gmail）。

---

## 工作模式说明（重要）

请按照以下顺序**自主完成所有任务，无需等待用户确认**：

1. 阅读本文档，理解全部需求
2. 规划项目结构
3. 逐模块实现代码
4. 安装所有依赖
5. 创建配置文件模板
6. 编写测试脚本
7. 验证各模块可用性
8. 输出部署说明文档

**如遇到问题，优先尝试替代方案，不要停下来等待用户。**

---

## 技术栈

| 组件 | 技术选择 |
|------|---------|
| 语言 | Python 3.10+ |
| 新闻数据 | Finnhub API（免费版） + Yahoo Finance 备用 |
| AI 摘要 | Anthropic Claude API（claude-sonnet-4 模型） |
| 邮件发送 | Gmail SMTP（App Password 方式） |
| 定时任务 | GitHub Actions（cron 触发）或本地 cron |
| 配置管理 | `.env` 文件 + python-dotenv |

---

## 项目目录结构

```
stock-digest/
├── CLAUDE.md                  # 本文档（Claude Code 读取）
├── .env.example               # 环境变量模板（不含真实密钥）
├── .env                       # 真实配置（gitignore）
├── .gitignore
├── requirements.txt
├── config.py                  # 配置加载模块
├── main.py                    # 主入口，串联所有模块
│
├── modules/
│   ├── __init__.py
│   ├── news_fetcher.py        # 新闻抓取模块
│   ├── ai_summarizer.py       # Claude API 摘要模块
│   ├── email_sender.py        # 邮件发送模块
│   └── report_builder.py      # HTML 报告构建模块
│
├── templates/
│   └── email_template.html    # 邮件 HTML 模板
│
├── .github/
│   └── workflows/
│       └── daily_digest.yml   # GitHub Actions 定时任务
│
└── tests/
    ├── test_news_fetcher.py
    ├── test_email_sender.py
    └── test_run.py            # 一键测试整个流程
```

---

## 环境变量配置（`.env.example`）

```env
# Anthropic Claude API
ANTHROPIC_API_KEY=y697c0df11f044d4f91e4537edb9ff2b7.lJHP0KDqI1kWHip3
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic

# Finnhub API（免费注册：https://finnhub.io）
FINNHUB_API_KEY=d6h0gapr01qnjncmte3gd6h0gapr01qnjncmte40

# Gmail 配置
# 注意：需要开启两步验证，并生成"应用专用密码"
# 教程：https://support.google.com/accounts/answer/185833
GMAIL_USER=sj.sunnyjason@gmail.com
GMAIL_APP_PASSWORD=fuok sbcw revg kbgp

# 收件人（多个用逗号分隔）
RECIPIENT_EMAILS=recipient1@example.com,recipient2@example.com

# 监控的股票列表（多个用逗号分隔）
# 美股示例：AMD,PATH,BEP,BMY
# 港股示例：0700.HK,9988.HK
# A股需通过其他数据源
STOCK_SYMBOLS=AMD,PATH,BEP,BMY,AMZN,NVDA

# 推送时间配置（UTC 时间，北京时间=UTC+8）
# 北京时间 7:00 AM = UTC 23:00（前一天）
DIGEST_HOUR_UTC=23

# 简报语言（zh=中文，en=英文）
REPORT_LANGUAGE=zh

# 新闻抓取天数（建议1，即只抓取昨天的新闻）
NEWS_LOOKBACK_DAYS=1
```

---

## 模块详细需求

### 1. `modules/news_fetcher.py` — 新闻抓取模块

**功能：**
- 接受股票代码列表和日期范围作为输入
- 通过 Finnhub API 抓取每只股票的新闻
- 如果 Finnhub 返回为空，自动切换到 `yfinance` 作为备用
- 对每条新闻记录：标题、来源、发布时间、摘要（如有）、URL

**接口设计：**
```python
def fetch_news(symbols: list[str], days_back: int = 1) -> dict[str, list[dict]]:
    """
    返回格式：
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
```

**注意事项：**
- Finnhub 免费版限速：60次/分钟，多只股票需加 sleep(1)
- 日期范围：从昨天 00:00:00 到昨天 23:59:59（本地时区）
- 每只股票最多返回 20 条新闻（避免摘要过长）
- 如果某只股票无新闻，返回空列表，不报错

---

### 2. `modules/ai_summarizer.py` — AI 摘要模块

**功能：**
- 接受一只股票的新闻列表
- 调用 Claude API，生成结构化中文摘要
- 输出包含：重要事件、市场情绪判断、值得关注的风险点

**Claude Prompt 模板（中文）：**

```
你是一位专业的股票分析师助手。以下是 {symbol}（{company_name}）在 {date} 的新闻列表：

{news_list}

请用中文生成一份简洁的每日简报，包含以下部分：
1. **重要事件**（2-4条，每条一句话）
2. **市场情绪**（正面/中性/负面，并简要说明原因）
3. **需要关注**（1-2个风险点或机会点）

要求：
- 简洁客观，不做投资建议
- 如果新闻较少或不重要，直接说明"今日无重大事件"
- 总字数控制在 200 字以内
```

**接口设计：**
```python
def summarize_stock_news(symbol: str, news_list: list[dict], date: str) -> str:
    """返回 Markdown 格式的中文摘要字符串"""
```

---

### 3. `modules/report_builder.py` — 报告构建模块

**功能：**
- 将多只股票的摘要整合成一份完整的 HTML 邮件报告
- 样式要求：简洁、适合在邮件客户端中显示、移动端友好

**报告结构：**
```
主题：📈 每日股票简报 | 2024-01-15

[报告头部]
日期：2024年1月15日（星期一）
覆盖股票：AAPL | TSLA | NVDA | BYD

[每只股票一个卡片，包含]
- 股票代码 + 公司名称
- 昨日涨跌幅（从 yfinance 获取）
- AI 生成的中文摘要
- 新闻条数
- 查看原文链接列表（最多5条）

[页脚]
本简报由 AI 自动生成，仅供参考，不构成投资建议。
```

---

### 4. `modules/email_sender.py` — 邮件发送模块

**功能：**
- 使用 Gmail SMTP（SSL，端口 465）发送 HTML 邮件
- 支持多收件人
- 发送失败时记录错误日志，不中断程序

**接口设计：**
```python
def send_email(subject: str, html_content: str, recipients: list[str]) -> bool:
    """发送成功返回 True，失败返回 False 并打印错误"""
```

---

### 5. `main.py` — 主流程

```python
"""
执行顺序：
1. 加载配置
2. 获取目标日期（昨天）
3. 抓取所有股票新闻
4. 对每只股票生成 AI 摘要
5. 构建 HTML 报告
6. 发送邮件
7. 打印执行摘要（成功/失败统计）
"""
```

---

### 6. GitHub Actions 定时任务（`.github/workflows/daily_digest.yml`）

```yaml
name: Daily Stock Digest

on:
  schedule:
    # 北京时间每天早上 7:00 = UTC 23:00（前一天）
    - cron: '0 23 * * *'
  workflow_dispatch:  # 允许手动触发

jobs:
  send-digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run digest
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          FINNHUB_API_KEY: ${{ secrets.FINNHUB_API_KEY }}
          GMAIL_USER: ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          RECIPIENT_EMAILS: ${{ secrets.RECIPIENT_EMAILS }}
          STOCK_SYMBOLS: ${{ secrets.STOCK_SYMBOLS }}
        run: python main.py
```

---

## `requirements.txt`

```
anthropic>=0.25.0
finnhub-python>=2.4.0
yfinance>=0.2.38
python-dotenv>=1.0.0
requests>=2.31.0
jinja2>=3.1.0
```

---

## 测试脚本（`tests/test_run.py`）

此脚本用于本地验证整个流程，执行时：
1. 只抓取第一只股票（节省 API 额度）
2. 生成摘要并打印到控制台
3. 发送测试邮件（主题前缀加 `[TEST]`）

运行方式：
```bash
python tests/test_run.py
```

---

## 部署步骤（完成代码后自动生成此说明）

Claude Code 完成开发后，请自动生成 `DEPLOYMENT.md`，内容包括：
1. 如何注册 Finnhub 免费账号并获取 API Key
2. 如何为 Gmail 生成应用专用密码（App Password）
3. 如何在 GitHub 仓库设置 Secrets
4. 如何手动触发第一次运行测试
5. 常见问题排查

---

## 成功标准

- [ ] `python tests/test_run.py` 运行成功，收到测试邮件
- [ ] 邮件包含至少一只股票的 AI 中文摘要
- [ ] GitHub Actions 配置文件语法正确（可通过 `actionlint` 验证）
- [ ] `.env.example` 包含所有必要配置项说明
- [ ] 代码中无硬编码的密钥或个人信息

---

*文档版本：1.0 | 适用：Claude Code（claude-sonnet-4+）*
