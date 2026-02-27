"""
邮件发送模块
使用 Gmail SMTP 发送 HTML 邮件
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

from email.utils import formatdate


def send_email(
    subject: str,
    html_content: str,
    recipients: List[str],
    sender: str = None,
    app_password: str = None,
) -> bool:
    """
    使用 Gmail SMTP 发送 HTML 邮件

    Args:
        subject: 邮件主题
        html_content: HTML 格式的邮件内容
        recipients: 收件人列表
        sender: 发件人邮箱地址
        app_password: Gmail 应用专用密码

    Returns:
        发送成功返回 True，失败返回 False
    """
    if not sender or not app_password:
        print("错误：缺少发件人信息或应用密码")
        return False

    if not recipients:
        print("错误：没有收件人")
        return False

    try:
        # 创建邮件对象
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg["Date"] = formatdate(localtime=True)

        # 添加 HTML 内容
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        # 连接 Gmail SMTP 服务器
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(sender, app_password)

            # 发送邮件
            for recipient in recipients:
                server.sendmail(sender, recipient, msg.as_string())

        print(f"邮件发送成功！收件人：{', '.join(recipients)}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("错误：Gmail 认证失败，请检查应用密码是否正确")
        print("提示：需要使用应用专用密码，而非普通密码")
        return False

    except smtplib.SMTPException as e:
        print(f"错误：SMTP 错误 - {e}")
        return False

    except Exception as e:
        print(f"错误：邮件发送失败 - {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    import os

    test_html = """
    <html>
    <body>
        <h2>测试邮件</h2>
        <p>这是一封测试邮件。</p>
        <p>如果收到此邮件，说明配置正确！</p>
    </body>
    </html>
    """

    sender = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    recipients = os.getenv("RECIPIENT_EMAILS", "").split(",")

    if sender and password and recipients:
        send_email(
            subject="[TEST] 股票简报测试",
            html_content=test_html,
            recipients=[r.strip() for r in recipients if r.strip()],
            sender=sender,
            app_password=password
        )
