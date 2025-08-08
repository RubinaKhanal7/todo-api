import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL

    def generate_verification_token(self) -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)

    def get_verification_expiry(self) -> datetime:
        """Get verification token expiry time"""
        return datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)

    def send_verification_email(self, to_email: str, full_name: str, verification_token: str) -> bool:
        """Send email verification email with clickable link that redirects to docs"""
        try:
            verification_url = f"http://localhost:8000/auth/verify-email/{verification_token}?redirect=/docs"
            
            html = f"""\
            <html>
            <body>
                <p>Hi {full_name},</p>
                <p>Please verify your email by clicking the link below:</p>
                <p><a href="{verification_url}">Verify Email</a></p>
                <p>If you didn't request this, please ignore this email.</p>
                <p>Best regards,<br>Todo App Team</p>
            </body>
            </html>
            """

            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "Verify Your Email - Todo App"

            # Attach HTML version
            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Verification email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            return False

    def send_status_change_email(self, to_email: str, full_name: str, new_status: str) -> bool:
        """Send email when user status changes"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = f"Account Status Update - Todo App"

            status_messages = {
                "ACTIVE": "Your account has been activated successfully!",
                "SUSPENDED": "Your account has been suspended. Please contact support.",
                "BANNED": "Your account has been banned due to policy violations.",
                "INACTIVE": "Your account has been deactivated.",
            }

            message = status_messages.get(new_status, f"Your account status has been changed to {new_status}.")

            # Create both plain and HTML versions
            text = f"""\
            Hi {full_name},
            
            {message}
            
            If you have any questions, please contact our support team.
            
            Best regards,
            Todo App Team
            """

            html = f"""\
            <html>
              <body>
                <p>Hi {full_name},</p>
                <p>{message}</p>
                <p>If you have any questions, please contact our support team.</p>
                <p>Best regards,<br>Todo App Team</p>
              </body>
            </html>
            """

            # Attach both versions
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send the email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Status change email sent to {to_email}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"Failed to send status change email: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending status email: {str(e)}")
            return False

email_service = EmailService()