#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIDA SECURE AI - Système de détection d'intrusion
Version améliorée - Envoi email avec photo + vidéo + PDF
"""

import cv2
import numpy as np
import subprocess
import os
import time
from datetime import datetime
from pathlib import Path

# ───────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────
RTSP_URL = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

SAVE_FOLDER       = Path("intrusions")
EMAIL_RECEIVER    = "yvestoure717@gmail.com"

WIDTH  = 640
HEIGHT = 360
FPS    = 15

MOTION_THRESHOLD  = 2000      # À ajuster selon tes tests
MIN_CONTOUR_AREA  = 500       # Taille minimale pour considérer un humain
BUFFER_SECONDS    = 10        # Durée du buffer vidéo pré-événement

# ───────────────────────────────────────────────
# INITIALISATION
# ───────────────────────────────────────────────
SAVE_FOLDER.mkdir(exist_ok=True)

print("┌────────────────────────────────────────────┐")
print("│   VIDA SECURE AI - Système actif           │")
print("│   (sans Google Drive - email direct)       │")
print("└────────────────────────────────────────────┘")

# ───────────────────────────────────────────────
# Génération du rapport PDF (inchangé mais importé proprement)
# ───────────────────────────────────────────────
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch


def get_threat_level(score):
    if score > 10000:
        return "CRITIQUE", colors.red
    elif score > 5000:
        return "ÉLEVÉ", colors.orange
    else:
        return "MODÉRÉ", colors.green


def generate_pdf_report(pdf_path: Path, timestamp: str, motion_score: float, photo_path: Path, video_path: Path):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    content = []

    threat_text, threat_color = get_threat_level(motion_score)

    content.append(Paragraph("<b>VIDA SECURE AI</b>", styles['Title']))
    content.append(Spacer(1, 12))
    content.append(Paragraph("<font color='red'><b>RAPPORT D'INTRUSION DÉTECTÉE</b></font>", styles['Heading2']))
    content.append(Spacer(1, 24))

    # Tableau infos
    data = [
        ["Date & Heure", timestamp],
        ["Score de mouvement", f"{int(motion_score):,}"],
        ["Niveau de menace", threat_text],
    ]

    table = Table(data, colWidths=[180, 300])
    table.setStyle(TableStyle([
        ('GRID',       (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0),  colors.lightgrey),
        ('ALIGN',      (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
    ]))

    content.append(table)
    content.append(Spacer(1, 24))

    # Photo
    if photo_path.exists():
        content.append(Paragraph("<b>Photo de l'intrus :</b>", styles['Heading3']))
        content.append(Spacer(1, 12))
        try:
            img = Image(str(photo_path), width=5.5*inch, height=3.3*inch)
            content.append(img)
        except Exception as e:
            content.append(Paragraph(f"[Erreur chargement image : {e}]", styles['Normal']))
        content.append(Spacer(1, 24))

    # Vidéo
    content.append(Paragraph("<b>Vidéo jointe :</b>", styles['Heading3']))
    content.append(Paragraph(f"Fichier : {video_path.name}", styles['Normal']))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Durée : ~15 secondes (pré-événement inclus)", styles['Italic']))

    content.append(Spacer(1, 36))
    content.append(Paragraph("<i>Rapport généré automatiquement par VIDA Secure AI – Côte d'Ivoire – 2025</i>", styles['Normal']))

    doc.build(content)
    print(f"📄 Rapport PDF créé : {pdf_path.name}")


# ───────────────────────────────────────────────
# Lancement du flux RTSP via ffmpeg
# ───────────────────────────────────────────────
ffmpeg_cmd = [
    "ffmpeg",
    "-rtsp_transport", "tcp",
    "-i", RTSP_URL,
    "-vf", f"scale={WIDTH}:{HEIGHT}",
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-"
]

print("→ Lancement du flux RTSP...")
pipe = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


# ───────────────────────────────────────────────
# BOUCLE PRINCIPALE DE DÉTECTION
# ───────────────────────────────────────────────
prev_gray = None
frames_buffer = []

print("→ Détection de mouvement active... (Ctrl+C pour arrêter)")

try:
    while True:
        raw_frame = pipe.stdout.read(WIDTH * HEIGHT * 3)
        if len(raw_frame) != WIDTH * HEIGHT * 3:
            time.sleep(0.01)
            continue

        frame = np.frombuffer(raw_frame, np.uint8).reshape((HEIGHT, WIDTH, 3))
        frames_buffer.append(frame.copy())

        # Garder seulement les N dernières secondes
        if len(frames_buffer) > FPS * BUFFER_SECONDS:
            frames_buffer.pop(0)

        # Pré-traitement
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if prev_gray is None:
            prev_gray = gray
            continue

        # Détection de mouvement
        delta = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]

        motion_pixels = np.sum(thresh) / 255
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        human_detected = any(cv2.contourArea(c) > MIN_CONTOUR_AREA for c in contours)

        # Alerte ?
        if motion_pixels > MOTION_THRESHOLD and human_detected:
            ts = datetime.now()
            timestamp_str = ts.strftime("%Y%m%d_%H%M%S")
            print(f"\n🚨 INTRUSION DÉTECTÉE ─ {timestamp_str} ─ Score: {int(motion_pixels)}")

            base_name = f"intrus_{timestamp_str}"

            # 1. Photo
            photo_path = SAVE_FOLDER / f"{base_name}.jpg"
            cv2.imwrite(str(photo_path), frame)
            print(f"  📸 Photo sauvegardée")

            # 2. Vidéo (buffer + frame actuel)
            video_path = SAVE_FOLDER / f"{base_name}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(video_path), fourcc, FPS, (WIDTH, HEIGHT))

            for f in frames_buffer:
                out.write(f)
            out.write(frame)           # on ajoute la frame qui a déclenché
            out.release()
            print(f"  🎥 Vidéo sauvegardée ({len(frames_buffer)+1} frames)")

            # 3. PDF
            pdf_path = SAVE_FOLDER / f"rapport_{timestamp_str}.pdf"
            generate_pdf_report(pdf_path, ts.strftime("%d/%m/%Y %H:%M:%S"), motion_pixels, photo_path, video_path)

            # 4. Envoi email avec les 3 fichiers
            print("  → Lancement envoi email...")
            try:
                subprocess.run([
                    "python", "send_mail.py",
                    EMAIL_RECEIVER,
                    timestamp_str,
                    str(int(motion_pixels)),
                    str(photo_path),
                    str(video_path),
                    str(pdf_path)
                ], check=True, timeout=45)
                print("  ✓ Email envoyé")
            except Exception as e:
                print(f"  ⚠ Erreur lors de l'envoi email : {e}")

            # Anti-spam : pause après détection
            time.sleep(25)

        prev_gray = gray.copy()

except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur.")
except Exception as e:
    print(f"\nErreur fatale : {e}")

finally:
    pipe.terminate()
    print("Flux vidéo terminé. Au revoir !")
