# send_mail.py
import sys, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from pathlib import Path

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
FROM_EMAIL  = "votre.email@gmail.com"       # ← À CHANGER
APP_PASS    = "votre-app-password"           # ← À CHANGER

def attach(msg, filepath):
    p = Path(filepath)
    if not p.exists(): return
    with open(p, "rb") as f:
        if p.suffix.lower() in {".jpg",".jpeg",".png"}:
            part = MIMEImage(f.read())
        else:
            part = MIMEApplication(f.read(), Name=p.name)
        part['Content-Disposition'] = f'attachment; filename="{p.name}"'
        msg.attach(part)

if __name__ == "__main__":
    if len(sys.argv) != 8:
        print("Usage: python send_mail.py <to> <date_heure> <zone> <niveau> <photo> <video> <pdf>")
        sys.exit(1)

    to_addr    = sys.argv[1]
    date_heure = sys.argv[2]
    zone       = sys.argv[3]
    niveau     = sys.argv[4]
    photo      = sys.argv[5]
    video      = sys.argv[6]
    pdf        = sys.argv[7]

    msg = MIMEMultipart()
    msg["From"]    = FROM_EMAIL
    msg["To"]      = to_addr
    msg["Subject"] = f"ALERTE - {zone} ({niveau})"

    body = f"""
    ALERTE INTRUSION
    {date_heure}
    Zone : {zone}
    Niveau : {niveau}

    Pièces jointes : photo, vidéo, pdf
    """

    msg.attach(MIMEText(body, "plain"))

    attach(msg, photo)
    attach(msg, video)
    attach(msg, pdf)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(FROM_EMAIL, APP_PASS)
            s.send_message(msg)
        print("OK")
    except Exception as e:
        print("Erreur:", e)
        sys.exit(1)
