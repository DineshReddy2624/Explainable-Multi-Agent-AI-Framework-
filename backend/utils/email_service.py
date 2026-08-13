import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings
from core.logging import logger

def send_password_reset_email(to_email: str, reset_otp: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Password Reset Request - DataQuality AI Platform"
        msg["From"] = settings.EMAILS_FROM
        msg["To"] = to_email

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #0b0f19; color: #ffffff; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #111827; padding: 30px; border-radius: 12px; border: 1px solid #1f2937;">
              <h2 style="color: #6366f1; text-align: center;">DataQuality AI</h2>
              <h3 style="text-align: center; color: #f9fafb;">Password Reset Verification Code</h3>
              <p style="color: #9ca3af;">You requested to reset your password. Use the verification code below to authorize your password reset:</p>
              
              <div style="background-color: #1f2937; padding: 15px; text-align: center; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 4px; color: #06b6d4; margin: 20px 0;">
                {reset_otp}
              </div>

              <p style="color: #9ca3af; font-size: 12px;">If you did not request a password reset, please ignore this email.</p>
              <hr style="border: 0; border-top: 1px solid #1f2937; margin: 20px 0;" />
              <p style="color: #6b7280; font-size: 11px; text-align: center;">© {settings.PROJECT_NAME}</p>
            </div>
          </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        # Connect to Gmail SMTP Server
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM, to_email, msg.as_string())

        logger.info(f"Password reset email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False
