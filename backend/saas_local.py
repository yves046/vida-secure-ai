import cv2
import numpy as np
import subprocess
import datetime
import os
from fpdf import FPDF
import time

# ------------------------
# CONFIGURATION DES DOSSIERS
# ------------------------
CAPTURE_DIR = "captures"
VIDEO_DIR = "videos"
PDF_DIR = "pdf_reports"

os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# ------------------------
# CONFIGURATION CAMERA
# ------------------------
RTSP_URL = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

PROC_WIDTH, PROC_HEIGHT = 640, 480   # pour traitement rapide
DISPLAY_WIDTH, DISPLAY_HEIGHT = 1280, 720  # affichage
FPS = 5
FRAME_INTERVAL = 1 / FPS

# ------------------------
# LANCER FFmpeg EN BACKGROUND
# ------------------------
ffmpeg_cmd = [
    "ffmpeg",
    "-rtsp_transport", "tcp",
    "-i", RTSP_URL,
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-"
]

pipe = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10**8)

# ------------------------
# VARIABLES DÉTECTION
# ------------------------
prev_frame = None
motion_accumulator = 0
video_frames = []
last_time = 0

# Fenêtre OpenCV réglable
cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Camera", DISPLAY_WIDTH, DISPLAY_HEIGHT)

print("🟢 Démarrage détection intrusion... Appuyez sur 'q' pour quitter")

# ------------------------
# BOUCLE PRINCIPALE
# ------------------------
while True:
    # Limitation FPS
    if time.time() - last_time < FRAME_INTERVAL:
        continue
    last_time = time.time()

    raw_frame = pipe.stdout.read(PROC_WIDTH*PROC_HEIGHT*3)
    if len(raw_frame) != PROC_WIDTH*PROC_HEIGHT*3:
        continue

    frame_proc = np.frombuffer(raw_frame, np.uint8).reshape((PROC_HEIGHT, PROC_WIDTH, 3))
    frame_display = cv2.resize(frame_proc, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

    # Conversion pour détection
    gray = cv2.cvtColor(frame_proc, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    if prev_frame is None:
        prev_frame = blur
        continue

    diff = cv2.absdiff(prev_frame, blur)
    _, thresh = cv2.threshold(diff, 35, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    movement_detected = False
    for contour in contours:
        if cv2.contourArea(contour) < 3000:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        # Adapter rectangle à la fenêtre affichage
        x_disp = int(x * DISPLAY_WIDTH / PROC_WIDTH)
        y_disp = int(y * DISPLAY_HEIGHT / PROC_HEIGHT)
        w_disp = int(w * DISPLAY_WIDTH / PROC_WIDTH)
        h_disp = int(h * DISPLAY_HEIGHT / PROC_HEIGHT)
        cv2.rectangle(frame_display, (x_disp, y_disp), (x_disp+w_disp, y_disp+h_disp), (0,255,0), 2)
        movement_detected = True

    # Accumulateur pour confirmer mouvement
    if movement_detected:
        motion_accumulator += 1
        video_frames.append(frame_display.copy())
    else:
        motion_accumulator = max(0, motion_accumulator - 1)

    # Si intrusion confirmée
    if motion_accumulator >= 2:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # ---- Photo ----
        photo_path = f"{CAPTURE_DIR}/intrusion_{timestamp}.jpg"
        cv2.imwrite(photo_path, frame_display)
        print(f"⚠️ Intrusion détectée ! Photo sauvegardée : {photo_path}")

        # ---- Vidéo courte ----
        if video_frames:
            video_path = f"{VIDEO_DIR}/intrusion_{timestamp}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_path, fourcc, FPS, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
            for f in video_frames:
                out.write(f)
            out.release()
            video_frames.clear()
            print(f"🎥 Vidéo sauvegardée : {video_path}")

        # ---- PDF ----
        pdf_path = f"{PDF_DIR}/intrusion_{timestamp}.pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(0,10, f"Rapport intrusion - {timestamp}", ln=True)
        pdf.image(photo_path, x=10, y=30, w=180)
        pdf.output(pdf_path)
        print(f"📄 PDF généré : {pdf_path}")

        # ---- Email simulé ----
        print(f"📧 Email simulé : pièce jointe -> {photo_path} + {pdf_path}")

        motion_accumulator = 0

    prev_frame = blur
    cv2.imshow("Camera", frame_display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

pipe.terminate()
cv2.destroyAllWindows()
