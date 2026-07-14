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

    msg["Subject"] = (
        f"ALERTE VIDA SECURE AI - {timestamp}"
    )

    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email

    msg.set_content(
        f"""
ALERTE VIDA SECURE AI

Une intrusion a été détectée.

Date : {timestamp}

Durée intrusion : {intrusion_duration} secondes

Nombre maximal de personnes détectées :
{persons_count}

Veuillez consulter les pièces jointes :

• Rapport PDF VIDA
• Capture d'écran de l'intrusion
• Vidéo de l'intrusion
"""
    )

    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename=os.path.basename(pdf_path)
            )

    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype="jpeg",
                filename=os.path.basename(image_path)
            )

    if os.path.exists(video_path):
        with open(video_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="video",
                subtype="mp4",
                filename=os.path.basename(video_path)
            )

    try:
        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=20
        ) as smtp:

            smtp.login(
                EMAIL_SENDER,
                APP_PASSWORD
            )

            print("Nombre de pièces jointes :", len(msg.get_payload()))

            for part in msg.iter_attachments():
                print(
                    "PJ :",
                    part.get_filename(),
                    part.get_content_type(),
                    len(part.get_payload(decode=True))
                )

            smtp.send_message(msg)

        print("EMAIL ENVOYÉ")

    except Exception as e:
        print("ERREUR EMAIL :", e)
