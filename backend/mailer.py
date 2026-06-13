import smtplib
from email.message import EmailMessage
import os

EMAIL_SENDER = "laetitiavautrelle17@gmail.com"
APP_PASSWORD = "cwlq yjoy dfhd odit"

def send_alert(
    to_email,
    timestamp,
    intrusion_duration,
    persons_count,
    pdf_path,
    image_path,
    video_path
):
    print("EMAIL EN COURS D'ENVOI")

    msg = EmailMessage()

    msg["Subject"] = f"ALERTE INTRUSION {timestamp}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email

    msg.set_content(f"""
ALERTE VIDA SECURE AI

Date : {timestamp}

Durée intrusion : {intrusion_duration} secondes

Nombre maximal de personnes :
{persons_count}

Vidéo :
{video_path}

Rapport :
{pdf_path}
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, APP_PASSWORD)
        smtp.send_message(msg)

    print("EMAIL ENVOYÉ")
