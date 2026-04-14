import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_env_manual(filepath=".env"):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

load_env_manual()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")

    def send_email(self, recipients: list, subject: str, html_body: str, plain_body: str = None) -> bool:
        """
        Sends a professional email with both HTML and Plain Text alternatives.
        """
        if not self.username or not self.password:
            print("Error: SMTP credentials not found in environment.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.username
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject

            # Add plain text version (fallback)
            if not plain_body:
                plain_body = "Professional Lead Distribution. Please view in an HTML-capable email client."
            
            msg.attach(MIMEText(plain_body, "plain"))
            # Add HTML version
            msg.attach(MIMEText(html_body, "html"))

            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
