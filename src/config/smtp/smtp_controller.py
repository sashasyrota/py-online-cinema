import os
import smtplib
from email.message import EmailMessage


def sent_message(content: str, subject: str, recipient_email: str):
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = subject
    msg["From"] = os.getenv("SENDER_EMAIL")
    msg["To"] = recipient_email

    with smtplib.SMTP(
        os.getenv("MAILHOG_HOST"), int(os.getenv("MAILHOG_PORT"))
    ) as server:
        server.send_message(msg)
