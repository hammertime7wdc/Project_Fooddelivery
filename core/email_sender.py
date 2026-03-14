import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SMTP_EMAIL")
        self.sender_password = os.getenv("SMTP_PASSWORD")
        self.sender_name = os.getenv("SMTP_SENDER_NAME", "LK Martin Food Systems")

    def is_configured(self):
        return bool(self.sender_email and self.sender_password)

    def _send_email(self, to_email: str, subject: str, text_body: str, html_body: str):
        if not self.is_configured():
            return False, "Email service not configured"

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            message.attach(MIMEText(text_body, "plain"))
            message.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            return True, "Email sent successfully"
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP authentication failed"
        except Exception as ex:
            return False, f"Email send error: {str(ex)}"

    def send_verification_email(self, to_email: str, full_name: str, token: str, expiry_minutes: int = 10):
        subject = "Your LK Martin Food Systems verification code"
        text_body = (
            f"Hello {full_name},\n\n"
            "Thanks for signing up for LK Martin Food Systems.\n\n"
            "Use this verification code to complete your signup:\n"
            f"{token}\n\n"
            f"This code expires in {expiry_minutes} minutes.\n"
            "Never share this code with anyone.\n\n"
            "If you did not request this, you can ignore this email.\n\n"
            "LK Martin Food Systems Team\n"
        )

        html_body = f"""
<html>
  <body style=\"font-family: Arial, sans-serif; color: #222;\">
        <div style="max-width: 600px; margin: auto; border: 1px solid #eee; border-radius: 12px; overflow: hidden;">
            <div style="background: #0D4715; color: #fff; padding: 16px 20px;">
                <h2 style="margin: 0; font-size: 20px;">Verify your email</h2>
            </div>
            <div style="padding: 20px;">
                <p style="margin-top: 0;">Hello <strong>{full_name}</strong>,</p>
                <p>Thanks for signing up for <strong>LK Martin Food Systems</strong>. Use this code to complete your signup:</p>

                <div style="font-size: 30px; font-weight: 700; letter-spacing: 4px; text-align: center; color: #0D4715; background: #F7F2E8; border: 1px solid #E7DCC7; border-radius: 10px; padding: 14px; margin: 16px 0;">
                    {token}
                </div>

                <p style="margin: 0;">⏱ This code expires in <strong>{expiry_minutes} minutes</strong>.</p>
                <p style="margin-top: 10px; color: #6b6b6b;">For your security, do not share this code with anyone.</p>
                <hr style="border: none; border-top: 1px solid #efefef; margin: 18px 0;" />
                <p style="margin: 0; color: #777; font-size: 13px;">If you did not request this, you can safely ignore this email.</p>
                <p style="margin-top: 16px; color: #666;">LK Martin Food Systems Team</p>
            </div>
    </div>
  </body>
</html>
"""

        return self._send_email(to_email, subject, text_body, html_body)

    def send_password_reset_email(self, to_email: str, full_name: str, token: str, expiry_minutes: int = 10):
        subject = "Your LK Martin Food Systems password reset code"
        text_body = (
            f"Hello {full_name},\n\n"
            "We received a request to reset your LK Martin Food Systems password.\n\n"
            "Use this code to reset your password:\n"
            f"{token}\n\n"
            f"This code expires in {expiry_minutes} minutes.\n"
            "Never share this code with anyone.\n\n"
            "If you did not request this, you can ignore this email.\n\n"
            "LK Martin Food Systems Team\n"
        )

        html_body = f"""
<html>
  <body style=\"font-family: Arial, sans-serif; color: #222;\">
        <div style="max-width: 600px; margin: auto; border: 1px solid #eee; border-radius: 12px; overflow: hidden;">
            <div style="background: #0D4715; color: #fff; padding: 16px 20px;">
                <h2 style="margin: 0; font-size: 20px;">Reset your password</h2>
            </div>
            <div style="padding: 20px;">
                <p style="margin-top: 0;">Hello <strong>{full_name}</strong>,</p>
                <p>Use this code to reset your <strong>LK Martin Food Systems</strong> password:</p>

                <div style="font-size: 30px; font-weight: 700; letter-spacing: 4px; text-align: center; color: #0D4715; background: #F7F2E8; border: 1px solid #E7DCC7; border-radius: 10px; padding: 14px; margin: 16px 0;">
                    {token}
                </div>

                <p style="margin: 0;">⏱ This code expires in <strong>{expiry_minutes} minutes</strong>.</p>
                <p style="margin-top: 10px; color: #6b6b6b;">For your security, do not share this code with anyone.</p>
                <hr style="border: none; border-top: 1px solid #efefef; margin: 18px 0;" />
                <p style="margin: 0; color: #777; font-size: 13px;">If you did not request this, you can safely ignore this email.</p>
                <p style="margin-top: 16px; color: #666;">LK Martin Food Systems Team</p>
            </div>
    </div>
  </body>
</html>
"""

        return self._send_email(to_email, subject, text_body, html_body)


_email_sender = None


def get_email_sender():
    global _email_sender
    if _email_sender is None:
        _email_sender = EmailSender()
    return _email_sender
