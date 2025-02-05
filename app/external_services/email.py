import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
            text-align: center;
        }}
        .header {{
            background: linear-gradient(45deg, #4CAF50, #7B1FA2);
            padding: 20px;
            color: white;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            font-size: 16px;
            color: #333;
            margin-top: 20px;
        }}
        .code-box {{
            display: inline-block;
            background: #f0f0f0;
            padding: 10px 20px;
            font-size: 20px;
            font-weight: bold;
            color: #333;
            border-radius: 5px;
            margin-top: 10px;
            user-select: all;
        }}
        .footer {{
            margin-top: 20px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">🌱 Умная Теплица</div>
        <div class="content">
            <p>{message}</p>
            <div class="code-box">{code}</div>
        </div>
        <div class="footer">
            &copy; {year} Умная Теплица. Все права защищены.
        </div>
    </div>
</body>
</html>
"""

def send_email(to: str, subject: str, message: str, code: str):
    try:
        email_body = HTML_TEMPLATE.format(message=message, code=code, year=2025)

        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(email_body, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to, msg.as_string())

        print(f"Email успешно отправлен на {to}")

    except Exception as e:
        print(f"Ошибка при отправке email: {e}")
