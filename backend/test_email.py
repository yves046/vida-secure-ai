import smtplib
from email.message import EmailMessage

EMAIL_SENDER = "laetitiavautrelle17@gmail.com"
EMAIL_RECEIVER = "yvestoure717@gmail.com"
APP_PASSWORD = "cwlq yjoy dfhd odit"

msg = EmailMessage()
msg["Subject"] = "TEST EMAIL"
msg["From"] = EMAIL_SENDER
msg["To"] = EMAIL_RECEIVER

msg.set_content("Test simple")

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(EMAIL_SENDER, APP_PASSWORD)
    smtp.send_message(msg)

print("Email envoyé")
