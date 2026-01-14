from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings


async def send_email(to: str, subject: str, html: str):
    msg = EmailMessage()
    msg["from"] = f"MGFisioBook <{settings.smtp_user}>"
    msg["to"] = to
    msg["subject"] = subject
    msg.set_content(html, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        start_tls=True,
        username=settings.smtp_user,
        password=settings.smtp_password,
    )
