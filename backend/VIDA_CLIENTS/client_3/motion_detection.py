import cv2
import numpy as np
import time
import os
import smtplib
import subprocess
from email.message import EmailMessage
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# =====================================================
# DOSSIERS AUTO
# =====================================================

os.makedirs("alerts/images", exist_ok=True)
os.makedirs("alerts/videos", exist_ok=True)
os.makedirs("alerts/reports", exist_ok=True)

# =====================================================
# CONFIGURATION
# =====================================================

RTSP_URL = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = "yvestoure717@gmail.com"

CLIENT_NAME = "Magasin Test"
CAMERA_NAME = "Entrée Principale"
COMPANY_NAME = "VIDA SECURE AI"

WIDTH = 640
HEIGHT = 360

MOTION_THRESHOLD = 5000000
ALERT_COOLDOWN = 45
VIDEO_DURATION = 6

# =====================================================
# OUTILS
# =====================================================

def now_string():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def write_log(message):
    with open("logs.txt", "a") as f:
        f.write(f"{now_string()} | {message}\n")


def launch_ffmpeg():
    print("🎥 Lancement FFmpeg...")

    cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", RTSP_URL,
        "-vf", f"scale={WIDTH}:{HEIGHT}",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo",
        "-an",
        "-sn",
        "-f", "rawvideo",
        "-"
    ]

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=10**8
    )


def read_frame(pipe):
    raw = pipe.stdout.read(WIDTH * HEIGHT * 3)

    if len(raw) != WIDTH * HEIGHT * 3:
        return None

    frame = np.frombuffer(raw, dtype=np.uint8)
    frame = frame.reshape((HEIGHT, WIDTH, 3))
    return frame


def record_video(video_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-rtsp_transport", "tcp",
        "-i", RTSP_URL,
        "-t", str(VIDEO_DURATION),
        "-an",
        "-c:v", "h264",
        "-movflags", "+faststart",
        video_path
    ]

    print("🎥 Enregistrement vidéo...")

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("❌ Erreur FFmpeg :")
        print(result.stderr)
        write_log("Erreur FFmpeg vidéo")
        return False

    if os.path.exists(video_path):
        print("✅ Vidéo créée :", video_path)
        return True
    else:
        print("❌ Fichier vidéo introuvable")
        return False


# =====================================================
# PDF
# =====================================================

def create_pdf(pdf_path):

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()
    elements = []

    # =====================================================
    # HEADER
    # =====================================================

    title = Paragraph(
        "<font size=22 color='#0B1F3A'><b>VIDA Secure AI</b></font>",
        styles["Title"]
    )
    elements.append(title)

    sub = Paragraph(
        "<font size=10 color='grey'>Système intelligent de surveillance automatisée</font>",
        styles["Normal"]
    )
    elements.append(sub)
    elements.append(Spacer(1, 18))

    # =====================================================
    # ALERTE ROUGE
    # =====================================================

    alert_table = Table(
        [[Paragraph(
            "<font size=16 color='white'><b>ALERTE SÉCURITÉ – INTRUSION DÉTECTÉE</b></font>",
            styles["Normal"]
        )]],
        colWidths=[540]
    )

    alert_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.red),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    elements.append(alert_table)
    elements.append(Spacer(1, 20))

    # =====================================================
    # INFOS INCIDENT
    # =====================================================

    incident_id = f"INC-{int(time.time())}"

    data = [
        ["Date & heure", now_string()],
        ["Zone violée", CAMERA_NAME],
        ["Niveau d'alerte", "WARNING"],
        ["ID Événement", incident_id],
    ]

    info_table = Table(data, colWidths=[180, 360])

    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#0B1F3A")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),

        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F4F6F8")),
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),

        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 22))

    # =====================================================
    # PREUVES
    # =====================================================

    preuve_title = Paragraph(
        "<font size=14 color='#0B1F3A'><b>Preuves disponibles</b></font>",
        styles["Heading2"]
    )
    elements.append(preuve_title)
    elements.append(Spacer(1, 10))

    preuves = """
    • Capture image jointe à l'email<br/>
    • Vidéo de l'incident jointe à l'email<br/>
    • Séquence enregistrée automatiquement<br/>
    • Données horodatées et archivables
    """

    elements.append(Paragraph(preuves, styles["Normal"]))
    elements.append(Spacer(1, 22))

    # =====================================================
    # ANALYSE IA
    # =====================================================

    ai_title = Paragraph(
        "<font size=14 color='#0B1F3A'><b>Analyse automatique VIDA AI</b></font>",
        styles["Heading2"]
    )
    elements.append(ai_title)
    elements.append(Spacer(1, 10))

    analyse = """
    Mouvement anormal détecté dans une zone surveillée.
    Présence potentiellement non autorisée identifiée.
    Vérification humaine immédiate recommandée.
    """

    elements.append(Paragraph(analyse, styles["Normal"]))
    elements.append(Spacer(1, 22))

    # =====================================================
    # RECOMMANDATIONS
    # =====================================================

    reco_title = Paragraph(
        "<font size=14 color='#0B1F3A'><b>Actions recommandées</b></font>",
        styles["Heading2"]
    )
    elements.append(reco_title)
    elements.append(Spacer(1, 10))

    reco = """
    • Vérifier les accès du site<br/>
    • Examiner la vidéo jointe<br/>
    • Informer le responsable sécurité<br/>
    • Conserver ce rapport dans les archives
    """

    elements.append(Paragraph(reco, styles["Normal"]))
    elements.append(Spacer(1, 35))

    # =====================================================
    # FOOTER
    # =====================================================

    footer = Paragraph(
        "<font size=9 color='grey'>VIDA Secure AI | Développé en Côte d'Ivoire | TOURE Yves – Ingénieur IA Sécurité</font>",
        styles["Normal"]
    )
    elements.append(footer)

    doc.build(elements)
# =====================================================
# EMAIL
# =====================================================

def attach_file(msg, filepath, maintype, subtype):
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(filepath)
            )


def send_email(image_path, video_path, pdf_path):
    try:
        msg = EmailMessage()

        msg["Subject"] = (
            f"🚨 ALERTE INTRUSION | "
            f"{CLIENT_NAME} | "
            f"{datetime.now().strftime('%H:%M:%S')}"
        )

        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO

        msg.set_content(f"""
Alerte automatique détectée

Client : {CLIENT_NAME}
Caméra : {CAMERA_NAME}
Date : {now_string()}

{COMPANY_NAME}
""")

        attach_file(msg, image_path, "image", "jpeg")

        if (
            video_path
            and os.path.exists(video_path)
            and os.path.getsize(video_path) > 10000
        ):
            attach_file(msg, video_path, "video", "mp4")
            print("🎬 Vidéo jointe au mail")

        attach_file(msg, pdf_path, "application", "pdf")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print("📧 Email envoyé")
        write_log("Email envoyé")

    except Exception as e:
        print("❌ Email erreur:", e)
        write_log("Erreur email")


# =====================================================
# PRINCIPAL
# =====================================================

pipe = launch_ffmpeg()

previous_gray = None
last_alert = 0
buffer_frames = []

try:

    while True:

        frame = read_frame(pipe)

        if frame is None:
            print("❌ Flux coupé → relance FFmpeg")
            write_log("Flux coupé")

            try:
                pipe.kill()
            except:
                pass

            time.sleep(5)
            pipe = launch_ffmpeg()
            previous_gray = None
            continue

        buffer_frames.append(frame.copy())

        if len(buffer_frames) > 8:
            buffer_frames.pop(0)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if previous_gray is None:
            previous_gray = gray
            continue

        delta = cv2.absdiff(previous_gray, gray)
        motion_score = np.sum(delta)
        previous_gray = gray

        if motion_score > MOTION_THRESHOLD:

            now = time.time()

            if now - last_alert > ALERT_COOLDOWN:

                print("🚨 MOUVEMENT DÉTECTÉ")
                write_log("Mouvement détecté")

                ts = int(now)

                image_path = f"alerts/images/intrusion_{ts}.jpg"
                video_path = f"alerts/videos/intrusion_{ts}.mp4"
                pdf_path = f"alerts/reports/rapport_{ts}.pdf"

                stable = buffer_frames[len(buffer_frames)//2]

                cv2.imwrite(image_path, stable)
                print("📸 Image:", image_path)

                ok = record_video(video_path)

                if ok:
                    print("💾 Vidéo:", video_path)
                    print("🎬 Taille vidéo:", os.path.getsize(video_path))
                else:
                    video_path = None

                create_pdf(pdf_path)

                send_email(
                    image_path,
                    video_path,
                    pdf_path
                )

                with open("alerts.csv", "a") as f:
                    f.write(
                        f"{now_string()},{CLIENT_NAME},{CAMERA_NAME},INTRUSION\n"
                        )

                last_alert = now

except KeyboardInterrupt:
    print("🛑 Arrêt manuel")

finally:
    try:
        pipe.kill()
    except:
        pass

    cv2.destroyAllWindows()
