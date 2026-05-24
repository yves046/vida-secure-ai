import cv2
import time
import datetime
import os
import subprocess
from fpdf import FPDF
import smtplib
from email.message import EmailMessage

# =========================
# CONFIG
# =========================
CAPTURE_DIR = "captures"
os.makedirs(CAPTURE_DIR, exist_ok=True)

EMAIL_SENDER = "laetitiavautrelle17@gmail.com"
EMAIL_PASSWORD = "cwlq yjoy dfhd odit"

# =========================
# EMAIL
# =========================
def send_email(email, photo_path, pdf_path, video_path):

    msg = EmailMessage()
    msg["Subject"] = "🚨 ALERTE INTRUSION VIDA AI"
    msg["From"] = EMAIL_SENDER
    msg["To"] = email

    msg.set_content("Intrusion détectée. Voir pièces jointes.")

    with open(photo_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename="intrusion.jpg")

    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="rapport.pdf")

    with open(video_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="video", subtype="mp4", filename="video.mp4")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

    print("📧 Email envoyé")

# =========================
# VIDEO (FFmpeg)
# =========================
def record_video(rtsp, output_path, duration=10):

    command = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", rtsp,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-y",
        output_path
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return os.path.exists(output_path)

# =========================
# PDF
# =========================
def generate_pdf(photo_path, video_name, timestamp):

    pdf_path = f"{CAPTURE_DIR}/rapport_{timestamp}.pdf"

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "VIDA Secure AI", ln=True, align="C")

    pdf.set_font("Arial", size=11)
    pdf.ln(5)

    pdf.cell(0, 8, f"Date: {timestamp}", ln=True)
    pdf.cell(0, 8, "Alerte: Intrusion detectee", ln=True)

    pdf.ln(10)
    pdf.cell(0, 8, f"Video: {video_name}", ln=True)

    pdf.output(pdf_path)

    print("📄 PDF généré")

    return pdf_path

# =========================
# ANALYSE PRINCIPALE
# =========================
def analyse_video(rtsp, email):

    print(f"🎥 Analyse caméra → {rtsp}")

    cap = cv2.VideoCapture(rtsp)

    if not cap.isOpened():
        print("❌ OpenCV échoue, fallback FFmpeg...")

        # test rapide avec ffmpeg (stabilité flux)
        try:
            subprocess.run([
                "ffmpeg",
                "-rtsp_transport", "tcp",
                "-i", rtsp,
                "-t", "3",
                "-f", "null",
                "-"
            ])
        except:
            print("❌ Flux totalement inaccessible")
            return

        return

    prev_frame = None
    motion_count = 0
    last_alert = 0
    COOLDOWN = 20

    start_time = time.time()
    MAX_DURATION = 20  # analyse courte mais répétée par monitor

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        if prev_frame is None:
            prev_frame = blur
            continue

        diff = cv2.absdiff(prev_frame, blur)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        movement = False
        for c in contours:
            if cv2.contourArea(c) > 4000:
                movement = True

        if movement:
            motion_count += 1
        else:
            motion_count = 0

        # =========================
        # DÉTECTION
        # =========================
        if motion_count >= 3 and (time.time() - last_alert > COOLDOWN):

            print("🚨 INTRUSION CONFIRMÉE")

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            photo_path = f"{CAPTURE_DIR}/intrusion_{timestamp}.jpg"
            cv2.imwrite(photo_path, frame)

            video_path = f"{CAPTURE_DIR}/intrusion_{timestamp}.mp4"

            print("🎥 Enregistrement vidéo...")
            success = record_video(rtsp, video_path)

            pdf_path = generate_pdf(photo_path, os.path.basename(video_path), timestamp)

            if success:
                try:
                    send_email(email, photo_path, pdf_path, video_path)
                except Exception as e:
                    print("❌ Erreur email:", e)

            last_alert = time.time()
            motion_count = 0

        prev_frame = blur

        # stop propre (évite blocage infini)
        if time.time() - start_time > MAX_DURATION:
            print("⏹️ Fin analyse")
            break

    cap.release()