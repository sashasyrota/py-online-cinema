import os
import smtplib
from email.message import EmailMessage


def sent_message(content: str, subject: str, recipient_email: str):
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = subject
    msg["From"] = os.getenv("SENDER_EMAIL")
    msg["To"] = recipient_email

    with smtplib.SMTP('localhost', 1025) as server:
        server.send_message(msg)