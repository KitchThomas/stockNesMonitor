# 股票每日新闻简报系统 — 部署说明

本文档说明如何部署和运行股票每日新闻简报系统。

---

## 目录

1. [本地运行](#本地运行)
2. [GitHub Actions 部署](#github-actions-部署)
3. [API 密钥获取](#api-密钥获取)
4. [Gmail 配置](#gmail-配置)
5. [常见问题](#常见问题)

---

## 本地运行

### 1. 安装依赖

```bash
cd stockNewsMonitor
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 密钥和配置。

### 3. 运行测试

测试整个流程是否正常：

```bash
python tests/test_run.py
```

### 4. 运行完整简报

```bash
python main.py
```

---

## GitHub Actions 部署

### 1. 创建 GitHub 仓库

如果还没有仓库，创建一个新的 GitHub 仓库并推送代码：

```bash
git init
git add .
git commit -m "Initial commit: Stock news digest system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. 配置 GitHub Secrets

进入仓库的 **Settings → Secrets and variables → Actions**，点击 **New repository secret** 添加以下密钥：

| Secret 名称 | 值 | 说明 |
|------------|-----|------|
| `ANTHROPIC_API_KEY` | 你的 Anthropic API Key | Claude API 密钥 |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` 或自定义 | API 基础 URL |
| `FINNHUB_API_KEY` | 你的 Finnhub API Key | 新闻数据源 |
| `GMAIL_USER` | 你的 Gmail 地址 | 发件邮箱 |
| `GMAIL_APP_PASSWORD` | Gmail 应用专用密码 | 非登录密码！ |
| `RECIPIENT_EMAILS` | 收件人邮箱（逗号分隔） | 接收简报的邮箱 |
| `STOCK_SYMBOLS` | 股票代码（逗号分隔） | 如: `AMD,NVDA,TSLA` |

### 3. 启用 GitHub Actions

1. 进入 **Actions** 标签页
2. 点击 **Daily Stock Digest** workflow
3. 点击 **Run workflow** 按钮进行首次测试

### 4. 验证运行

1. 在 Actions 页面查看运行日志
2. 检查收件箱是否收到测试邮件

---

## API 密钥获取

### Finnhub API Key（免费）

1. 访问 [Finnhub.io](https://finnhub.io/)
2. 点击右上角 **Get free API key**
3. 注册账号（支持 Google/Github 登录）
4. 在 Dashboard 复制 API Key

> **注意**：免费版限制 60 次/分钟，对本项目足够使用。

---

## Gmail 配置

### 1. 开启两步验证

1. 访问 [Google Account Security](https://myaccount.google.com/security)
2. 确保 **两步验证** 已开启

### 2. 生成应用专用密码

1. 访问 [Google App Passwords](https://myaccount.google.com/apppasswords)
2. 选择：
   - **应用**：选择「邮件」或「其他」输入「Stock Digest」
   - **设备**：选择「其他」输入「GitHub Actions」
3. 点击 **生成**
4. **复制 16 位密码**（格式：`xxxx xxxx xxxx xxxx`）

> **重要**：应用密码只在生成时显示一次，请妥善保存！

---

## 常见问题

### Q: 收不到邮件？

**检查清单**：
1. 查看 `.env` 中的 `GMAIL_APP_PASSWORD` 是否正确（包含空格）
2. 检查垃圾邮件文件夹
3. 确认收件人邮箱地址正确
4. 查看 GitHub Actions 日志是否有错误

### Q: Finnhub 返回空数据？

**可能原因**：
1. API Key 未激活（新注册需要等待几分钟）
2. 免费版每天有调用限制
3. 股票代码格式不正确

**解决方法**：系统会自动切换到 yfinance 作为备用数据源。

### Q: Claude API 调用失败？

**检查清单**：
1. 确认 `ANTHROPIC_API_KEY` 正确
2. 如果使用代理 API，检查 `ANTHROPIC_BASE_URL` 是否正确
3. 检查账户是否有足够的额度

### Q: 如何修改推送时间？

编辑 `.github/workflows/daily_digest.yml` 中的 cron 表达式：

```yaml
# UTC 时间（北京时间 = UTC + 8）
# 格式：分 时 日 月 周
schedule:
  - cron: '0 23 * * *'  # UTC 23:00 = 北京时间 07:00
```

常用时间：
- 北京时间 07:00 → `0 23 * * *`
- 北京时间 08:00 → `0 0 * * *`
- 北京时间 20:00 → `0 12 * * *`

### Q: 如何添加更多股票？

编辑 `.env` 中的 `STOCK_SYMBOLS`：

```env
# 美股
STOCK_SYMBOLS=AAPL,GOOGL,MSFT,TSLA,NVDA

# 港股
STOCK_SYMBOLS=0700.HK,9988.HK

# 混合
STOCK_SYMBOLS=AAPL,0700.HK,TSLA
```

---

## 本地定时任务（可选）

如果你想在本地服务器上定时运行，可以使用 cron：

### crontab 配置

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天早上 7:00 运行）
0 7 * * * cd /path/to/stockNewsMonitor && /usr/bin/python3 main.py >> logs/digest.log 2>&1
```

---

## 技术支持

如遇到问题，请检查：
1. Python 版本是否 >= 3.10
2. 所有依赖是否正确安装
3. GitHub Actions 日志中的详细错误信息

---

*文档版本：1.0*
