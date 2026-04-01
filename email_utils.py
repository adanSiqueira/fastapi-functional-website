from fastapi.templating import Jinja2Templates
from config import settings
import aiosmtplib
from email.message import EmailMessage

templates = Jinja2Templates(directory="templates")

async def send_email(
        to_email: str,
        subject: str,
        plain_text: str,
        html_content: str | None = None) -> None:
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(plain_text)

    if html_content:
        message.add_alternative(html_content, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.mail_server,
        port=settings.mail_port,
        username=settings.mail_username,
        password=settings.mail_password.get_secret_value() or None,
        start_tls=True,
        use_tls=settings.mail_use_tls,
    )

async def send_password_reset_email(to_email: str, username: str, token: str) -> None:
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    subject = "Password Reset Request"
    plain_text = f"""
    Hi {username},

    You requested to reset your password. If you did not make this request, please ignore this email.
    To reset your password, click the following link: 
    
    {reset_url}

    This link will expire in {settings.reset_token_expire_minutes} minutes."""

    template = templates.env.get_template("email/password_reset.html")
    html_content = template.render(reset_link=reset_url, username=username)


    await send_email(
        to_email, 
        subject=subject,
        plain_text=plain_text,
        html_content=html_content
        )