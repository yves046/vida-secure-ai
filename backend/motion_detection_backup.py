import cv2
import numpy as np
import subprocess
import time
import os
import smtplib
from email.message import EmailMessage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

RTSP_URL = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

WIDTH = 640
HEIGHT = 360

EMAIL_SENDER = "laetitiavautrelle17@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = "yvestoure717@gmail.com"

# ---------------- EMAIL ----------------
def send_email(image_path, video_path, pdf_path):
    try:
        msg = EmailMessage()
        msg["Subject"] = "🚨 ALERTE INTRUSION"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        msg.set_content("Intrusion détectée. Voir pièces jointes.")

        # image
        with open(image_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename=image_path)

        # video
        if os.path.exists(video_path):
            with open(video_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="video", subtype="mp4", filename=video_path)

        # pdf
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=pdf_path)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print("📧 Email envoyé")

    except Exception as e:
        print("❌ Email erreur:", e)


# ---------------- PDF ----------------
def create_pdf(pdf_path, image_path):
    doc = SimpleDocTemplate(pdf_path)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("RAPPORT DE SÉCURITÉ", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Type : Intrusion détectée", styles["Normal"]))
    elements.append(Paragraph(f"Heure : {time.ctime()}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    elements.append(Image(image_path, width=300, height=200))

    doc.build(elements)


# ---------------- VIDEO FFmpeg ----------------
def record_video(video_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-rtsp_transport", "tcp",
        "-i", RTSP_URL,
        "-t", "10",
        "-vcodec", "libx264",
        "-preset", "ultrafast",
        video_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------- PIPE FFmpeg ----------------
def start_ffmpeg():
    return subprocess.Popen(
        [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", RTSP_URL,
            "-f", "image2pipe",
            "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo",
            "-"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=10**8
    )


# ---------------- MAIN ----------------
print("🎥 Lancement FFmpeg...")

pipe = start_ffmpeg()
previous_frame = None
last_alert = 0

while True:
    try:
        raw = pipe.stdout.read(WIDTH * HEIGHT * 3)

        if len(raw) != WIDTH * HEIGHT * 3:
            print("❌ Flux coupé → relance FFmpeg")
            pipe.kill()
            time.sleep(2)
            pipe = start_ffmpeg()
            previous_frame = None
            continue

        frame = np.frombuffer(raw, np.uint8).reshape((HEIGHT, WIDTH, 3))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if previous_frame is None:
            previous_frame = gray
            continue

        diff = cv2.absdiff(previous_frame, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        motion_score = np.sum(thresh)

        # DETECTION
        if motion_score > 5000000 and time.time() - last_alert > 10:
            print("🚨 MOUVEMENT DÉTECTÉ")

            timestamp = int(time.time())

            image_path = f"intrusion_{timestamp}.jpg"
            video_path = f"intrusion_{timestamp}.mp4"
            pdf_path = f"intrusion_{timestamp}.pdf"

            cv2.imwrite(image_path, frame)
            print(f"📸 Image: {image_path}")

            # vidéo (FFmpeg)
            record_video(video_path)
            print(f"💾 Vidéo: {video_path}")

            # pdf
            create_pdf(pdf_path, image_path)

            # email
            send_email(image_path, video_path, pdf_path)

            last_alert = time.time()

        previous_frame = gray

    except KeyboardInterrupt:
        print("🛑 Arrêt manuel")
        pipe.kill()
        break

    except Exception as e:
        print("❌ Erreur:", e)
        pipe.kill()
        time.sleep(2)
        pipe = start_ffmpeg()
