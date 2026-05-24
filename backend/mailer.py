import smtplib
from email.message import EmailMessage

EMAIL_SENDER = "laetitiavautrelle17@gmail.com"
APP_PASSWORD = "cwlq yjoy dfhd odit"

def send_alert(to_email, timestamp, motion_score, video_link):
    msg = EmailMessage()
    msg["Subject"] = f"ALERTE INTRUSION {timestamp}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email

    msg.set_content(f"""
ALERTE

Date : {timestamp}
Score : {int(motion_score)}

Vidéo :
{video_link}
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, APP_PASSWORD)
        smtp.send_message(msg)

    print("EMAIL ENVOYÉ (module externe)")
